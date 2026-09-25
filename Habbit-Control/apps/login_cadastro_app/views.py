from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db import IntegrityError
from .forms import ClienteForm, LoginForm
from .models import Cliente

# Create your views here.

def index(request):
    return render(request, 'login_cadastro_app/index.html')

def cadastro_cliente(request):
    """
    Página de cadastro de cliente.
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        
        if form.is_valid():
            try:
                # Verifica se email já existe antes de salvar
                email = form.cleaned_data.get('email')
                cpf = form.cleaned_data.get('cpf')
                
                if Cliente.objects.filter(email=email).exists():
                    messages.error(request, 'Este email já está cadastrado. Por favor, use outro email ou faça login.')
                    return render(request, 'login_cadastro_app/cadastro_cliente.html', {'form': form})
                
                if Cliente.objects.filter(cpf=cpf).exists():
                    messages.error(request, 'Este CPF já está cadastrado. Por favor, use outro CPF ou faça login.')
                    return render(request, 'login_cadastro_app/cadastro_cliente.html', {'form': form})
                
                form.save()
                return redirect('login')
            except IntegrityError as e:
                # Erro de integridade (CPF ou email já existe) - exibe mensagem de erro
                error_msg = str(e)
                if 'email' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                    messages.error(request, 'Este email já está cadastrado. Por favor, use outro email ou faça login.')
                elif 'cpf' in error_msg.lower():
                    messages.error(request, 'Este CPF já está cadastrado. Por favor, use outro CPF ou faça login.')
                else:
                    messages.error(request, 'Erro ao cadastrar. Este email ou CPF já está em uso.')
                return render(request, 'login_cadastro_app/cadastro_cliente.html', {'form': form})
        
        else:
            # Exibe mensagens de erro do formulário, incluindo email/CPF já existentes
            for field, errors in form.errors.items():
                for error in errors:
                    error_lower = str(error).lower()
                    # Verifica se é erro de email/CPF já existente
                    if 'email' in error_lower and ('já existe' in error_lower or 'already exists' in error_lower or 'unique' in error_lower):
                        messages.error(request, 'Este email já está cadastrado. Por favor, use outro email ou faça login.')
                        continue
                    if 'cpf' in error_lower and ('já existe' in error_lower or 'already exists' in error_lower or 'unique' in error_lower):
                        messages.error(request, 'Este CPF já está cadastrado. Por favor, use outro CPF ou faça login.')
                        continue
                    
                    if field == '__all__':
                        messages.error(request, f"{error}")
                    else:
                        label = form.fields[field].label
                        messages.error(request, f"{label}: {error}")
            return render(request, 'login_cadastro_app/cadastro_cliente.html', {'form': form})
    
    else:
        form = ClienteForm()
    
    return render(request, 'login_cadastro_app/cadastro_cliente.html', {'form': form})

# Lógica de Login
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            try:
                # 1. Tenta encontrar o cliente pelo email
                cliente = Cliente.objects.get(email=email)
            except Cliente.DoesNotExist:
                # Limpa mensagens antigas antes de renderizar
                storage = messages.get_messages(request)
                storage.used = True
                return render(request, 'login_cadastro_app/login.html', {'form': form})
            
            # 2. Verifica a senha usando o método check_password do modelo Cliente
            if cliente.check_password(password):
                # Limpa mensagens antigas antes de criar nova mensagem
                storage = messages.get_messages(request)
                storage.used = True
                
                # Autenticação bem-sucedida 
                request.session['cliente_email'] = cliente.email
                messages.success(request, f'Bem-vindo(a), {cliente.nome_completo.split()[0]}!')
                
                # Redireciona para a página interna 
                return redirect('alterar_dados')
            else:
                # Limpa mensagens antigas antes de renderizar
                storage = messages.get_messages(request)
                storage.used = True
                return render(request, 'login_cadastro_app/login.html', {'form': form})
        
        # Se o formulário não for válido, renderiza com erros
        else:
            # Limpa mensagens antigas antes de renderizar
            storage = messages.get_messages(request)
            storage.used = True
            return render(request, 'login_cadastro_app/login.html', {'form': form})
    
    else:
        # Limpa mensagens antigas quando acessa a página de login via GET
        storage = messages.get_messages(request)
        storage.used = True
        form = LoginForm()
        return render(request, 'login_cadastro_app/login.html', {'form': form})

# Lógica de Logout 
def logout_view(request):
    if 'cliente_email' in request.session:
        del request.session['cliente_email']
        messages.success(request, 'Logout realizado com sucesso!')
    else:
        messages.info(request, 'Você não estava logado.')
        
    return redirect('index')

def consentimento(request):
    return render(request, 'login_cadastro_app/consentimento.html')