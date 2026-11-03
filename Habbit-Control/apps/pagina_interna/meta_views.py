from datetime import timedelta
import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.login_cadastro_app.models import Parceiro
from .access import get_cliente_from_session
from .forms import MetaForm
from .meta_assistant import sanitizar_objetivo_texto, sugerir_meta
from .models import Habito, Meta
from .services import atualizar_ciclos_meta, inicio_periodo, _proximo_inicio, _progresso_do_ciclo


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
        .select_related('habito')
        .prefetch_related('parceiros')
    )
    for meta in metas_cliente:
        atualizar_ciclos_meta(meta)

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
    if request.method != 'POST':
        return redirect('metas')

    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return redirect('login')

    meta = Meta.objects.filter(
        pk=meta_id,
        habito__cliente=cliente,
    ).first()
    if meta is None:
        messages.error(request, 'Meta não encontrada ou sem permissão para excluí-la.')
        return redirect('metas')

    meta.delete()
    messages.success(request, 'Meta excluída. O hábito e as atividades foram mantidos.')
    return redirect('metas')


def ativar_compartilhamento_meta(request, meta_id):
    """Ativa o compartilhamento público de uma Meta pertencente ao Cliente autenticado.

    Operação aceita apenas POST com token CSRF.
    """
    if request.method != 'POST':
        return redirect('metas')

    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return redirect('login')

    meta = Meta.objects.filter(
        pk=meta_id,
        habito__cliente=cliente,
    ).first()
    if meta is None:
        messages.error(request, 'Meta não encontrada ou sem permissão para compartilhá-la.')
        return redirect('metas')

    meta.ativar_compartilhamento()
    messages.success(request, 'Link público de compartilhamento gerado com sucesso.')
    return redirect('metas')


def desativar_compartilhamento_meta(request, meta_id):
    """Desativa o compartilhamento público da Meta pertencente ao Cliente autenticado.

    O token é mantido persistido para possibilitar reativação futura com o mesmo link.
    """
    if request.method != 'POST':
        return redirect('metas')

    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return redirect('login')

    meta = Meta.objects.filter(
        pk=meta_id,
        habito__cliente=cliente,
    ).first()
    if meta is None:
        messages.error(request, 'Meta não encontrada ou sem permissão para desativar o compartilhamento.')
        return redirect('metas')

    meta.desativar_compartilhamento()
    messages.success(request, 'Compartilhamento público desativado. O link anterior agora está indisponível.')
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

    hoje = timezone.localdate()
    inicio = inicio_periodo(hoje, meta.periodo)
    fim = _proximo_inicio(inicio, meta.periodo) - timedelta(days=1)
    progresso = _progresso_do_ciclo(meta, inicio, fim)

    if meta.quantidade_minima > 0:
        percentual = min(100, round(progresso / meta.quantidade_minima * 100, 1))
    else:
        percentual = 0

    estado_str = 'Cumprida' if progresso >= meta.quantidade_minima else 'Ativa'

    return render(request, 'pagina_interna/meta_publica.html', {
        'nome_habito': meta.habito.nome_habito,
        'quantidade_minima': meta.quantidade_minima,
        'periodo': meta.get_periodo_display(),
        'progresso': progresso,
        'percentual': percentual,
        'percentual_css': f'{percentual:.1f}',
        'estado': estado_str,
        'streak': meta.streak,
    })


def assistente_sugerir_meta(request):
    """Endpoint autenticado para sugerir Meta (IA com fallback determinístico).

    Aceita apenas POST via JSON ou formulário. Não altera e não cria registros
    no banco de dados. O texto opcional ``objetivo_texto`` não é persistido.
    """
    if request.method != 'POST':
        return JsonResponse({'sucesso': False, 'erro': 'Método não permitido.'}, status=405)

    cliente, _ = get_cliente_from_session(request)
    if cliente is None:
        return JsonResponse({'sucesso': False, 'erro': 'Usuário não autenticado.'}, status=401)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'sucesso': False, 'erro': 'Formato JSON inválido.'}, status=400)
    else:
        data = request.POST

    habito_id = data.get('habito_id')
    frequencia_atual = data.get('frequencia_atual')
    periodo = data.get('periodo')
    nivel = data.get('nivel')
    objetivo_texto = sanitizar_objetivo_texto(data.get('objetivo_texto'))

    if not habito_id:
        return JsonResponse({'sucesso': False, 'erro': 'Selecione um hábito para a meta.'}, status=400)

    try:
        habito_id_int = int(habito_id)
    except (TypeError, ValueError):
        return JsonResponse({'sucesso': False, 'erro': 'Identificador de hábito inválido.'}, status=400)

    habito = Habito.objects.filter(pk=habito_id_int, cliente=cliente).first()
    if habito is None:
        return JsonResponse({'sucesso': False, 'erro': 'Hábito não encontrado ou não pertence à sua conta.'}, status=404)

    if habito.tipo_habito != 'positivo':
        return JsonResponse({'sucesso': False, 'erro': 'Apenas hábitos positivos podem receber metas.'}, status=400)

    if habito.metas.exists():
        return JsonResponse({'sucesso': False, 'erro': 'Este hábito já possui uma meta cadastrada.'}, status=400)

    try:
        frequencia_atual_int = int(frequencia_atual)
    except (TypeError, ValueError):
        return JsonResponse({'sucesso': False, 'erro': 'A frequência atual deve ser um número inteiro maior que zero.'}, status=400)

    if frequencia_atual_int < 1:
        return JsonResponse({'sucesso': False, 'erro': 'A frequência atual deve ser maior ou igual a 1.'}, status=400)

    try:
        sugestao = sugerir_meta(
            frequencia_atual=frequencia_atual_int,
            nivel=nivel,
            periodo=periodo,
            nome_habito=habito.nome_habito,
            frequencia_desejada=habito.frequencia_desejada_valor,
            periodo_desejado=habito.frequencia_desejada_periodo,
            objetivo_texto=objetivo_texto,
        )
    except ValueError as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=400)

    resposta = {
        'sucesso': True,
        'habito_id': habito.id,
        'nome_habito': habito.nome_habito,
        'quantidade_sugerida': sugestao['quantidade_sugerida'],
        'periodo': sugestao['periodo'],
        'nivel': sugestao['nivel'],
        'mensagem': sugestao['mensagem'],
        'origem': sugestao.get('origem', 'deterministico'),
    }
    if sugestao.get('justificativa'):
        resposta['justificativa'] = sugestao['justificativa']
    return JsonResponse(resposta)
