import calendar
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import MetaCiclo, RegistroAtividade


def inicio_periodo(data, periodo):
    """Retorna o primeiro dia civil do período que contém ``data``.

    Args:
        data: Data usada para localizar o ciclo.
        periodo: Intervalo da meta: dia, semana, mês ou ano.

    Returns:
        Data inicial do ciclo, com semanas iniciadas na segunda-feira.

    Raises:
        ValueError: Se ``periodo`` não for suportado.
    """
    if periodo == 'dia':
        return data
    if periodo == 'semana':
        return data - timedelta(days=data.weekday())
    if periodo == 'mes':
        return date(data.year, data.month, 1)
    if periodo == 'ano':
        return date(data.year, 1, 1)
    raise ValueError(f'Período inválido: {periodo}')


def _proximo_inicio(inicio, periodo):
    """Calcula o início do ciclo civil imediatamente seguinte."""
    if periodo == 'dia':
        return inicio + timedelta(days=1)
    if periodo == 'semana':
        return inicio + timedelta(days=7)
    if periodo == 'mes':
        ano = inicio.year + (inicio.month // 12)
        mes = inicio.month % 12 + 1
        return date(ano, mes, 1)
    if periodo == 'ano':
        return date(inicio.year + 1, 1, 1)
    raise ValueError(f'Período inválido: {periodo}')


def _progresso_do_ciclo(meta, inicio, fim):
    """Soma as quantidades registadas para o hábito dentro do ciclo inclusivo."""
    return RegistroAtividade.objects.filter(
        habito=meta.habito,
        data__gte=inicio,
        data__lte=fim,
    ).aggregate(total=Sum('quantidade'))['total'] or 0


def _atualizar_progresso_ciclo(meta, ciclo):
    """Atualiza o ciclo vigente e gere a reversão do seu cumprimento.

    O timestamp de cumprimento é preservado enquanto o ciclo continuar
    cumprido e removido quando o progresso voltar a ficar abaixo do objetivo.
    """
    progresso = _progresso_do_ciclo(meta, ciclo.inicio, ciclo.fim)
    estado = (
        MetaCiclo.ESTADO_CUMPRIDA
        if progresso >= meta.quantidade_minima
        else MetaCiclo.ESTADO_ATIVA
    )
    if estado == MetaCiclo.ESTADO_CUMPRIDA:
        data_cumprimento = ciclo.data_cumprimento or timezone.now()
    else:
        data_cumprimento = None
    MetaCiclo.objects.filter(pk=ciclo.pk).update(
        progresso=progresso,
        estado=estado,
        data_cumprimento=data_cumprimento,
    )
    ciclo.progresso = progresso
    ciclo.estado = estado
    ciclo.data_cumprimento = data_cumprimento
    return ciclo


def _calcular_streak(meta, ciclos, hoje, ciclo_atual_inicio):
    """Calcula a sequência com base somente em ciclos já encerrados."""
    streak = 0
    for ciclo in ciclos:
        if ciclo.fim >= hoje or ciclo.inicio >= ciclo_atual_inicio:
            continue
        if ciclo.estado == MetaCiclo.ESTADO_CUMPRIDA:
            streak += 1
        elif ciclo.estado == MetaCiclo.ESTADO_NAO_CUMPRIDA:
            streak = 0
    if meta.streak != streak:
        meta.streak = streak
        meta.save(update_fields=['streak'])


@transaction.atomic
def atualizar_ciclos_meta(meta, hoje=None):
    """Materializa e atualiza ciclos civis, estados, progresso e streak.

    A operação é atómica e idempotente: ciclos existentes não são duplicados,
    ciclos históricos já fechados não são reabertos e o streak não é
    incrementado novamente quando o mesmo fechamento é processado outra vez.

    Args:
        meta: Meta cujos ciclos serão avaliados.
        hoje: Data de referência opcional, útil para testes e processamento
            agendado. Por omissão, usa a data local configurada no Django.

    Returns:
        Ciclos da meta desde o período de início até ao período atual, em ordem.
    """
    hoje = hoje or timezone.localdate()
    inicio_atual = inicio_periodo(hoje, meta.periodo)
    inicio = inicio_periodo(meta.data_inicio, meta.periodo)
    ciclos = []

    while inicio <= inicio_atual:
        proximo = _proximo_inicio(inicio, meta.periodo)
        fim = proximo - timedelta(days=1)
        ciclo, criado = MetaCiclo.objects.get_or_create(
            meta=meta,
            inicio=inicio,
            defaults={'fim': fim},
        )

        if ciclo.inicio < inicio_atual:
            if criado or ciclo.estado == MetaCiclo.ESTADO_ATIVA:
                progresso = _progresso_do_ciclo(meta, ciclo.inicio, ciclo.fim)
                estado = (
                    MetaCiclo.ESTADO_CUMPRIDA
                    if progresso >= meta.quantidade_minima
                    else MetaCiclo.ESTADO_NAO_CUMPRIDA
                )
                data_cumprimento = (
                    ciclo.data_cumprimento or timezone.now()
                    if estado == MetaCiclo.ESTADO_CUMPRIDA
                    else None
                )
                MetaCiclo.objects.filter(pk=ciclo.pk).update(
                    progresso=progresso,
                    estado=estado,
                    fim=fim,
                    data_cumprimento=data_cumprimento,
                )
                ciclo.progresso = progresso
                ciclo.estado = estado
                ciclo.fim = fim
                ciclo.data_cumprimento = data_cumprimento
        else:
            ciclo = _atualizar_progresso_ciclo(meta, ciclo)

        ciclos.append(ciclo)
        inicio = proximo

    _calcular_streak(meta, ciclos, hoje, inicio_atual)
    return ciclos
