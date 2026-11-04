from datetime import date, datetime, timedelta
import json

from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.login_cadastro_app.models import Cliente
from .access import get_cliente_from_session
from .models import Habito, Meta, RegistroAtividade
from .progresso import obter_dados_relatorio
from .services import atualizar_ciclos_meta, obter_resumo_meta

_MSG_LOGIN = 'Por favor, faça login para acessar esta página.'


def _cliente_ou_redirect_login(request):
	"""Resolve o Cliente da sessão ou devolve redirect para login com warning."""
	cliente, _ = get_cliente_from_session(request)
	if cliente:
		return cliente, None
	messages.warning(request, _MSG_LOGIN)
	return None, redirect('login')


def _habitos_do_cliente(cliente):
	"""Lista de hábitos do cliente com contagens usadas nas páginas internas."""
	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')
	return {
		'habitos': habitos,
		'total_habitos': habitos.count(),
		'habitos_positivos': habitos.filter(tipo_habito='positivo').count(),
		'habitos_negativos': habitos.filter(tipo_habito='negativo').count(),
	}


def _ler_campos_form_habito(post):
	return {
		'tipo_habito': post.get('tipo_habito'),
		'nome_habito': post.get('nome_habito'),
		'frequencia_atual_valor': post.get('frequencia_valor'),
		'frequencia_atual_periodo': post.get('periodo'),
		'frequencia_desejada_valor': post.get('frequencia_desejada_valor'),
		'frequencia_desejada_periodo': post.get('periodo_desejado'),
	}


def _validar_campos_form_habito(campos):
	"""Valida o formulário de hábito.

	Returns:
		``(dados, None)`` em sucesso ou ``(None, mensagem_de_erro)`` em falha.
		As mensagens são as mesmas já usadas pelas views de cadastro/edição.
	"""
	obrigatorios = (
		campos['tipo_habito'],
		campos['nome_habito'],
		campos['frequencia_atual_valor'],
		campos['frequencia_atual_periodo'],
		campos['frequencia_desejada_valor'],
		campos['frequencia_desejada_periodo'],
	)
	if not all(obrigatorios):
		return None, 'Por favor, preencha todos os campos.'

	try:
		freq_atual = int(campos['frequencia_atual_valor'])
		freq_desejada = int(campos['frequencia_desejada_valor'])
	except ValueError:
		return None, 'Os valores de frequência devem ser números válidos.'

	if freq_atual < 0 or freq_desejada < 0:
		return None, 'As frequências não podem ser negativas.'

	return {
		'tipo_habito': campos['tipo_habito'],
		'nome_habito': campos['nome_habito'],
		'frequencia_atual_valor': freq_atual,
		'frequencia_atual_periodo': campos['frequencia_atual_periodo'],
		'frequencia_desejada_valor': freq_desejada,
		'frequencia_desejada_periodo': campos['frequencia_desejada_periodo'],
	}, None


def _parse_data_iso(valor, padrao=None):
	"""Converte string YYYY-MM-DD em date; em falha devolve ``padrao`` ou hoje."""
	if padrao is None:
		padrao = date.today()
	try:
		if isinstance(valor, str):
			return datetime.strptime(valor, '%Y-%m-%d').date()
		if isinstance(valor, date):
			return valor
	except (ValueError, TypeError):
		pass
	return padrao


def alterar_dados(request):
	try:
		cliente, redirect_response = _cliente_ou_redirect_login(request)
		if redirect_response:
			return redirect_response

		context = {'cliente': cliente}
		return render(request, 'pagina_interna/alterar_dados_cliente.html', context)
	except Exception as e:
		print(f"Erro ao buscar cliente: {str(e)}")
		messages.error(request, 'Erro ao carregar seus dados. Por favor, tente novamente.')
		return redirect('login')


def cadastro_garantia(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	messages.info(request, 'A funcionalidade de cadastro de garantia não está disponível no momento.')
	return redirect('alterar_dados')


def consultar_garantia(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	messages.info(request, 'A funcionalidade de consulta de garantia não está disponível no momento.')
	return redirect('alterar_dados')


def cadastro_habito(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	if request.method == 'POST':
		try:
			dados, erro = _validar_campos_form_habito(_ler_campos_form_habito(request.POST))
			if erro:
				messages.error(request, erro)
				return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})

			Habito.objects.create(cliente=cliente, **dados)
			messages.success(request, f'Hábito "{dados["nome_habito"]}" cadastrado com sucesso!')
			return redirect('cadastro_habito')

		except Exception as e:
			messages.error(request, f'Erro ao cadastrar hábito: {str(e)}')
			return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})

	return render(request, 'pagina_interna/cadastro_habito.html', {'cliente': cliente})


def dashboard(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	stats = _habitos_do_cliente(cliente)
	habitos = stats['habitos']

	hoje = date.today()
	atividade_hoje = []
	for habito in habitos:
		registro = RegistroAtividade.objects.filter(habito=habito, data=hoje).first()
		atividade_hoje.append({
			'habito': habito,
			'quantidade': registro.quantidade if registro else 0
		})

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

	atividades_recentes = RegistroAtividade.objects.filter(
		habito__cliente=cliente
	).select_related('habito').order_by('-data', '-data_criacao')[:8]

	metas_cliente = (
		Meta.objects.filter(habito__cliente=cliente)
		.select_related('habito', 'plano_assistente')
		.order_by('-data_criacao')
	)
	metas_resumo = [obter_resumo_meta(meta) for meta in metas_cliente]

	context = {
		'cliente': cliente,
		'habitos': habitos,
		'total_habitos': stats['total_habitos'],
		'habitos_positivos': stats['habitos_positivos'],
		'habitos_negativos': stats['habitos_negativos'],
		'atividade_hoje': atividade_hoje,
		'habito_selecionado': habito_selecionado,
		'progresso_atual': progresso_atual,
		'periodo_progresso': periodo_progresso,
		'atividades_recentes': atividades_recentes,
		'metas_resumo': metas_resumo,
	}

	return render(request, 'pagina_interna/dashboard.html', context)


def progressos(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	stats = _habitos_do_cliente(cliente)
	context = {
		'cliente': cliente,
		'habitos': stats['habitos'],
		'total_habitos': stats['total_habitos'],
		'habitos_positivos': stats['habitos_positivos'],
		'habitos_negativos': stats['habitos_negativos'],
	}

	return render(request, 'pagina_interna/progressos.html', context)


def atividade_diaria(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	data_selecionada = _parse_data_iso(
		request.GET.get('data', date.today().isoformat()),
		padrao=date.today(),
	)

	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')

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
		'data_minima': date.today() - timedelta(days=365),
		'data_maxima': date.today()
	}

	return render(request, 'pagina_interna/atividade_diaria.html', context)


def relatorios(request):
	cliente, redirect_response = _cliente_ou_redirect_login(request)
	if redirect_response:
		return redirect_response

	habitos = Habito.objects.filter(cliente=cliente).order_by('-data_criacao')

	context = {
		'cliente': cliente,
		'habitos': habitos
	}

	return render(request, 'pagina_interna/relatorios.html', context)


def api_dados_relatorio(request):
	cliente, _ = get_cliente_from_session(request)

	if not cliente:
		return JsonResponse({'success': False, 'error': 'Usuário não autenticado'}, status=401)

	if request.method == 'GET':
		try:
			habito_id = request.GET.get('habito_id')
			periodo = request.GET.get('periodo', 'mes')

			if not habito_id:
				return JsonResponse({'success': False, 'error': 'Hábito não especificado'}, status=400)

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
	cliente, _ = get_cliente_from_session(request)

	if not cliente:
		# Parceiro autenticado também é barrado, sem flash de warning de cliente.
		if not request.session.get('parceiro_email'):
			messages.warning(request, _MSG_LOGIN)
		return redirect('login')

	try:
		habito = Habito.objects.get(id=habito_id, cliente=cliente)
	except Habito.DoesNotExist:
		messages.error(request, 'Hábito não encontrado ou você não tem permissão para editá-lo.')
		return redirect('progressos')

	if request.method == 'POST' and 'excluir' in request.POST:
		try:
			nome_habito = habito.nome_habito
			habito.delete()
			messages.error(request, f'Hábito "{nome_habito}" foi apagado com sucesso!')
			return redirect('progressos')
		except Exception as e:
			messages.error(request, f'Erro ao excluir hábito: {str(e)}')
			return redirect('progressos')

	if request.method == 'POST':
		try:
			dados, erro = _validar_campos_form_habito(_ler_campos_form_habito(request.POST))
			if erro:
				messages.error(request, erro)
				return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})

			if dados['tipo_habito'] == 'negativo' and habito.metas.exists():
				messages.error(request, 'Exclua a meta antes de converter o hábito para negativo.')
				return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})

			habito.tipo_habito = dados['tipo_habito']
			habito.nome_habito = dados['nome_habito']
			habito.frequencia_atual_valor = dados['frequencia_atual_valor']
			habito.frequencia_atual_periodo = dados['frequencia_atual_periodo']
			habito.frequencia_desejada_valor = dados['frequencia_desejada_valor']
			habito.frequencia_desejada_periodo = dados['frequencia_desejada_periodo']
			habito.save()

			messages.success(request, f'Hábito "{dados["nome_habito"]}" atualizado com sucesso!')
			return redirect('progressos')

		except Exception as e:
			messages.error(request, f'Erro ao atualizar hábito: {str(e)}')
			return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})

	return render(request, 'pagina_interna/editar_habito.html', {'cliente': cliente, 'habito': habito})


def registrar_atividade(request):
	cliente, _ = get_cliente_from_session(request)

	if not cliente:
		return JsonResponse({'success': False, 'error': 'Usuário não autenticado'}, status=401)

	if request.method == 'POST':
		try:
			data = json.loads(request.body)
			habito_id = data.get('habito_id')
			quantidade = int(data.get('quantidade', 1))
			data_registro = data.get('data', date.today().isoformat())

			if quantidade < 0:
				return JsonResponse({'success': False, 'error': 'A quantidade não pode ser negativa'}, status=400)

			try:
				habito = Habito.objects.get(id=habito_id, cliente=cliente)
			except Habito.DoesNotExist:
				return JsonResponse({'success': False, 'error': 'Hábito não encontrado'}, status=404)

			# Mantém o comportamento anterior: data inválida sobe ValueError
			# e responde com o mesmo erro genérico já coberto pelos testes.
			if isinstance(data_registro, str):
				data_registro = datetime.strptime(data_registro, '%Y-%m-%d').date()

			registro, created = RegistroAtividade.objects.get_or_create(
				habito=habito,
				data=data_registro,
				defaults={'quantidade': quantidade}
			)

			if not created:
				registro.quantidade = quantidade
				registro.save()

			for meta in Meta.objects.filter(habito=habito):
				atualizar_ciclos_meta(meta)

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


@require_POST
def update_cliente(request):
	try:
		data = json.loads(request.body)
		field = data.get('field')
		value = data.get('value')

		if not field or value is None:
			return JsonResponse({'success': False, 'error': 'Campo ou valor inválido'}, status=400)

		cliente, cliente_email = get_cliente_from_session(request)

		if not cliente:
			return JsonResponse({'success': False, 'error': 'Usuário não autenticado. Faça login novamente.'}, status=401)

		field_map = {
			'nome_completo': 'nome_completo',
			'idade': 'idade',
			'email': 'email',
			'password': 'password',
			'cidade': 'cidade',
			'estado': 'estado',
		}

		if field not in field_map:
			print(f"[ERRO] Tentativa de editar campo não permitido: {field}")
			return JsonResponse({'success': False, 'error': f'Campo {field} não permitido'}, status=400)

		model_field = field_map[field]
		response_value = None

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
			response_value = None
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

		try:
			cliente.save()
		except IntegrityError:
			return JsonResponse({'success': False, 'error': 'Este email já está cadastrado'}, status=400)

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
