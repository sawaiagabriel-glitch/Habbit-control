from apps.login_cadastro_app.models import Cliente


def get_cliente_from_session(request):
    """Resolve o Cliente da sessão e remove referências já inválidas.

    Args:
        request: Pedido Django que contém a sessão do navegador.

    Returns:
        Par ``(cliente, email)`` quando a sessão é válida; caso contrário,
        ``(None, None)``.
    """
    email = request.session.get('cliente_email')
    if not email:
        return None, None

    cliente = Cliente.objects.filter(email=email).first()
    if cliente is None:
        request.session.pop('cliente_email', None)
        return None, None

    return cliente, email