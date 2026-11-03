"""Serviço isolado para sugestão de metas de hábitos.

Opera de forma híbrida: tenta a OpenAI Responses API quando configurada e
disponível; em qualquer falha, usa o algoritmo determinístico local.
A IA apenas sugere valores — nunca cria nem persiste Metas.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

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

OBJETIVO_TEXTO_MAX_CHARS = 200

SYSTEM_PROMPT = (
    'Você é um assistente do Habbit-Control especializado em ajudar usuários a '
    'criar metas de hábitos realistas, progressivas e mensuráveis.\n\n'
    'Sua função é sugerir uma quantidade e um período com base apenas no hábito, '
    'frequência atual, objetivo e nível de desafio informado, e também um plano '
    'estruturado de execução com poucas etapas curtas e objetivas.\n\n'
    'Regras do plano:\n'
    '- Crie de 1 a 4 etapas.\n'
    '- Cada etapa deve ser curta e objetiva.\n'
    '- O plano deve ser compatível com quantidade_sugerida e periodo.\n'
    '- Não aumente agressivamente frequência ou volume.\n'
    '- Priorize consistência antes de intensidade.\n\n'
    'Não faça diagnósticos médicos, psicológicos ou nutricionais.\n'
    'Não dê conselhos perigosos.\n'
    'Não sugira valores extremos, impraticáveis ou comportamentos perigosos.\n'
    'Não invente dados do usuário.\n'
    'A meta deve ser específica, simples e mensurável.\n'
    'Você não cria nem salva metas. Apenas gera uma sugestão.\n'
    'Retorne obrigatoriamente dados estruturados conforme o schema fornecido.'
)

PLANO_ETAPA_SCHEMA = {
    'type': 'object',
    'properties': {
        'titulo': {
            'type': 'string',
            'description': 'Nome curto da etapa (ex.: Adaptação).',
        },
        'duracao_semanas': {
            'type': 'integer',
            'description': 'Duração da etapa em semanas (inteiro >= 1).',
        },
        'descricao': {
            'type': 'string',
            'description': 'Orientação objetiva do que fazer nesta etapa.',
        },
    },
    'required': ['titulo', 'duracao_semanas', 'descricao'],
    'additionalProperties': False,
}

PLANO_META_SCHEMA = {
    'type': 'object',
    'properties': {
        'duracao_sugerida_semanas': {
            'type': 'integer',
            'description': 'Duração total sugerida do plano em semanas (1 a 52).',
        },
        'criterio_sucesso': {
            'type': 'string',
            'description': 'Critério claro para considerar o plano bem-sucedido.',
        },
        'etapas': {
            'type': 'array',
            'description': 'De 1 a 4 etapas progressivas e realistas.',
            'items': PLANO_ETAPA_SCHEMA,
        },
        'plano_recuperacao': {
            'type': 'string',
            'description': 'Orientação caso o usuário saia do ritmo.',
        },
        'dica': {
            'type': 'string',
            'description': 'Dica prática curta de consistência.',
        },
    },
    'required': [
        'duracao_sugerida_semanas',
        'criterio_sucesso',
        'etapas',
        'plano_recuperacao',
        'dica',
    ],
    'additionalProperties': False,
}

SUGESTAO_META_SCHEMA = {
    'type': 'object',
    'properties': {
        'quantidade_sugerida': {
            'type': 'integer',
            'description': 'Quantidade mínima sugerida para a meta (inteiro >= 1).',
        },
        'periodo': {
            'type': 'string',
            'enum': list(PERIODOS_VALIDOS),
            'description': 'Período da meta.',
        },
        'nivel': {
            'type': 'string',
            'enum': list(NIVEIS_VALIDOS),
            'description': 'Nível de desafio aplicado.',
        },
        'mensagem': {
            'type': 'string',
            'description': 'Texto curto e amigável descrevendo a sugestão.',
        },
        'justificativa': {
            'type': 'string',
            'description': 'Explicação curta da recomendação.',
        },
        'plano': PLANO_META_SCHEMA,
    },
    'required': [
        'quantidade_sugerida',
        'periodo',
        'nivel',
        'mensagem',
        'justificativa',
        'plano',
    ],
    'additionalProperties': False,
}

# Limites usados apenas na validação defensiva do plano (não persistidos).
PLANO_DURACAO_TOTAL_MIN = 1
PLANO_DURACAO_TOTAL_MAX = 52
PLANO_ETAPA_DURACAO_MAX = 26
PLANO_ETAPAS_MIN = 1
PLANO_ETAPAS_MAX = 4
PLANO_TEXTO_MAX_CHARS = 400


class MetaAssistantIAError(Exception):
    """Falha controlada na integração com a OpenAI (dispara fallback)."""


def sanitizar_objetivo_texto(texto: str | None, max_chars: int = OBJETIVO_TEXTO_MAX_CHARS) -> str:
    """Limita e sanitiza o texto livre opcional do usuário.

    Não persiste nada; apenas prepara contexto seguro para a IA.
    """
    if texto is None:
        return ''
    limpo = str(texto).strip()
    limpo = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', limpo)
    limpo = re.sub(r'\s+', ' ', limpo).strip()
    if len(limpo) > max_chars:
        limpo = limpo[:max_chars].rstrip()
    return limpo


def _normalizar_entrada(frequencia_atual: int, nivel: str, periodo: str) -> tuple[int, str, str]:
    if not isinstance(frequencia_atual, int) or frequencia_atual < 1:
        raise ValueError('A frequência atual deve ser um número inteiro maior ou igual a 1.')

    nivel_normalizado = str(nivel).strip().lower()
    if nivel_normalizado not in NIVEIS_VALIDOS:
        raise ValueError(f'Nível inválido: {nivel}. Opções válidas: {", ".join(NIVEIS_VALIDOS)}.')

    periodo_normalizado = str(periodo).strip().lower()
    if periodo_normalizado not in PERIODOS_VALIDOS:
        raise ValueError(f'Período inválido: {periodo}. Opções válidas: {", ".join(PERIODOS_VALIDOS)}.')

    return frequencia_atual, nivel_normalizado, periodo_normalizado


def _aplicar_limite_seguranca(quantidade: int, periodo: str) -> int:
    limite_teto = LIMITES_SEGURANCA.get(periodo, 100)
    return max(1, min(int(quantidade), limite_teto))


def _openai_api_key() -> str:
    return (getattr(settings, 'OPENAI_API_KEY', None) or '').strip()


def _openai_model() -> str:
    configurado = (getattr(settings, 'OPENAI_META_ASSISTANT_MODEL', None) or '').strip()
    if configurado:
        return configurado
    return 'gpt-4.1-mini'


def _openai_timeout() -> float:
    try:
        return float(getattr(settings, 'OPENAI_META_ASSISTANT_TIMEOUT', 15.0))
    except (TypeError, ValueError):
        return 15.0


def sugerir_meta_deterministica(frequencia_atual: int, nivel: str, periodo: str) -> dict:
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
    frequencia_atual, nivel_normalizado, periodo_normalizado = _normalizar_entrada(
        frequencia_atual, nivel, periodo,
    )

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

    quantidade_final = _aplicar_limite_seguranca(quantidade, periodo_normalizado)

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
        'justificativa': (
            f'Recomendação calculada localmente com base na frequência atual '
            f'({frequencia_atual}) e no nível {nivel_normalizado}.'
        ),
        'origem': 'deterministico',
    }


def _validar_plano(plano_bruto: Any) -> dict | None:
    """Valida e normaliza o plano estruturado.

    Retorna o plano normalizado ou ``None`` se inválido (falha soft: a sugestão
    principal da meta permanece válida). Não exige igualdade estrita entre a
    soma das durações das etapas e ``duracao_sugerida_semanas``.
    """
    if not isinstance(plano_bruto, dict):
        return None

    duracao_total = plano_bruto.get('duracao_sugerida_semanas')
    if isinstance(duracao_total, bool) or not isinstance(duracao_total, int):
        return None
    if duracao_total < PLANO_DURACAO_TOTAL_MIN or duracao_total > PLANO_DURACAO_TOTAL_MAX:
        return None

    etapas_brutas = plano_bruto.get('etapas')
    if not isinstance(etapas_brutas, list):
        return None
    if not (PLANO_ETAPAS_MIN <= len(etapas_brutas) <= PLANO_ETAPAS_MAX):
        return None

    etapas_normalizadas: list[dict] = []
    soma_duracoes = 0
    for etapa in etapas_brutas:
        if not isinstance(etapa, dict):
            return None
        titulo = etapa.get('titulo')
        descricao = etapa.get('descricao')
        duracao = etapa.get('duracao_semanas')
        if not isinstance(titulo, str) or not titulo.strip():
            return None
        if not isinstance(descricao, str) or not descricao.strip():
            return None
        if isinstance(duracao, bool) or not isinstance(duracao, int):
            return None
        if duracao < 1 or duracao > PLANO_ETAPA_DURACAO_MAX:
            return None
        soma_duracoes += duracao
        etapas_normalizadas.append({
            'titulo': titulo.strip()[:120],
            'duracao_semanas': duracao,
            'descricao': descricao.strip()[:PLANO_TEXTO_MAX_CHARS],
        })

    # Coerência: soma positiva e dentro do teto; pequena diferença vs. total é ok.
    if soma_duracoes < PLANO_DURACAO_TOTAL_MIN or soma_duracoes > PLANO_DURACAO_TOTAL_MAX:
        return None

    criterio = plano_bruto.get('criterio_sucesso')
    recuperacao = plano_bruto.get('plano_recuperacao')
    dica = plano_bruto.get('dica')
    if not isinstance(criterio, str) or not criterio.strip():
        return None
    if not isinstance(recuperacao, str) or not recuperacao.strip():
        return None
    if not isinstance(dica, str) or not dica.strip():
        return None

    return {
        'duracao_sugerida_semanas': duracao_total,
        'criterio_sucesso': criterio.strip()[:PLANO_TEXTO_MAX_CHARS],
        'etapas': etapas_normalizadas,
        'plano_recuperacao': recuperacao.strip()[:PLANO_TEXTO_MAX_CHARS],
        'dica': dica.strip()[:PLANO_TEXTO_MAX_CHARS],
    }


def _validar_resposta_ia(dados: dict[str, Any], periodo_solicitado: str, nivel_solicitado: str) -> dict:
    """Valida e normaliza a saída da IA. Levanta MetaAssistantIAError se inválida.

    O plano estruturado é opcional na prática: se vier inválido, a sugestão
    principal é preservada e o plano é omitido.
    """
    if not isinstance(dados, dict):
        raise MetaAssistantIAError('Resposta da IA não é um objeto.')

    quantidade = dados.get('quantidade_sugerida')
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise MetaAssistantIAError('quantidade_sugerida inválida.')
    if quantidade < 1:
        raise MetaAssistantIAError('quantidade_sugerida deve ser >= 1.')

    periodo = str(dados.get('periodo', '')).strip().lower()
    if periodo not in PERIODOS_VALIDOS:
        raise MetaAssistantIAError('periodo inválido na resposta da IA.')
    # O período da sugestão deve respeitar o escolhido pelo usuário
    if periodo != periodo_solicitado:
        raise MetaAssistantIAError('periodo divergente do solicitado.')

    nivel = str(dados.get('nivel', '')).strip().lower()
    if nivel not in NIVEIS_VALIDOS:
        raise MetaAssistantIAError('nivel inválido na resposta da IA.')
    if nivel != nivel_solicitado:
        raise MetaAssistantIAError('nivel divergente do solicitado.')

    limite = LIMITES_SEGURANCA.get(periodo, 100)
    if quantidade > limite:
        raise MetaAssistantIAError('quantidade acima do limite de segurança.')

    mensagem = dados.get('mensagem')
    justificativa = dados.get('justificativa')
    if not isinstance(mensagem, str) or not mensagem.strip():
        raise MetaAssistantIAError('mensagem inválida.')
    if not isinstance(justificativa, str) or not justificativa.strip():
        raise MetaAssistantIAError('justificativa inválida.')

    resultado = {
        'quantidade_sugerida': quantidade,
        'periodo': periodo,
        'nivel': nivel,
        'mensagem': mensagem.strip()[:500],
        'justificativa': justificativa.strip()[:500],
        'origem': 'ia',
    }

    plano_normalizado = _validar_plano(dados.get('plano'))
    if plano_normalizado is not None:
        resultado['plano'] = plano_normalizado
    elif 'plano' in dados:
        logger.info(
            'Assistente de metas: plano estruturado inválido; '
            'mantendo apenas a sugestão principal.'
        )

    return resultado


def _montar_contexto_ia(
    *,
    frequencia_atual: int,
    nivel: str,
    periodo: str,
    nome_habito: str = '',
    frequencia_desejada: int | None = None,
    periodo_desejado: str | None = None,
    objetivo_texto: str = '',
) -> str:
    partes = [
        f'Hábito: {nome_habito or "não informado"}',
        f'Frequência atual: {frequencia_atual} vez(es) por {periodo}',
        f'Nível desejado: {nivel}',
        f'Período da meta: {periodo}',
        f'Limite máximo seguro para este período: {LIMITES_SEGURANCA.get(periodo, 100)}',
    ]
    if frequencia_desejada is not None and isinstance(frequencia_desejada, int) and frequencia_desejada >= 1:
        periodo_ref = periodo_desejado if periodo_desejado in PERIODOS_VALIDOS else periodo
        partes.append(f'Frequência desejada informada no hábito: {frequencia_desejada} vez(es) por {periodo_ref}')
    if objetivo_texto:
        partes.append(f'Objetivo descrito pelo usuário: {objetivo_texto}')
    partes.append(
        'Sugira quantidade_sugerida (>= 1), mantendo o mesmo periodo e nivel informados, '
        'respeitando o limite de segurança.'
    )
    partes.append(
        'Inclua também um plano estruturado com 1 a 4 etapas curtas, duração total em '
        'semanas, critério de sucesso, plano de recuperação e uma dica prática. '
        'O plano deve ser compatível com a quantidade e o período sugeridos, sem '
        'aumentos agressivos.'
    )
    return '\n'.join(partes)


def _extrair_json_resposta(response: Any) -> dict:
    """Extrai JSON estruturado da resposta da Responses API."""
    output_text = getattr(response, 'output_text', None)
    if output_text:
        try:
            return json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise MetaAssistantIAError('JSON inválido em output_text.') from exc

    # Fallback defensivo: percorrer itens de saída
    output = getattr(response, 'output', None) or []
    for item in output:
        contents = getattr(item, 'content', None) or []
        for content in contents:
            text = getattr(content, 'text', None)
            if text:
                try:
                    return json.loads(text)
                except (TypeError, json.JSONDecodeError):
                    continue
    raise MetaAssistantIAError('Resposta da IA sem conteúdo estruturado.')


def sugerir_meta_com_ia(
    frequencia_atual: int,
    nivel: str,
    periodo: str,
    *,
    nome_habito: str = '',
    frequencia_desejada: int | None = None,
    periodo_desejado: str | None = None,
    objetivo_texto: str = '',
) -> dict:
    """Gera sugestão via OpenAI Responses API com Structured Outputs.

    Raises:
        ValueError: Entrada inválida (mesmas regras do algoritmo determinístico).
        MetaAssistantIAError: Qualquer falha de integração ou validação da saída.
    """
    frequencia_atual, nivel_normalizado, periodo_normalizado = _normalizar_entrada(
        frequencia_atual, nivel, periodo,
    )

    api_key = _openai_api_key()
    if not api_key:
        raise MetaAssistantIAError('OPENAI_API_KEY ausente.')

    objetivo_limpo = sanitizar_objetivo_texto(objetivo_texto)
    contexto = _montar_contexto_ia(
        frequencia_atual=frequencia_atual,
        nivel=nivel_normalizado,
        periodo=periodo_normalizado,
        nome_habito=(nome_habito or '').strip()[:120],
        frequencia_desejada=frequencia_desejada,
        periodo_desejado=periodo_desejado,
        objetivo_texto=objetivo_limpo,
    )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise MetaAssistantIAError('SDK openai não instalado.') from exc

    try:
        client = OpenAI(api_key=api_key, timeout=_openai_timeout())
        response = client.responses.create(
            model=_openai_model(),
            instructions=SYSTEM_PROMPT,
            input=contexto,
            store=False,
            text={
                'format': {
                    'type': 'json_schema',
                    'name': 'sugestao_meta',
                    'strict': True,
                    'schema': SUGESTAO_META_SCHEMA,
                }
            },
        )
        dados_brutos = _extrair_json_resposta(response)
        return _validar_resposta_ia(dados_brutos, periodo_normalizado, nivel_normalizado)
    except MetaAssistantIAError:
        raise
    except ValueError:
        raise
    except Exception as exc:
        # Não vaza detalhes técnicos ao chamador; loga de forma segura
        logger.warning(
            'Falha na OpenAI Responses API no assistente de metas: %s',
            type(exc).__name__,
        )
        raise MetaAssistantIAError(f'Erro na API OpenAI: {type(exc).__name__}') from exc


def sugerir_meta(
    frequencia_atual: int,
    nivel: str,
    periodo: str,
    *,
    nome_habito: str = '',
    frequencia_desejada: int | None = None,
    periodo_desejado: str | None = None,
    objetivo_texto: str = '',
) -> dict:
    """Sugere uma meta: tenta IA quando disponível; senão usa algoritmo determinístico.

    A assinatura posicional (frequencia_atual, nivel, periodo) permanece compatível
    com o código e os testes existentes.
    """
    # Valida entrada cedo (ValueError propaga para o endpoint como 400)
    _normalizar_entrada(frequencia_atual, nivel, periodo)

    if not _openai_api_key():
        return sugerir_meta_deterministica(frequencia_atual, nivel, periodo)

    try:
        return sugerir_meta_com_ia(
            frequencia_atual,
            nivel,
            periodo,
            nome_habito=nome_habito,
            frequencia_desejada=frequencia_desejada,
            periodo_desejado=periodo_desejado,
            objetivo_texto=objetivo_texto,
        )
    except MetaAssistantIAError:
        logger.info('Assistente de metas: usando fallback determinístico.')
        return sugerir_meta_deterministica(frequencia_atual, nivel, periodo)
    except Exception:
        logger.warning(
            'Assistente de metas: exceção inesperada; usando fallback determinístico.',
            exc_info=False,
        )
        return sugerir_meta_deterministica(frequencia_atual, nivel, periodo)
