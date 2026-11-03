"""
Cálculo de progresso de hábitos.

Reutiliza a mesma regra já usada em Relatórios / api_dados_relatorio.
"""
from datetime import date, timedelta

from apps.pagina_interna.models import RegistroAtividade


def frequencia_desejada_por_dia(habito):
    """Converte a frequência desejada do hábito para valor por dia."""
    freq_desejada_valor = habito.frequencia_desejada_valor
    freq_desejada_periodo = habito.frequencia_desejada_periodo

    freq_desejada_por_dia = freq_desejada_valor
    if freq_desejada_periodo == 'semana':
        freq_desejada_por_dia = freq_desejada_valor / 7
    elif freq_desejada_periodo == 'mes':
        freq_desejada_por_dia = freq_desejada_valor / 30
    elif freq_desejada_periodo == 'ano':
        freq_desejada_por_dia = freq_desejada_valor / 365

    return freq_desejada_por_dia


def calcular_progresso_percentual(tipo_habito, total_registrado, total_esperado):
    """
    Calcula o progresso percentual.

    Positivo: quanto mais registrado em relação ao esperado, melhor.
    Negativo: quanto menos registrado em relação ao esperado, melhor.
    """
    if tipo_habito == 'positivo':
        if total_esperado > 0:
            return min(100, (total_registrado / total_esperado) * 100)
        return 0

    # Hábitos negativos
    if total_esperado > 0:
        return min(100, max(0, (1 - (total_registrado / total_esperado)) * 100))
    return 100 if total_registrado == 0 else 0


def definir_periodo(periodo, data_fim=None):
    """Define data_inicio, data_fim e intervalo conforme o período selecionado."""
    if data_fim is None:
        data_fim = date.today()

    if periodo == 'dia':
        data_inicio = data_fim
        intervalo = timedelta(days=1)
    elif periodo == 'semana':
        data_inicio = data_fim - timedelta(days=6)
        intervalo = timedelta(days=1)
    elif periodo == 'mes':
        data_inicio = data_fim - timedelta(days=29)
        intervalo = timedelta(days=1)
    elif periodo == 'ano':
        data_inicio = data_fim - timedelta(days=364)
        intervalo = timedelta(days=7)
    else:
        raise ValueError('Período inválido')

    return data_inicio, data_fim, intervalo


def calcular_total_esperado(periodo, freq_desejada_por_dia, data_inicio, data_fim):
    """Calcula o total esperado no período (mesma regra dos relatórios)."""
    dias_total = (data_fim - data_inicio).days + 1
    if periodo == 'dia':
        return freq_desejada_por_dia
    if periodo == 'semana':
        return freq_desejada_por_dia * dias_total
    if periodo == 'mes':
        return freq_desejada_por_dia * dias_total
    # ano
    return freq_desejada_por_dia * 365


def obter_dados_relatorio(habito, periodo='semana'):
    """
    Retorna os dados de progresso/gráfico para um hábito e período.

    Mesma regra utilizada por api_dados_relatorio.
    """
    data_inicio, data_fim, _intervalo = definir_periodo(periodo)

    registros = RegistroAtividade.objects.filter(
        habito=habito,
        data__gte=data_inicio,
        data__lte=data_fim
    ).order_by('data')

    freq_por_dia = frequencia_desejada_por_dia(habito)

    labels = []
    dados_registrados_acumulados = []
    dados_esperados_acumulados = []
    progresso_percent = []

    current_date = data_inicio
    total_registrado_acumulado = 0
    dias_contados = 0

    while current_date <= data_fim:
        if periodo == 'ano':
            semana_fim = min(current_date + timedelta(days=6), data_fim)
            registros_periodo = registros.filter(
                data__gte=current_date,
                data__lte=semana_fim
            )
            quantidade_periodo = sum(r.quantidade for r in registros_periodo)
            label = f"{current_date.strftime('%d/%m')} - {semana_fim.strftime('%d/%m')}"
            dias_no_periodo = (semana_fim - current_date).days + 1
            dias_contados += dias_no_periodo
            current_date = semana_fim + timedelta(days=1)
        else:
            registro_dia = registros.filter(data=current_date).first()
            quantidade_periodo = registro_dia.quantidade if registro_dia else 0
            label = current_date.strftime('%d/%m')
            dias_contados += 1
            current_date += timedelta(days=1)

        total_registrado_acumulado += quantidade_periodo
        esperado_acumulado = freq_por_dia * dias_contados
        progresso = calcular_progresso_percentual(
            habito.tipo_habito,
            total_registrado_acumulado,
            esperado_acumulado
        )

        labels.append(label)
        dados_registrados_acumulados.append(total_registrado_acumulado)
        dados_esperados_acumulados.append(round(esperado_acumulado, 1))
        progresso_percent.append(round(progresso, 2))

    total_registrado_periodo = sum(r.quantidade for r in registros)
    total_esperado = calcular_total_esperado(
        periodo, freq_por_dia, data_inicio, data_fim
    )
    progresso_geral = calcular_progresso_percentual(
        habito.tipo_habito,
        total_registrado_periodo,
        total_esperado
    )

    return {
        'habito': {
            'id': habito.id,
            'nome': habito.nome_habito,
            'tipo': habito.tipo_habito,
            'frequencia_desejada_valor': habito.frequencia_desejada_valor,
            'frequencia_desejada_periodo': habito.get_frequencia_desejada_periodo_display()
        },
        'periodo': periodo,
        'total_registrado': total_registrado_periodo,
        'total_esperado': round(total_esperado, 1),
        'progresso_percentual': round(progresso_geral, 2),
        'labels': labels,
        'dados_registrados': dados_registrados_acumulados,
        'dados_esperados': dados_esperados_acumulados,
        'progresso_percent': progresso_percent
    }
