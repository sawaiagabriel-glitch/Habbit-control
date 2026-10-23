from django.contrib import messages
from django.shortcuts import redirect, render

from .models import Parceiro


def cadastro_parceiro(request):
    """Cria uma conta de Parceiro com email normalizado e senha protegida."""
    if request.method == 'POST':
        nome = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')

        if not nome or not email or not password:
            messages.error(request, 'Preencha todos os campos.')
        elif Parceiro.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está associado a um parceiro.')
        else:
            Parceiro.objects.create(
                nome_completo=nome,
                email=email,
                password=password,
            )
            messages.success(request, 'Conta de parceiro criada com sucesso.')
            return redirect('login_parceiro')

    return render(request, 'login_cadastro_app/cadastro_parceiro.html')


def login_parceiro(request):
    """Autentica o Parceiro e inicia uma sessão exclusiva desse perfil."""
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        parceiro = Parceiro.objects.filter(email=email).first()

        if parceiro and parceiro.check_password(password):
            request.session.flush()
            request.session['parceiro_email'] = parceiro.email
            return redirect('metas_partilhadas')

        messages.error(request, 'Email ou senha inválidos.')

    return render(request, 'login_cadastro_app/login_parceiro.html')