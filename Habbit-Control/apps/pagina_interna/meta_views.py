import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.login_cadastro_app.models import Parceiro
from .access import get_cliente_from_session
from .forms import MetaForm
from .meta_assistant import (
    conversar_meta_assistente,
    sanitizar_mensagem,
    validar_payload_criacao_meta_assistente,
)
from .models import Habito, Meta
from .services import (
    atualizar_ciclos_meta,
    criar_meta_com_plano_assistente,
    obter_resumo_meta,
)


def _json_erro(erro, status):
    """Resposta JSON de erro no contrato dos endpoints do assistente."""
    return JsonResponse({'sucesso': False, 'erro': erro}, status=status)


def _ler_corpo_request(request, *, form_as_dict=False):
    """Lê JSON ou form-data.

    ``assistente_sugerir_meta`` usa ``request.POST`` (QueryDict);
    ``assistente_criar_meta`` usa ``request.POST.dict()``.
    """
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body.decode('utf-8')), None
        except (ValueError, UnicodeDecodeError):
            return None, _json_erro('Formato JSON inválido.', 400)
    if form_as_dict:
        return request.POST.dict(), None
    return request.POST, None


def _cliente_json_autenticado(request):
    """Cliente da sessão para endpoints JSON, ou resposta 401."""
    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return None, _json_erro('Usuário não autenticado.', 401)
    return cliente, None


def _obter_habito_elegivel_para_meta(cliente, habito_id):
    """Resolve e valida hábito do Cliente para criar/sugerir Meta.

    Preserva as mesmas mensagens e status (400/404) dos endpoints do assistente.
    """
    if not habito_id:
        return None, _json_erro('Selecione um hábito para a meta.', 400)

    try:
        habito_id_int = int(habito_id)
    except (TypeError, ValueError):
        return None, _json_erro('Identificador de hábito inválido.', 400)

    habito = Habito.objects.filter(pk=habito_id_int, cliente=cliente).first()
    if habito is None:
        return None, _json_erro(
            'Hábito não encontrado ou não pertence à sua conta.',
            404,
        )

    if habito.tipo_habito != 'positivo':
        return None, _json_erro(
            'Apenas hábitos positivos podem receber metas.',
            400,
        )

    if habito.metas.exists():
        return None, _json_erro(
            'Este hábito já possui uma meta cadastrada.',
            400,
        )

    return habito, None


def _meta_do_cliente_via_post(request, meta_id, erro_msg):
    """Fluxo comum POST + Cliente + Meta própria.

    Returns:
        ``(meta, None)`` em sucesso ou ``(None, HttpResponseRedirect)`` para
        método inválido, anônimo ou meta inexistente/alheia.
    """
    if request.method != 'POST':
        return None, redirect('metas')

    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return None, redirect('login')

    meta = Meta.objects.filter(
        pk=meta_id,
        habito__cliente=cliente,
    ).first()
    if meta is None:
        messages.error(request, erro_msg)
        return None, redirect('metas')

    return meta, None


def metas(request):
    """Apresenta as metas do Cliente e recebe novas metas por formulário.

    A seleção de hábitos e Parceiros é validada pelo ``MetaForm`` e limitada
    aos dados autorizados para a conta associada à sessão.
    """
    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return redirect('login')

    form = MetaForm(request.POST or None, cliente=cliente)
    if request.method == 'POST' and form.is_valid():
        meta = form.save(commit=False)
        meta.save()
        form.save_m2m()
        atualizar_ciclos_meta(meta)
        messages.success(request, 'Meta criada com sucesso.')
        return redirect('metas')

    metas_cliente = (
        Meta.objects.filter(habito__cliente=cliente)
        .select_related('habito', 'plano_assistente')
        .prefetch_related('parceiros')
    )
    for meta in metas_cliente:
        atualizar_ciclos_meta(meta)

    metas_resumo = [obter_resumo_meta(meta) for meta in metas_cliente]

    habitos_assistente = [
        {
            'id': h.id,
            'nome': h.nome_habito,
            'frequencia_valor': h.frequencia_atual_valor,
            'frequencia_periodo': h.frequencia_atual_periodo,
        }
        for h in form.fields['habito'].queryset
    ]

    return render(request, 'pagina_interna/metas.html', {
        'cliente': cliente,
        'form': form,
        'metas': metas_cliente,
        'metas_resumo': metas_resumo,
        'habitos_assistente': habitos_assistente,
    })


def metas_partilhadas(request):
    """Apresenta ao Parceiro somente metas partilhadas com a sua conta."""
    parceiro = Parceiro.objects.filter(
        email=request.session.get('parceiro_email'),
    ).first()
    if parceiro is None:
        return redirect('login_parceiro')

    metas_do_parceiro = (
        Meta.objects.filter(parceiros=parceiro)
        .select_related('habito', 'habito__cliente')
    )
    for meta in metas_do_parceiro:
        atualizar_ciclos_meta(meta)

    return render(request, 'pagina_interna/metas_partilhadas.html', {
        'parceiro': parceiro,
        'metas': metas_do_parceiro,
    })


def excluir_meta(request, meta_id):
    """Exclui uma meta do Cliente sem tocar no hábito ou nas atividades.

    A operação aceita apenas POST e limita a consulta ao Cliente da sessão.
    """
    meta, resposta = _meta_do_cliente_via_post(
        request,
        meta_id,
        'Meta não encontrada ou sem permissão para excluí-la.',
    )
    if resposta:
        return resposta

    meta.delete()
    messages.success(request, 'Meta excluída. O hábito e as atividades foram mantidos.')
    return redirect('metas')


def ativar_compartilhamento_meta(request, meta_id):
    """Ativa o compartilhamento público de uma Meta pertencente ao Cliente autenticado.

    Operação aceita apenas POST com token CSRF.
    """
    meta, resposta = _meta_do_cliente_via_post(
        request,
        meta_id,
        'Meta não encontrada ou sem permissão para compartilhá-la.',
    )
    if resposta:
        return resposta

    meta.ativar_compartilhamento()
    messages.success(request, 'Link público de compartilhamento gerado com sucesso.')
    return redirect('metas')


def desativar_compartilhamento_meta(request, meta_id):
    """Desativa o compartilhamento público da Meta pertencente ao Cliente autenticado.

    O token é mantido persistido para possibilitar reativação futura com o mesmo link.
    """
    meta, resposta = _meta_do_cliente_via_post(
        request,
        meta_id,
        'Meta não encontrada ou sem permissão para desativar o compartilhamento.',
    )
    if resposta:
        return resposta

    meta.desativar_compartilhamento()
    messages.success(
        request,
        'Compartilhamento público desativado. O link anterior agora está indisponível.',
    )
    return redirect('metas')


def meta_publica(request, token):
    """Página pública somente-leitura de uma Meta compartilhada.

    Não requer autenticação e exibe apenas indicadores essenciais do hábito,
    sem expor dados pessoais do cliente e sem disparar escritas no banco de dados.
    """
    meta = (
        Meta.objects.filter(
            token_publico=token,
            compartilhamento_ativo=True,
        )
        .select_related('habito')
        .first()
    )
    if meta is None:
        return render(request, 'pagina_interna/meta_publica_indisponivel.html', status=404)

    resumo = obter_resumo_meta(meta)

    return render(request, 'pagina_interna/meta_publica.html', {
        'nome_habito': resumo['habito_nome'],
        'quantidade_minima': resumo['quantidade_minima'],
        'periodo': resumo['periodo_display'],
        'progresso': resumo['progresso'],
        'percentual': resumo['percentual'],
        'percentual_css': f"{resumo['percentual']:.1f}",
        'estado': resumo['estado_display'],
        'streak': resumo['streak'],
    })


def assistente_sugerir_meta(request):
    """Endpoint autenticado para o assistente conversacional de Meta.

    Aceita POST JSON com ``habito_id``, ``mensagem`` e ``historico`` opcional.
    Não altera nem cria registros no banco. Histórico/perguntas/plano não são
    persistidos. A titularidade do hábito vem só da sessão do Cliente.
    """
    if request.method != 'POST':
        return _json_erro('Método não permitido.', 405)

    cliente, erro = _cliente_json_autenticado(request)
    if erro:
        return erro

    data, erro = _ler_corpo_request(request, form_as_dict=False)
    if erro:
        return erro

    habito_id = data.get('habito_id')
    # Compat: clientes antigos podem enviar objetivo_texto em vez de mensagem.
    mensagem_bruta = data.get('mensagem')
    if mensagem_bruta is None or str(mensagem_bruta).strip() == '':
        mensagem_bruta = data.get('objetivo_texto')
    mensagem = sanitizar_mensagem(mensagem_bruta)
    historico = data.get('historico')

    habito, erro = _obter_habito_elegivel_para_meta(cliente, habito_id)
    if erro:
        return erro

    if not mensagem:
        return _json_erro('Informe uma mensagem para o assistente.', 400)

    try:
        sugestao = conversar_meta_assistente(
            mensagem=mensagem,
            historico=historico,
            nome_habito=habito.nome_habito,
            frequencia_atual=habito.frequencia_atual_valor or 1,
            periodo_habito=habito.frequencia_atual_periodo or 'semana',
            frequencia_desejada=habito.frequencia_desejada_valor,
            periodo_desejado=habito.frequencia_desejada_periodo,
        )
    except ValueError as e:
        return _json_erro(str(e), 400)

    resposta = {
        'sucesso': True,
        'habito_id': habito.id,
        'nome_habito': habito.nome_habito,
        'estado': sugestao.get('estado', 'meta_pronta'),
        'mensagem': sugestao.get('mensagem', ''),
        'origem': sugestao.get('origem', 'deterministico'),
        'meta': sugestao.get('meta'),
    }

    # Campos flat quando a meta está pronta (facilitam "Usar esta meta" e testes).
    if sugestao.get('estado') == 'meta_pronta' and isinstance(sugestao.get('meta'), dict):
        meta = sugestao['meta']
        for campo in (
            'titulo_meta',
            'objetivo_principal',
            'quantidade_sugerida',
            'periodo',
            'nivel',
            'justificativa',
            'duracao_semanas',
            'criterio_sucesso',
            'plano_recuperacao',
            'etapas',
        ):
            if meta.get(campo) is not None:
                resposta[campo] = meta[campo]
        if meta.get('mensagem') and not resposta.get('mensagem'):
            resposta['mensagem'] = meta['mensagem']

    return JsonResponse(resposta)


def assistente_criar_meta(request):
    """Cria Meta (+ PlanoMetaAssistente quando houver) a partir do assistente.

    Aceita POST JSON com hábito, quantidade, período e dados estruturados do plano.
    Não chama OpenAI; apenas revalida o payload e persiste em ``transaction.atomic``.
    """
    if request.method != 'POST':
        return _json_erro('Método não permitido.', 405)

    cliente, erro = _cliente_json_autenticado(request)
    if erro:
        return erro

    data, erro = _ler_corpo_request(request, form_as_dict=True)
    if erro:
        return erro

    habito, erro = _obter_habito_elegivel_para_meta(cliente, data.get('habito_id'))
    if erro:
        return erro

    plano_bruto = data.get('plano') if isinstance(data.get('plano'), dict) else {}
    payload_validacao = {
        'quantidade_minima': data.get('quantidade_minima', data.get('quantidade_sugerida')),
        'periodo': data.get('periodo'),
        'titulo_meta': data.get('titulo_meta', plano_bruto.get('titulo_meta')),
        'objetivo_principal': data.get(
            'objetivo_principal',
            plano_bruto.get('objetivo_principal'),
        ),
        'nivel': data.get('nivel', plano_bruto.get('nivel')),
        'mensagem': data.get('mensagem', plano_bruto.get('mensagem')),
        'justificativa': data.get('justificativa', plano_bruto.get('justificativa')),
        'duracao_semanas': data.get('duracao_semanas', plano_bruto.get('duracao_semanas')),
        'criterio_sucesso': data.get('criterio_sucesso', plano_bruto.get('criterio_sucesso')),
        'plano_recuperacao': data.get(
            'plano_recuperacao',
            plano_bruto.get('plano_recuperacao'),
        ),
        'etapas': data.get('etapas', plano_bruto.get('etapas')),
    }

    try:
        normalizado = validar_payload_criacao_meta_assistente(payload_validacao)
    except ValueError as exc:
        return _json_erro(str(exc), 400)

    meta = criar_meta_com_plano_assistente(
        habito=habito,
        quantidade_minima=normalizado['quantidade_minima'],
        periodo=normalizado['periodo'],
        plano=normalizado['plano'],
    )

    return JsonResponse({
        'sucesso': True,
        'meta_id': meta.id,
        'tem_plano': normalizado['plano'] is not None,
        'redirect_url': f'/metas/#meta-{meta.id}',
    })
