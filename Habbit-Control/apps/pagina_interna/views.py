from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import json
from apps.login_cadastro_app.models import Cliente 

# Create your views here.

def get_cliente_from_session(request):
	"""Função auxiliar para obter o cliente da sessão."""
	cliente_email = request.session.get('cliente_email')
	
	if not cliente_email:
		return None, None
	
	cliente = Cliente.objects.filter(email=cliente_email).first()
	
	if not cliente:
		# Se o email na sessão não existe mais no banco, limpa a sessão
		del request.session['cliente_email']
		return None, None
	
	return cliente, cliente_email

def alterar_dados(request):
	try:
		# Busca o cliente pelo email armazenado na sessão
		cliente, _ = get_cliente_from_session(request)
		
		if not cliente:
			# Se não há email na sessão ou cliente não encontrado, redireciona para login
			messages.warning(request, 'Por favor, faça login para acessar esta página.')
			return redirect('login')
		
		context = {'cliente': cliente}
		return render(request, 'pagina_interna/alterar_dados_cliente.html', context)
	except Exception as e:
		print(f"Erro ao buscar cliente: {str(e)}")
		messages.error(request, 'Erro ao carregar seus dados. Por favor, tente novamente.')
		return redirect('login')


def cadastro_garantia(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	messages.info(request, 'A funcionalidade de cadastro de garantia não está disponível no momento.')
	return redirect('alterar_dados')


def consultar_garantia(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	messages.info(request, 'A funcionalidade de consulta de garantia não está disponível no momento.')
	return redirect('alterar_dados')

def cadastro_habito(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	# Processa o formulário se for POST
	if request.method == 'POST':
		try:
			from apps.pagina_interna.models import Habito
			
			# Obtém os dados do formulário
			tipo_habito = request.POST.get('tipo_habito')
			nome_habito = request.POST.get('nome_habito')
			frequencia_atual_valor = request.POST.get('frequencia_valor')
			frequencia_atual_periodo = request.POST.get('periodo')
			frequencia_desejada_valor = request.POST.get('frequencia_desejada_valor')
			frequencia_desejada_periodo = request.POST.get('periodo_desejado')
			
			# Validação básica
			if not all([tipo_habito, nome_habito, frequencia_atual_valor, frequencia_atual_periodo, 
			           frequencia_desejada_valor, frequencia_desejada_periodo]):
				messages.error(request, 'Por favor, preencha todos os campos.')
				return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})
			
			# Converte e valida valores numéricos
			try:
				freq_atual = int(frequencia_atual_valor)
				freq_desejada = int(frequencia_desejada_valor)
				
				# Valida que os valores sejam >= 0
				if freq_atual < 0 or freq_desejada < 0:
					messages.error(request, 'As frequências não podem ser negativas.')
					return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})
			except ValueError:
				messages.error(request, 'Os valores de frequência devem ser números válidos.')
				return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})
			
			# Cria o hábito
			habito = Habito.objects.create(
				cliente=cliente,
				tipo_habito=tipo_habito,
				nome_habito=nome_habito,
				frequencia_atual_valor=freq_atual,
				frequencia_atual_periodo=frequencia_atual_periodo,
				frequencia_desejada_valor=freq_desejada,
				frequencia_desejada_periodo=frequencia_desejada_periodo
			)
			
			messages.success(request, f'Hábito "{nome_habito}" cadastrado com sucesso!')
			return redirect('cadastro_habito')
			
		except Exception as e:
			messages.error(request, f'Erro ao cadastrar hábito: {str(e)}')
			return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})
	
	# Renderiza a página normalmente para GET
	return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})

def dashboard(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)

	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')

	from apps.pagina_interna.models import Habito, RegistroAtividade
	from apps.pagina_interna.progresso import obter_dados_relatorio
	from datetime import date

	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')
	total_habitos = habitos.count()
	habitos_positivos = habitos.filter(tipo_habito='positivo').count()
	habitos_negativos = habitos.filter(tipo_habito='negativo').count()

	# Atividade de hoje (mesma lógica de atividade_diaria para a data atual)
	hoje = date.today()
	atividade_hoje = []
	for habito in habitos:
		registro = RegistroAtividade.objects.filter(habito=habito, data=hoje).first()
		atividade_hoje.append({
			'habito': habito,
			'quantidade': registro.quantidade if registro else 0
		})

	# Progresso atual — reutiliza a regra de api_dados_relatorio (período padrão: semana)
	habito_selecionado = None
	progresso_atual = None
	habito_id = request.GET.get('habito_id')
	periodo_progresso = request.GET.get('periodo', 'semana')
	if periodo_progresso not in ('dia', 'semana', 'mes', 'ano'):
		periodo_progresso = 'semana'

	if habitos.exists():
		if habito_id:
			habito_selecionado = habitos.filter(id=habito_id).first()
		if not habito_selecionado:
			habito_selecionado = habitos.first()
		progresso_atual = obter_dados_relatorio(habito_selecionado, periodo_progresso)

	# Atividade recente — registros do próprio usuário, ordenados por data
	atividades_recentes = RegistroAtividade.objects.filter(
		habito__cliente=cliente
	).select_related('habito').order_by('-data', '-data_criacao')[:8]

	context = {
		'cliente': cliente,
		'habitos': habitos,
		'total_habitos': total_habitos,
		'habitos_positivos': habitos_positivos,
		'habitos_negativos': habitos_negativos,
		'atividade_hoje': atividade_hoje,
		'habito_selecionado': habito_selecionado,
		'progresso_atual': progresso_atual,
		'periodo_progresso': periodo_progresso,
		'atividades_recentes': atividades_recentes,
	}

	return render(request, 'pagina_interna/dashboard.html', context)


def progressos(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	# Busca todos os hábitos do cliente
	from apps.pagina_interna.models import Habito
	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')
	
	# Calcula estatísticas
	total_habitos = habitos.count()
	habitos_positivos = habitos.filter(tipo_habito='positivo').count()
	habitos_negativos = habitos.filter(tipo_habito='negativo').count()
	
	context = {
		'cliente': cliente,
		'habitos': habitos,
		'total_habitos': total_habitos,
		'habitos_positivos': habitos_positivos,
		'habitos_negativos': habitos_negativos
	}
	
	return render(request, 'pagina_interna/progressos.html', context)

def atividade_diaria(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	from apps.pagina_interna.models import Habito, RegistroAtividade
	from datetime import date, timedelta
	
	# Obtém a data selecionada (padrão: hoje)
	data_selecionada = request.GET.get('data', date.today().isoformat())
	
	try:
		if isinstance(data_selecionada, str):
			from datetime import datetime
			data_selecionada = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
	except (ValueError, TypeError):
		data_selecionada = date.today()
	
	# Busca todos os hábitos do cliente
	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')
	
	# Para cada hábito, busca o registro da data selecionada
	habitos_com_registros = []
	for habito in habitos:
		registro = RegistroAtividade.objects.filter(
			habito=habito,
			data=data_selecionada
		).first()
		habitos_com_registros.append({
			'habito': habito,
			'registro': registro
		})
	
	context = {
		'cliente': cliente,
		'habitos_com_registros': habitos_com_registros,
		'data_selecionada': data_selecionada,
		'data_hoje': date.today(),
		'data_minima': date.today() - timedelta(days=365),  # Permite selecionar até 1 ano atrás
		'data_maxima': date.today()
	}
	
	return render(request, 'pagina_interna/atividade_diaria.html', context)

def relatorios(request):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	from apps.pagina_interna.models import Habito
	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')
	
	context = {
		'cliente': cliente,
		'habitos': habitos
	}
	
	return render(request, 'pagina_interna/relatorios.html', context)

def api_dados_relatorio(request):
	# API endpoint para buscar dados do gráfico de relatórios
	from django.http import JsonResponse
	from apps.pagina_interna.models import Habito
	from apps.pagina_interna.progresso import obter_dados_relatorio

	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)

	if not cliente:
		return JsonResponse({'success': False, 'error': 'Usuário não autenticado'}, status=401)

	if request.method == 'GET':
		try:
			habito_id = request.GET.get('habito_id')
			periodo = request.GET.get('periodo', 'mes')  # dia, semana, mes, ano

			if not habito_id:
				return JsonResponse({'success': False, 'error': 'Hábito não especificado'}, status=400)

			# Busca o hábito e verifica se pertence ao cliente
			try:
				habito = Habito.objects.get(id=habito_id, cliente=cliente)
			except Habito.DoesNotExist:
				return JsonResponse({'success': False, 'error': 'Hábito não encontrado'}, status=404)

			if periodo not in ('dia', 'semana', 'mes', 'ano'):
				return JsonResponse({'success': False, 'error': 'Período inválido'}, status=400)

			dados = obter_dados_relatorio(habito, periodo)

			return JsonResponse({
				'success': True,
				'habito': dados['habito'],
				'periodo': dados['periodo'],
				'total_registrado': dados['total_registrado'],
				'total_esperado': dados['total_esperado'],
				'labels': dados['labels'],
				'dados_registrados': dados['dados_registrados'],
				'dados_esperados': dados['dados_esperados'],
				'progresso_percent': dados['progresso_percent']
			})

		except Exception as e:
			return JsonResponse({'success': False, 'error': str(e)}, status=400)

	return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

def editar_habito(request, habito_id):
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		messages.warning(request, 'Por favor, faça login para acessar esta página.')
		return redirect('login')
	
	from apps.pagina_interna.models import Habito
	
	# Busca o hábito e verifica se pertence ao cliente
	try:
		habito = Habito.objects.get(id=habito_id, cliente=cliente)
	except Habito.DoesNotExist:
		messages.error(request, 'Hábito não encontrado ou você não tem permissão para editá-lo.')
		return redirect('progressos')
	
	# Processa exclusão se for POST com 'excluir'
	if request.method == 'POST' and 'excluir' in request.POST:
		try:
			nome_habito = habito.nome_habito
			habito.delete()
			messages.error(request, f'Hábito "{nome_habito}" foi apagado com sucesso!')
			return redirect('progressos')
		except Exception as e:
			messages.error(request, f'Erro ao excluir hábito: {str(e)}')
			return redirect('progressos')
	
	# Processa edição se for POST
	if request.method == 'POST':
		try:
			# Obtém os dados do formulário
			tipo_habito = request.POST.get('tipo_habito')
			nome_habito = request.POST.get('nome_habito')
			frequencia_atual_valor = request.POST.get('frequencia_valor')
			frequencia_atual_periodo = request.POST.get('periodo')
			frequencia_desejada_valor = request.POST.get('frequencia_desejada_valor')
			frequencia_desejada_periodo = request.POST.get('periodo_desejado')
			
			# Validação básica
			if not all([tipo_habito, nome_habito, frequencia_atual_valor, frequencia_atual_periodo, 
			           frequencia_desejada_valor, frequencia_desejada_periodo]):
				messages.error(request, 'Por favor, preencha todos os campos.')
				return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})
			
			# Converte e valida valores numéricos
			try:
				freq_atual = int(frequencia_atual_valor)
				freq_desejada = int(frequencia_desejada_valor)
				
				# Valida que os valores sejam >= 0
				if freq_atual < 0 or freq_desejada < 0:
					messages.error(request, 'As frequências não podem ser negativas.')
					return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})
			except ValueError:
				messages.error(request, 'Os valores de frequência devem ser números válidos.')
				return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})
			
			# Atualiza o hábito
			habito.tipo_habito = tipo_habito
			habito.nome_habito = nome_habito
			habito.frequencia_atual_valor = freq_atual
			habito.frequencia_atual_periodo = frequencia_atual_periodo
			habito.frequencia_desejada_valor = freq_desejada
			habito.frequencia_desejada_periodo = frequencia_desejada_periodo
			habito.save()
			
			messages.success(request, f'Hábito "{nome_habito}" atualizado com sucesso!')
			return redirect('progressos')
			
		except Exception as e:
			messages.error(request, f'Erro ao atualizar hábito: {str(e)}')
			return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})
	
	# Renderiza a página normalmente para GET
	return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})

def registrar_atividade(request):
	from django.http import JsonResponse
	from apps.pagina_interna.models import Habito, RegistroAtividade
	from datetime import date
	
	# Verifica se o usuário está autenticado
	cliente, _ = get_cliente_from_session(request)
	
	if not cliente:
		return JsonResponse({'success': False, 'error': 'Usuário não autenticado'}, status=401)
	
	if request.method == 'POST':
		try:
			import json
			data = json.loads(request.body)
			habito_id = data.get('habito_id')
			quantidade = int(data.get('quantidade', 1))
			data_registro = data.get('data', date.today().isoformat())
			
			# Valida a quantidade
			if quantidade < 0:
				return JsonResponse({'success': False, 'error': 'A quantidade não pode ser negativa'}, status=400)
			
			# Busca o hábito e verifica se pertence ao cliente
			try:
				habito = Habito.objects.get(id=habito_id, cliente=cliente)
			except Habito.DoesNotExist:
				return JsonResponse({'success': False, 'error': 'Hábito não encontrado'}, status=404)
			
			# Converte a data
			if isinstance(data_registro, str):
				from datetime import datetime
				data_registro = datetime.strptime(data_registro, '%Y-%m-%d').date()
			
			# Busca ou cria o registro da data
			registro, created = RegistroAtividade.objects.get_or_create(
				habito=habito,
				data=data_registro,
				defaults={'quantidade': quantidade}
			)
			
			if not created:
				# Se já existe, atualiza a quantidade
				registro.quantidade = quantidade
				registro.save()
			
			return JsonResponse({
				'success': True,
				'quantidade': registro.quantidade,
				'data': registro.data.isoformat()
			})
			
		except ValueError:
			return JsonResponse({'success': False, 'error': 'Quantidade inválida'}, status=400)
		except Exception as e:
			return JsonResponse({'success': False, 'error': str(e)}, status=400)
	
	return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

def revenda_adm(request):
	return render(request, 'pagina_interna/home.html') 


@require_POST
def update_cliente(request):
    try:
        from django.core.validators import validate_email
        from django.db import IntegrityError

        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value')
        
        # Validação básica
        if not field or value is None: # value pode ser string vazia, mas não None
            return JsonResponse({'success': False, 'error': 'Campo ou valor inválido'}, status=400)
        
        # 1. Busca o Cliente pelo email na sessão
        cliente, cliente_email = get_cliente_from_session(request)
        
        if not cliente:
            return JsonResponse({'success': False, 'error': 'Usuário não autenticado. Faça login novamente.'}, status=401)
        
        # 2. LISTA DE CAMPOS PERMITIDOS (profissao não está e não deve estar)
        field_map = {
            'nome_completo': 'nome_completo',
            'idade': 'idade',
            'email': 'email',
            'password': 'password', # O JS manda 'password', o model tem 'password'
            'cidade': 'cidade',
            'estado': 'estado',
        }

        # Verifica se o campo enviado é permitido
        if field not in field_map:
            print(f"[ERRO] Tentativa de editar campo não permitido: {field}")
            return JsonResponse({'success': False, 'error': f'Campo {field} não permitido'}, status=400)
        
        model_field = field_map[field]
        response_value = None

        # 3. Validações e atualização por campo
        if model_field == 'password':
            if not value or not str(value).strip():
                return JsonResponse({'success': False, 'error': 'A senha não pode ser vazia'}, status=400)
            raw_password = str(value)
            try:
                validate_password(raw_password, user=cliente)
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'error': '; '.join(e.messages),
                    'errors': list(e.messages)
                }, status=400)
            cliente.password = raw_password
            response_value = None  # nunca devolver senha
        elif model_field == 'nome_completo':
            nome = str(value).strip()
            if not nome:
                return JsonResponse({'success': False, 'error': 'O nome completo não pode ficar vazio'}, status=400)
            if len(nome) > 255:
                return JsonResponse({'success': False, 'error': 'O nome completo é muito longo'}, status=400)
            cliente.nome_completo = nome
            response_value = nome
        elif model_field == 'idade':
            try:
                idade = int(value)
            except (TypeError, ValueError):
                return JsonResponse({'success': False, 'error': 'A idade deve ser um número inteiro válido'}, status=400)
            if idade < 0:
                return JsonResponse({'success': False, 'error': 'A idade não pode ser negativa'}, status=400)
            cliente.idade = idade
            response_value = idade
        elif model_field == 'email':
            email = str(value).lower().strip()
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'error': 'Informe um e-mail válido'}, status=400)
            if Cliente.objects.filter(email=email).exclude(pk=cliente.pk).exists():
                return JsonResponse({'success': False, 'error': 'Este email já está cadastrado'}, status=400)
            cliente.email = email
            response_value = email
        elif model_field == 'estado':
            estado = str(value).strip().upper()
            if estado and len(estado) > 2:
                return JsonResponse({'success': False, 'error': 'Estado inválido'}, status=400)
            cliente.estado = estado or None
            response_value = cliente.estado or ''
        elif model_field == 'cidade':
            cidade = str(value).strip()
            if len(cidade) > 100:
                return JsonResponse({'success': False, 'error': 'A cidade é muito longa'}, status=400)
            cliente.cidade = cidade or None
            response_value = cliente.cidade or ''

        # 4. Salvar
        try:
            cliente.save()
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Este email já está cadastrado'}, status=400)

        # Mantém a sessão alinhada se o e-mail foi alterado
        if model_field == 'email':
            request.session['cliente_email'] = cliente.email
        
        print(f"[SUCESSO] Cliente {cliente.id} atualizou {model_field}.")
        payload = {'success': True, 'message': 'Dados atualizados com sucesso'}
        if response_value is not None:
            payload['value'] = response_value
        return JsonResponse(payload)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        print(f"[ERRO CRÍTICO] {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
