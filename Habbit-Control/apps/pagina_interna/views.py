from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
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
	#API endpoint para buscar dados do gráfico de relatórios
	from django.http import JsonResponse
	from apps.pagina_interna.models import Habito, RegistroAtividade
	from datetime import date, timedelta
	from django.db.models import Sum
	
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
			
			# Define o período de tempo
			data_fim = date.today()
			if periodo == 'dia':
				data_inicio = data_fim
				intervalo = timedelta(days=1)
			elif periodo == 'semana':
				data_inicio = data_fim - timedelta(days=6)
				intervalo = timedelta(days=1)
			elif periodo == 'mes':
				data_inicio = data_fim - timedelta(days=29)
				intervalo = timedelta(days=1)
			elif periodo == 'ano':
				data_inicio = data_fim - timedelta(days=364)
				intervalo = timedelta(days=7)  # Agrupa por semana no ano
			else:
				return JsonResponse({'success': False, 'error': 'Período inválido'}, status=400)
			
			# Busca registros do período
			registros = RegistroAtividade.objects.filter(
				habito=habito,
				data__gte=data_inicio,
				data__lte=data_fim
			).order_by('data')
			
			# Calcula a frequência desejada normalizada para o período
			freq_desejada_valor = habito.frequencia_desejada_valor
			freq_desejada_periodo = habito.frequencia_desejada_periodo
			
			# Converte frequência desejada para "por dia"
			freq_desejada_por_dia = freq_desejada_valor
			if freq_desejada_periodo == 'semana':
				freq_desejada_por_dia = freq_desejada_valor / 7
			elif freq_desejada_periodo == 'mes':
				freq_desejada_por_dia = freq_desejada_valor / 30
			elif freq_desejada_periodo == 'ano':
				freq_desejada_por_dia = freq_desejada_valor / 365
			
			# Prepara dados para o gráfico
			labels = []
			dados_registrados_acumulados = []
			dados_esperados_acumulados = []
			progresso_percent = []
			
			current_date = data_inicio
			total_registrado_acumulado = 0
			dias_contados = 0
			
			while current_date <= data_fim:
				# Busca registros deste dia/período
				if periodo == 'ano':
					# Para ano, agrupa por semana
					semana_fim = min(current_date + timedelta(days=6), data_fim)
					registros_periodo = registros.filter(
						data__gte=current_date,
						data__lte=semana_fim
					)
					quantidade_periodo = sum(r.quantidade for r in registros_periodo)
					label = f"{current_date.strftime('%d/%m')} - {semana_fim.strftime('%d/%m')}"
					dias_no_periodo = (semana_fim - current_date).days + 1
					dias_contados += dias_no_periodo
					current_date = semana_fim + timedelta(days=1)
				else:
					# Para dia, semana, mês - mostra por dia
					registro_dia = registros.filter(data=current_date).first()
					quantidade_periodo = registro_dia.quantidade if registro_dia else 0
					label = current_date.strftime('%d/%m')
					dias_no_periodo = 1
					dias_contados += 1
					current_date += timedelta(days=1)
				
				# Soma acumulada dos registros
				total_registrado_acumulado += quantidade_periodo
				
				# Calcula o esperado acumulado até este ponto
				esperado_acumulado = freq_desejada_por_dia * dias_contados
				
				# Calcula progresso baseado no acumulado
				if habito.tipo_habito == 'positivo':
					# Para hábitos positivos: quanto mais, melhor
					if esperado_acumulado > 0:
						progresso = min(100, (total_registrado_acumulado / esperado_acumulado) * 100)
					else:
						progresso = 0
				else:
					# Para hábitos negativos: quanto menos, melhor
					if esperado_acumulado > 0:
						progresso = min(100, max(0, (1 - (total_registrado_acumulado / esperado_acumulado)) * 100))
					else:
						progresso = 100 if total_registrado_acumulado == 0 else 0
				
				labels.append(label)
				dados_registrados_acumulados.append(total_registrado_acumulado)
				dados_esperados_acumulados.append(round(esperado_acumulado, 1))
				progresso_percent.append(round(progresso, 2))
			
			# Calcula total registrado no período
			total_registrado_periodo = sum(r.quantidade for r in registros)
			
			# Calcula total esperado no período
			dias_total = (data_fim - data_inicio).days + 1
			if periodo == 'dia':
				total_esperado = freq_desejada_por_dia
			elif periodo == 'semana':
				total_esperado = freq_desejada_por_dia * dias_total
			elif periodo == 'mes':
				total_esperado = freq_desejada_por_dia * dias_total
			else:  # ano
				total_esperado = freq_desejada_por_dia * 365
			
			return JsonResponse({
				'success': True,
				'habito': {
					'id': habito.id,
					'nome': habito.nome_habito,
					'tipo': habito.tipo_habito,
					'frequencia_desejada_valor': habito.frequencia_desejada_valor,
					'frequencia_desejada_periodo': habito.get_frequencia_desejada_periodo_display()
				},
				'periodo': periodo,
				'total_registrado': total_registrado_periodo,
				'total_esperado': round(total_esperado, 1),
				'labels': labels,
				'dados_registrados': dados_registrados_acumulados,
				'dados_esperados': dados_esperados_acumulados,
				'progresso_percent': progresso_percent
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
        
        # 2. LISTA DE CAMPOS PERMITIDOS 
        field_map = {
            'nome_completo': 'nome_completo',
            'idade': 'idade',
            'cpf': 'cpf',
            'email': 'email',
            'password': 'password', # O JS manda 'password', o model tem 'password'
            'cidade': 'cidade',
            'pais': 'pais',
            'profissao': 'profissao'
        }

        # Verifica se o campo enviado é permitido
        if field not in field_map:
            print(f"[ERRO] Tentativa de editar campo não permitido: {field}")
            return JsonResponse({'success': False, 'error': f'Campo {field} não permitido'}, status=400)
        
        model_field = field_map[field]

        # 3. Lógica Especial para Senha
        if model_field == 'password':
            if not value:
                return JsonResponse({'success': False, 'error': 'A senha não pode ser vazia'}, status=400)
            cliente.password = value
        else:

            setattr(cliente, model_field, value)

        # 4. Salvar
        cliente.save()
        
        print(f"[SUCESSO] Cliente {cliente.id} atualizou {model_field}.")
        return JsonResponse({'success': True, 'message': 'Dados atualizados com sucesso'})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        print(f"[ERRO CRÍTICO] {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)