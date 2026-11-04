import calendar
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Meta, MetaCiclo, PlanoMetaAssistente, RegistroAtividade

OBJETIVO_RESUMO_MAX_CHARS = 160


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


def _obter_plano_assistente(meta):
    """Retorna o PlanoMetaAssistente ligado à meta, ou None."""
    try:
        return meta.plano_assistente
    except PlanoMetaAssistente.DoesNotExist:
        return None


def obter_resumo_meta(meta, hoje=None):
    """Monta um resumo read-only da meta (progresso, streak e plano opcional).

    Não cria ``MetaCiclo``, não altera o banco e não chama OpenAI. Reutiliza a
    mesma regra de soma de atividades do ciclo civil corrente.

    Args:
        meta: Instância de ``Meta`` (preferencialmente com ``habito`` carregado).
        hoje: Data de referência opcional (útil em testes).

    Returns:
        Dicionário com progresso atual, percentual, estado, streak e, quando
        existir, dados resumidos de ``PlanoMetaAssistente``.
    """
    hoje = hoje or timezone.localdate()
    inicio = inicio_periodo(hoje, meta.periodo)
    fim = _proximo_inicio(inicio, meta.periodo) - timedelta(days=1)
    progresso = _progresso_do_ciclo(meta, inicio, fim)

    if meta.quantidade_minima > 0:
        percentual = min(100, round(progresso / meta.quantidade_minima * 100, 1))
    else:
        percentual = 0

    if progresso >= meta.quantidade_minima:
        estado = MetaCiclo.ESTADO_CUMPRIDA
        estado_display = 'Cumprida'
    else:
        estado = MetaCiclo.ESTADO_ATIVA
        estado_display = 'Ativa'

    plano = _obter_plano_assistente(meta)
    objetivo_principal = plano.objetivo_principal if plano else None
    objetivo_resumo = None
    if objetivo_principal:
        if len(objetivo_principal) <= OBJETIVO_RESUMO_MAX_CHARS:
            objetivo_resumo = objetivo_principal
        else:
            objetivo_resumo = objetivo_principal[: OBJETIVO_RESUMO_MAX_CHARS - 1].rstrip() + '…'

    return {
        'meta': meta,
        'meta_id': meta.pk,
        'habito_nome': meta.habito.nome_habito,
        'quantidade_minima': meta.quantidade_minima,
        'periodo': meta.periodo,
        'periodo_display': meta.get_periodo_display(),
        'progresso': progresso,
        'percentual': percentual,
        'estado': estado,
        'estado_display': estado_display,
        'streak': meta.streak,
        'tem_plano': plano is not None,
        'titulo_meta': plano.titulo_meta if plano else meta.habito.nome_habito,
        'objetivo_principal': objetivo_principal,
        'objetivo_resumo': objetivo_resumo,
        'prazo_semanas': plano.duracao_semanas if plano else None,
        'nivel': plano.nivel if plano else None,
        'justificativa': plano.justificativa if plano else None,
        'criterio_sucesso': plano.criterio_sucesso if plano else None,
        'plano_recuperacao': plano.plano_recuperacao if plano else None,
        'etapas': list(plano.etapas) if plano and plano.etapas else [],
        'url_plano': f'/metas/#meta-{meta.pk}',
        'plano': plano,
    }


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


@transaction.atomic
def criar_meta_com_plano_assistente(*, habito, quantidade_minima, periodo, plano=None):
    """Cria a Meta e, quando houver, o ``PlanoMetaAssistente`` na mesma transação.

    Args:
        habito: Hábito positivo titular da meta.
        quantidade_minima: Objetivo operacional da Meta.
        periodo: Período civil da Meta.
        plano: Dict normalizado do plano ou ``None`` para meta sem plano.

    Returns:
        A ``Meta`` recém-criada (com ciclos inicializados).
    """
    meta = Meta(
        habito=habito,
        quantidade_minima=quantidade_minima,
        periodo=periodo,
    )
    meta.save()

    if plano:
        PlanoMetaAssistente.objects.create(
            meta=meta,
            titulo_meta=plano['titulo_meta'],
            objetivo_principal=plano['objetivo_principal'],
            duracao_semanas=plano['duracao_semanas'],
            nivel=plano.get('nivel') or '',
            justificativa=plano.get('justificativa') or '',
            criterio_sucesso=plano['criterio_sucesso'],
            plano_recuperacao=plano['plano_recuperacao'],
            etapas=plano.get('etapas') or [],
        )

    atualizar_ciclos_meta(meta)
    return meta
