from django.contrib import messages
from django.shortcuts import redirect, render

from apps.login_cadastro_app.models import Parceiro
from .access import get_cliente_from_session
from .forms import MetaForm
from .models import Meta
from .services import atualizar_ciclos_meta


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

    return render(request, 'pagina_interna/metas.html', {
        'cliente': cliente,
        'form': form,
        'metas': metas_cliente,
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