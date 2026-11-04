"""Serviço isolado para sugestão conversacional de metas de hábitos.

Opera de forma híbrida: tenta a OpenAI Responses API quando configurada e
disponível; em qualquer falha, usa o algoritmo determinístico local (sem
simular conversa). A IA apenas sugere valores — nunca cria nem persiste Metas.
O histórico de chat não é persistido; o backend apenas sanitiza o payload.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

LIMITES_SEGURANCA = {
    'dia': 24,
    'semana': 70,
    'mes': 300,
    'ano': 3650,
}

NIVEIS_VALIDOS = ('confortavel', 'equilibrada', 'desafiadora')
PERIODOS_VALIDOS = ('dia', 'semana', 'mes', 'ano')
ROLES_HISTORICO_VALIDOS = ('user', 'assistant')

NOMES_PERIODOS = {
    'dia': 'dia',
    'semana': 'semana',
    'mes': 'mês',
    'ano': 'ano',
}

OBJETIVO_TEXTO_MAX_CHARS = 500
MENSAGEM_MAX_CHARS = 500
HISTORICO_MAX_MENSAGENS = 10
MAX_PERGUNTAS_ACOMPANHAMENTO = 4

SYSTEM_PROMPT = (
    'Você é o assistente conversacional de metas do Habbit-Control.\n\n'
    'Regra fundamental:\n'
    'Não crie uma meta imediatamente quando faltarem informações relevantes.\n'
    'Primeiro compreenda o objetivo do usuário.\n'
    'Faça uma pergunta por vez.\n'
    'Pergunte somente o necessário para transformar a intenção em uma meta '
    'específica, mensurável e realista.\n'
    'Evite interrogatórios longos.\n'
    'Normalmente faça entre 1 e 4 perguntas antes de gerar a meta.\n'
    'Se já houver contexto suficiente, não faça perguntas desnecessárias.\n'
    'Nunca invente respostas que o usuário não forneceu.\n\n'
    'Modos de resposta (campo estado):\n'
    '- coletando_contexto: ainda faltam dados; meta deve ser null; mensagem deve '
    'conter exatamente uma pergunta de acompanhamento (sem plano parcial).\n'
    '- meta_pronta: contexto suficiente; preencha meta completa; a justificativa '
    'deve citar fatos concretos da conversa (números, prazos, disponibilidade).\n\n'
    'As perguntas devem ser adaptativas ao objetivo. Não use roteiro fixo. '
    'Decida quais lacunas importam para aquele caso.\n\n'
    'quantidade_sugerida e periodo devem ser mensuráveis para o formulário de Meta, '
    'derivados do objetivo e do contexto coletado — nunca um simples +1 na frequência.\n'
    'Escolha periodo e nivel adequados ao contexto (confortavel, equilibrada ou desafiadora).\n'
    'Crie de 1 a 4 etapas com inicio_semana e fim_semana coerentes com duracao_semanas.\n'
    'Priorize consistência antes de intensidade; evite aumentos agressivos.\n'
    'Não faça diagnósticos médicos, psicológicos ou nutricionais.\n'
    'Não sugira metas perigosas, extremas ou impraticáveis.\n'
    'Não invente dados pessoais. Não solicite nem utilize documentos de identificação, '
    'credenciais de acesso ou dados de contato.\n'
    'Você nunca cria nem salva metas; apenas conversa e sugere.\n'
    'Retorne obrigatoriamente JSON conforme o schema fornecido.'
)

PLANO_ETAPA_SCHEMA = {
    'type': 'object',
    'properties': {
        'titulo': {
            'type': 'string',
            'description': 'Nome curto da etapa (ex.: Adaptação, Progressão, Consolidação).',
        },
        'inicio_semana': {
            'type': 'integer',
            'description': 'Semana inicial da etapa (inteiro >= 1).',
        },
        'fim_semana': {
            'type': 'integer',
            'description': 'Semana final da etapa (inteiro >= inicio_semana).',
        },
        'descricao': {
            'type': 'string',
            'description': 'Orientação objetiva do que fazer nesta etapa.',
        },
    },
    'required': ['titulo', 'inicio_semana', 'fim_semana', 'descricao'],
    'additionalProperties': False,
}

META_PRONTA_SCHEMA = {
    'type': 'object',
    'properties': {
        'titulo_meta': {
            'type': 'string',
            'description': 'Título curto da meta principal.',
        },
        'objetivo_principal': {
            'type': 'string',
            'description': 'Resultado principal que o usuário quer alcançar.',
        },
        'quantidade_sugerida': {
            'type': 'integer',
            'description': 'Quantidade mínima sugerida para a meta (inteiro >= 1).',
        },
        'periodo': {
            'type': 'string',
            'enum': list(PERIODOS_VALIDOS),
            'description': 'Período da meta.',
        },
        'duracao_semanas': {
            'type': 'integer',
            'description': 'Prazo total sugerido do plano em semanas (1 a 52).',
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
            'description': 'Explicação citando fatos concretos da conversa.',
        },
        'criterio_sucesso': {
            'type': 'string',
            'description': 'Critério claro para considerar o plano bem-sucedido.',
        },
        'plano_recuperacao': {
            'type': 'string',
            'description': 'Orientação caso o usuário saia do ritmo.',
        },
        'etapas': {
            'type': 'array',
            'description': 'De 1 a 4 etapas progressivas e realistas.',
            'items': PLANO_ETAPA_SCHEMA,
        },
    },
    'required': [
        'titulo_meta',
        'objetivo_principal',
        'quantidade_sugerida',
        'periodo',
        'duracao_semanas',
        'nivel',
        'mensagem',
        'justificativa',
        'criterio_sucesso',
        'plano_recuperacao',
        'etapas',
    ],
    'additionalProperties': False,
}

# Compat: nome antigo usado por testes/imports que referenciam o schema da meta.
SUGESTAO_META_SCHEMA = META_PRONTA_SCHEMA

RESPOSTA_CONVERSA_SCHEMA = {
    'type': 'object',
    'properties': {
        'estado': {
            'type': 'string',
            'enum': ['coletando_contexto', 'meta_pronta'],
            'description': 'Modo da resposta do assistente.',
        },
        'mensagem': {
            'type': 'string',
            'description': (
                'Pergunta de acompanhamento (coletando_contexto) ou resumo amigável '
                '(meta_pronta).'
            ),
        },
        'meta': {
            'anyOf': [
                {'type': 'null'},
                META_PRONTA_SCHEMA,
            ],
            'description': 'Meta completa quando estado=meta_pronta; null caso contrário.',
        },
    },
    'required': ['estado', 'mensagem', 'meta'],
    'additionalProperties': False,
}

PLANO_DURACAO_TOTAL_MIN = 1
PLANO_DURACAO_TOTAL_MAX = 52
PLANO_ETAPAS_MIN = 1
PLANO_ETAPAS_MAX = 4
PLANO_TEXTO_MAX_CHARS = 400
TITULO_META_MAX_CHARS = 160
OBJETIVO_PRINCIPAL_MAX_CHARS = 300


class MetaAssistantIAError(Exception):
    """Falha controlada na integração com a OpenAI (dispara fallback)."""


def sanitizar_objetivo_texto(texto: str | None, max_chars: int = OBJETIVO_TEXTO_MAX_CHARS) -> str:
    """Limita e sanitiza texto livre. Não persiste nada."""
    if texto is None:
        return ''
    limpo = str(texto).strip()
    limpo = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', limpo)
    limpo = re.sub(r'\s+', ' ', limpo).strip()
    if len(limpo) > max_chars:
        limpo = limpo[:max_chars].rstrip()
    return limpo


def sanitizar_mensagem(texto: str | None, max_chars: int = MENSAGEM_MAX_CHARS) -> str:
    """Sanitiza a mensagem atual do usuário no chat."""
    return sanitizar_objetivo_texto(texto, max_chars=max_chars)


def sanitizar_historico(historico: Any) -> list[dict[str, str]]:
    """Valida e limita o histórico enviado pelo frontend.

    - Aceita no máximo HISTORICO_MAX_MENSAGENS mensagens.
    - role deve ser user|assistant.
    - content limitado a MENSAGEM_MAX_CHARS e sanitizado.
    - Campos extras são ignorados.
    - Não usa o histórico para autenticação ou titularidade.
    """
    if historico is None:
        return []
    if not isinstance(historico, list):
        return []

    limpo: list[dict[str, str]] = []
    for item in historico:
        if len(limpo) >= HISTORICO_MAX_MENSAGENS:
            break
        if not isinstance(item, dict):
            continue
        role = str(item.get('role', '')).strip().lower()
        if role not in ROLES_HISTORICO_VALIDOS:
            continue
        content = sanitizar_mensagem(item.get('content'))
        if not content:
            continue
        limpo.append({'role': role, 'content': content})
    return limpo


def contar_perguntas_assistente(historico: list[dict[str, str]]) -> int:
    """Conta turnos do assistente já presentes no histórico sanitizado."""
    return sum(1 for msg in historico if msg.get('role') == 'assistant')


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
    """Calcula deterministamente uma quantidade mínima recomendada para uma meta."""
    frequencia_atual, nivel_normalizado, periodo_normalizado = _normalizar_entrada(
        frequencia_atual, nivel, periodo,
    )

    if nivel_normalizado == 'confortavel':
        quantidade = max(1, int(round(frequencia_atual * 1.15)) if frequencia_atual >= 2 else 2)
        descricao_nivel = 'confortável, ideal para consolidar consistência sem sobrecarga'
    elif nivel_normalizado == 'equilibrada':
        quantidade = max(frequencia_atual + 1, int(round(frequencia_atual * 1.5)))
        descricao_nivel = 'equilibrada, trazendo avanço sustentável para a sua rotina'
    else:
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


def _empacotar_fallback_deterministico(
    frequencia_atual: int,
    nivel: str = 'equilibrada',
    periodo: str = 'semana',
) -> dict:
    """Converte a sugestão determinística no contrato conversacional meta_pronta."""
    det = sugerir_meta_deterministica(frequencia_atual, nivel, periodo)
    meta = {
        'quantidade_sugerida': det['quantidade_sugerida'],
        'periodo': det['periodo'],
        'nivel': det['nivel'],
        'mensagem': det['mensagem'],
        'justificativa': det['justificativa'],
    }
    return {
        'estado': 'meta_pronta',
        'mensagem': det['mensagem'],
        'meta': meta,
        'origem': 'deterministico',
        # Campos flat para compatibilidade com consumidores antigos / "Usar esta meta".
        **meta,
    }


def _validar_plano(plano_bruto: Any) -> dict | None:
    """Valida e normaliza o plano flat. Retorna None se inválido (soft-fail)."""
    if not isinstance(plano_bruto, dict):
        return None

    duracao_total = plano_bruto.get('duracao_semanas')
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
    for etapa in etapas_brutas:
        if not isinstance(etapa, dict):
            return None
        titulo = etapa.get('titulo')
        descricao = etapa.get('descricao')
        inicio = etapa.get('inicio_semana')
        fim = etapa.get('fim_semana')
        if not isinstance(titulo, str) or not titulo.strip():
            return None
        if not isinstance(descricao, str) or not descricao.strip():
            return None
        if isinstance(inicio, bool) or not isinstance(inicio, int):
            return None
        if isinstance(fim, bool) or not isinstance(fim, int):
            return None
        if inicio < 1 or fim < inicio:
            return None
        if fim > duracao_total:
            return None
        etapas_normalizadas.append({
            'titulo': titulo.strip()[:120],
            'inicio_semana': inicio,
            'fim_semana': fim,
            'descricao': descricao.strip()[:PLANO_TEXTO_MAX_CHARS],
        })

    criterio = plano_bruto.get('criterio_sucesso')
    recuperacao = plano_bruto.get('plano_recuperacao')
    if not isinstance(criterio, str) or not criterio.strip():
        return None
    if not isinstance(recuperacao, str) or not recuperacao.strip():
        return None

    return {
        'duracao_semanas': duracao_total,
        'criterio_sucesso': criterio.strip()[:PLANO_TEXTO_MAX_CHARS],
        'etapas': etapas_normalizadas,
        'plano_recuperacao': recuperacao.strip()[:PLANO_TEXTO_MAX_CHARS],
    }


def _validar_meta_pronta(dados: dict[str, Any]) -> dict:
    """Valida a meta quando estado=meta_pronta. Soft-fail do plano."""
    if not isinstance(dados, dict):
        raise MetaAssistantIAError('meta inválida.')

    quantidade = dados.get('quantidade_sugerida')
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise MetaAssistantIAError('quantidade_sugerida inválida.')
    if quantidade < 1:
        raise MetaAssistantIAError('quantidade_sugerida deve ser >= 1.')

    periodo = str(dados.get('periodo', '')).strip().lower()
    if periodo not in PERIODOS_VALIDOS:
        raise MetaAssistantIAError('periodo inválido na resposta da IA.')

    nivel = str(dados.get('nivel', '')).strip().lower()
    if nivel not in NIVEIS_VALIDOS:
        raise MetaAssistantIAError('nivel inválido na resposta da IA.')

    limite = LIMITES_SEGURANCA.get(periodo, 100)
    if quantidade > limite:
        raise MetaAssistantIAError('quantidade acima do limite de segurança.')

    titulo_meta = dados.get('titulo_meta')
    objetivo_principal = dados.get('objetivo_principal')
    mensagem = dados.get('mensagem')
    justificativa = dados.get('justificativa')
    if not isinstance(titulo_meta, str) or not titulo_meta.strip():
        raise MetaAssistantIAError('titulo_meta inválido.')
    if not isinstance(objetivo_principal, str) or not objetivo_principal.strip():
        raise MetaAssistantIAError('objetivo_principal inválido.')
    if not isinstance(mensagem, str) or not mensagem.strip():
        raise MetaAssistantIAError('mensagem inválida.')
    if not isinstance(justificativa, str) or not justificativa.strip():
        raise MetaAssistantIAError('justificativa inválida.')

    resultado = {
        'titulo_meta': titulo_meta.strip()[:TITULO_META_MAX_CHARS],
        'objetivo_principal': objetivo_principal.strip()[:OBJETIVO_PRINCIPAL_MAX_CHARS],
        'quantidade_sugerida': quantidade,
        'periodo': periodo,
        'nivel': nivel,
        'mensagem': mensagem.strip()[:500],
        'justificativa': justificativa.strip()[:500],
    }

    plano_normalizado = _validar_plano({
        'duracao_semanas': dados.get('duracao_semanas'),
        'criterio_sucesso': dados.get('criterio_sucesso'),
        'plano_recuperacao': dados.get('plano_recuperacao'),
        'etapas': dados.get('etapas'),
    })
    if plano_normalizado is not None:
        resultado.update(plano_normalizado)
    else:
        logger.info(
            'Assistente de metas: plano/etapas inválidos; '
            'mantendo apenas a sugestão principal.'
        )

    return resultado


def _validar_resposta_conversa(
    dados: dict[str, Any],
    *,
    perguntas_ja_feitas: int,
) -> dict:
    """Valida a resposta discriminada da IA."""
    if not isinstance(dados, dict):
        raise MetaAssistantIAError('Resposta da IA não é um objeto.')

    estado = str(dados.get('estado', '')).strip().lower()
    if estado not in ('coletando_contexto', 'meta_pronta'):
        raise MetaAssistantIAError('estado inválido.')

    mensagem = dados.get('mensagem')
    if not isinstance(mensagem, str) or not mensagem.strip():
        raise MetaAssistantIAError('mensagem inválida.')
    mensagem_limpa = mensagem.strip()[:MENSAGEM_MAX_CHARS]

    meta_bruta = dados.get('meta')

    if estado == 'coletando_contexto':
        if meta_bruta is not None:
            raise MetaAssistantIAError('meta deve ser null em coletando_contexto.')
        if perguntas_ja_feitas >= MAX_PERGUNTAS_ACOMPANHAMENTO:
            raise MetaAssistantIAError(
                'Limite de perguntas de acompanhamento atingido sem meta_pronta.'
            )
        return {
            'estado': 'coletando_contexto',
            'mensagem': mensagem_limpa,
            'meta': None,
            'origem': 'ia',
        }

    # meta_pronta
    if meta_bruta is None:
        raise MetaAssistantIAError('meta obrigatória em meta_pronta.')
    meta_normalizada = _validar_meta_pronta(meta_bruta)
    return {
        'estado': 'meta_pronta',
        'mensagem': mensagem_limpa,
        'meta': meta_normalizada,
        'origem': 'ia',
        **meta_normalizada,
    }


# Compatibilidade com testes que ainda importam o validador antigo.
def _validar_resposta_ia(dados: dict[str, Any], periodo_solicitado: str = '', nivel_solicitado: str = '') -> dict:
    """Compat: valida meta flat ou envelope conversacional."""
    if isinstance(dados, dict) and 'estado' in dados:
        return _validar_resposta_conversa(dados, perguntas_ja_feitas=0)
    meta = _validar_meta_pronta(dados)
    if periodo_solicitado and meta['periodo'] != periodo_solicitado:
        raise MetaAssistantIAError('periodo divergente do solicitado.')
    if nivel_solicitado and meta['nivel'] != nivel_solicitado:
        raise MetaAssistantIAError('nivel divergente do solicitado.')
    return {'origem': 'ia', **meta}


def _montar_instrucoes_contexto(
    *,
    nome_habito: str,
    frequencia_atual: int,
    periodo_habito: str,
    frequencia_desejada: int | None,
    periodo_desejado: str | None,
    perguntas_ja_feitas: int,
) -> str:
    partes = [
        SYSTEM_PROMPT,
        '',
        'Contexto do hábito (apenas referência; não substitui a conversa):',
        f'- Hábito: {nome_habito or "não informado"}',
        f'- Frequência registrada: {frequencia_atual} vez(es) por {periodo_habito}',
        f'- Limite máximo seguro por período: dia={LIMITES_SEGURANCA["dia"]}, '
        f'semana={LIMITES_SEGURANCA["semana"]}, mes={LIMITES_SEGURANCA["mes"]}, '
        f'ano={LIMITES_SEGURANCA["ano"]}',
    ]
    if frequencia_desejada is not None and isinstance(frequencia_desejada, int) and frequencia_desejada >= 1:
        periodo_ref = periodo_desejado if periodo_desejado in PERIODOS_VALIDOS else periodo_habito
        partes.append(
            f'- Frequência desejada no cadastro: {frequencia_desejada} vez(es) por {periodo_ref}'
        )
    partes.append(f'- Perguntas de acompanhamento já feitas nesta conversa: {perguntas_ja_feitas}')
    if perguntas_ja_feitas >= MAX_PERGUNTAS_ACOMPANHAMENTO:
        partes.append(
            f'- OBRIGATÓRIO: já houve {perguntas_ja_feitas} perguntas. '
            'Responda com estado=meta_pronta agora (exceto se houver razão clara de '
            'segurança para recusar a meta). Não faça nova pergunta.'
        )
    else:
        restantes = MAX_PERGUNTAS_ACOMPANHAMENTO - perguntas_ja_feitas
        partes.append(
            f'- Você pode fazer no máximo mais {restantes} pergunta(s) antes de '
            'precisar concluir com meta_pronta.'
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


def conversar_meta_assistente(
    *,
    mensagem: str,
    historico: Any = None,
    nome_habito: str = '',
    frequencia_atual: int = 1,
    periodo_habito: str = 'semana',
    frequencia_desejada: int | None = None,
    periodo_desejado: str | None = None,
    nivel_fallback: str = 'equilibrada',
) -> dict:
    """Conduz um turno do assistente conversacional.

    Returns:
        Dict com estado, mensagem, meta (ou None), origem e campos flat quando meta_pronta.
    """
    mensagem_limpa = sanitizar_mensagem(mensagem)
    if not mensagem_limpa:
        raise ValueError('Informe uma mensagem para o assistente.')

    historico_limpo = sanitizar_historico(historico)
    perguntas_ja_feitas = contar_perguntas_assistente(historico_limpo)

    # Normaliza contexto do hábito para fallback / prompt (não autoriza usuário).
    try:
        freq_int = int(frequencia_atual)
    except (TypeError, ValueError):
        freq_int = 1
    if freq_int < 1:
        freq_int = 1
    periodo_ctx = str(periodo_habito or 'semana').strip().lower()
    if periodo_ctx not in PERIODOS_VALIDOS:
        periodo_ctx = 'semana'
    nivel_fb = str(nivel_fallback or 'equilibrada').strip().lower()
    if nivel_fb not in NIVEIS_VALIDOS:
        nivel_fb = 'equilibrada'

    if not _openai_api_key():
        return _empacotar_fallback_deterministico(freq_int, nivel_fb, periodo_ctx)

    try:
        return _conversar_com_ia(
            mensagem=mensagem_limpa,
            historico=historico_limpo,
            perguntas_ja_feitas=perguntas_ja_feitas,
            nome_habito=(nome_habito or '').strip()[:120],
            frequencia_atual=freq_int,
            periodo_habito=periodo_ctx,
            frequencia_desejada=frequencia_desejada,
            periodo_desejado=periodo_desejado,
        )
    except MetaAssistantIAError:
        logger.info('Assistente de metas: usando fallback determinístico.')
        return _empacotar_fallback_deterministico(freq_int, nivel_fb, periodo_ctx)
    except Exception:
        logger.warning(
            'Assistente de metas: exceção inesperada; usando fallback determinístico.',
            exc_info=False,
        )
        return _empacotar_fallback_deterministico(freq_int, nivel_fb, periodo_ctx)


def _conversar_com_ia(
    *,
    mensagem: str,
    historico: list[dict[str, str]],
    perguntas_ja_feitas: int,
    nome_habito: str,
    frequencia_atual: int,
    periodo_habito: str,
    frequencia_desejada: int | None,
    periodo_desejado: str | None,
) -> dict:
    api_key = _openai_api_key()
    if not api_key:
        raise MetaAssistantIAError('OPENAI_API_KEY ausente.')

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise MetaAssistantIAError('SDK openai não instalado.') from exc

    instructions = _montar_instrucoes_contexto(
        nome_habito=nome_habito,
        frequencia_atual=frequencia_atual,
        periodo_habito=periodo_habito,
        frequencia_desejada=frequencia_desejada,
        periodo_desejado=periodo_desejado,
        perguntas_ja_feitas=perguntas_ja_feitas,
    )

    input_messages: list[dict[str, str]] = [
        {'role': msg['role'], 'content': msg['content']}
        for msg in historico
    ]
    input_messages.append({'role': 'user', 'content': mensagem})

    try:
        client = OpenAI(api_key=api_key, timeout=_openai_timeout())
        response = client.responses.create(
            model=_openai_model(),
            instructions=instructions,
            input=input_messages,
            store=False,
            text={
                'format': {
                    'type': 'json_schema',
                    'name': 'resposta_assistente_meta',
                    'strict': True,
                    'schema': RESPOSTA_CONVERSA_SCHEMA,
                }
            },
        )
        dados_brutos = _extrair_json_resposta(response)
        return _validar_resposta_conversa(
            dados_brutos,
            perguntas_ja_feitas=perguntas_ja_feitas,
        )
    except MetaAssistantIAError:
        raise
    except ValueError:
        raise
    except Exception as exc:
        logger.warning(
            'Falha na OpenAI Responses API no assistente de metas: %s',
            type(exc).__name__,
        )
        raise MetaAssistantIAError(f'Erro na API OpenAI: {type(exc).__name__}') from exc


def sugerir_meta_com_ia(
    frequencia_atual: int,
    nivel: str,
    periodo: str,
    *,
    nome_habito: str = '',
    frequencia_desejada: int | None = None,
    periodo_desejado: str | None = None,
    objetivo_texto: str = '',
    mensagem: str = '',
    historico: Any = None,
) -> dict:
    """Gera turno via IA. Compatível com assinatura antiga (objetivo_texto).

    Raises MetaAssistantIAError em falhas (sem fallback automático).
    """
    frequencia_atual, nivel_normalizado, periodo_normalizado = _normalizar_entrada(
        frequencia_atual, nivel, periodo,
    )
    texto = sanitizar_mensagem(mensagem or objetivo_texto)
    if not texto:
        texto = 'Quero melhorar este hábito.'

    historico_limpo = sanitizar_historico(historico)
    return _conversar_com_ia(
        mensagem=texto,
        historico=historico_limpo,
        perguntas_ja_feitas=contar_perguntas_assistente(historico_limpo),
        nome_habito=(nome_habito or '').strip()[:120],
        frequencia_atual=frequencia_atual,
        periodo_habito=periodo_normalizado,
        frequencia_desejada=frequencia_desejada,
        periodo_desejado=periodo_desejado,
    )


def sugerir_meta(
    frequencia_atual: int,
    nivel: str,
    periodo: str,
    *,
    nome_habito: str = '',
    frequencia_desejada: int | None = None,
    periodo_desejado: str | None = None,
    objetivo_texto: str = '',
    mensagem: str = '',
    historico: Any = None,
) -> dict:
    """Sugere meta/conversa: tenta IA; senão fallback determinístico.

    Mantém assinatura posicional compatível. Com IA, retorna o contrato
    conversacional (estado/mensagem/meta). Sem IA ou em falha, retorna
    fallback empacotado como meta_pronta.
    """
    _normalizar_entrada(frequencia_atual, nivel, periodo)

    return conversar_meta_assistente(
        mensagem=mensagem or objetivo_texto or 'Quero melhorar este hábito.',
        historico=historico,
        nome_habito=nome_habito,
        frequencia_atual=frequencia_atual,
        periodo_habito=periodo,
        frequencia_desejada=frequencia_desejada,
        periodo_desejado=periodo_desejado,
        nivel_fallback=nivel,
    )
