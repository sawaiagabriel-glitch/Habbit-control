"""Serviço isolado para sugestão de metas de hábitos.

Desenvolvido para operar de forma determinística e extensível, permitindo futura
substituição ou aprimoramento com inteligência artificial (LLM) sem alterar
a interface ou as regras de negócio de persistência de Metas.
"""

LIMITES_SEGURANCA = {
    'dia': 24,        # Ex: beber água a cada hora acordada
    'semana': 70,     # Até 10 ocorrências diárias ao longo da semana
    'mes': 300,       # Até 10 ocorrências diárias no mês
    'ano': 3650,      # Até 10 ocorrências diárias no ano
}

NIVEIS_VALIDOS = ('confortavel', 'equilibrada', 'desafiadora')
PERIODOS_VALIDOS = ('dia', 'semana', 'mes', 'ano')

NOMES_PERIODOS = {
    'dia': 'dia',
    'semana': 'semana',
    'mes': 'mês',
    'ano': 'ano',
}


def sugerir_meta(frequencia_atual: int, nivel: str, periodo: str) -> dict:
    """Calcula deterministamente uma quantidade mínima recomendada para uma meta.

    Args:
        frequencia_atual: Frequência com que o hábito é praticado atualmente.
        nivel: Grau de desafio ('confortavel', 'equilibrada', 'desafiadora').
        periodo: Intervalo da meta ('dia', 'semana', 'mes', 'ano').

    Returns:
        Dicionário com a quantidade sugerida, período, nível e mensagem explicativa.

    Raises:
        ValueError: Se a frequência atual for menor que 1, se o período ou o nível
            forem inválidos.
    """
    if not isinstance(frequencia_atual, int) or frequencia_atual < 1:
        raise ValueError('A frequência atual deve ser um número inteiro maior ou igual a 1.')

    nivel_normalizado = str(nivel).strip().lower()
    if nivel_normalizado not in NIVEIS_VALIDOS:
        raise ValueError(f'Nível inválido: {nivel}. Opções válidas: {", ".join(NIVEIS_VALIDOS)}.')

    periodo_normalizado = str(periodo).strip().lower()
    if periodo_normalizado not in PERIODOS_VALIDOS:
        raise ValueError(f'Período inválido: {periodo}. Opções válidas: {", ".join(PERIODOS_VALIDOS)}.')

    # Cálculo progressivo baseado no nível
    if nivel_normalizado == 'confortavel':
        # Foco em consistência: ritmo atual ou reforço suave
        quantidade = max(1, int(round(frequencia_atual * 1.15)) if frequencia_atual >= 2 else 2)
        descricao_nivel = 'confortável, ideal para consolidar consistência sem sobrecarga'
    elif nivel_normalizado == 'equilibrada':
        # Evolução moderada e sustentável (+30% a +50%)
        quantidade = max(frequencia_atual + 1, int(round(frequencia_atual * 1.5)))
        descricao_nivel = 'equilibrada, trazendo avanço sustentável para a sua rotina'
    else:  # desafiadora
        # Alta performance (+70% a +100%)
        quantidade = max(frequencia_atual + 2, int(round(frequencia_atual * 2.0)))
        descricao_nivel = 'desafiadora, focada em maximizar sua evolução e novos patamares'

    # Aplicação de limites de segurança razoáveis por período
    limite_teto = LIMITES_SEGURANCA.get(periodo_normalizado, 100)
    quantidade_final = max(1, min(quantidade, limite_teto))

    nome_periodo = NOMES_PERIODOS.get(periodo_normalizado, periodo_normalizado)
    mensagem = (
        f'Minha sugestão é de {quantidade_final} vez(es) por {nome_periodo}. '
        f'Essa é uma meta {descricao_nivel}.'
    )

    return {
        'quantidade_sugerida': quantidade_final,
        'periodo': periodo_normalizado,
        'nivel': nivel_normalizado,
        'mensagem': mensagem,
    }
