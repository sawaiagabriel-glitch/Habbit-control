from datetime import date, timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.core.management import call_command
from django.core.exceptions import ValidationError
from unittest.mock import patch

from apps.login_cadastro_app.models import Cliente, Parceiro
from apps.pagina_interna.models import Habito, Meta, MetaCiclo, RegistroAtividade
from apps.pagina_interna.services import atualizar_ciclos_meta, inicio_periodo


class MetaProgressTest(TestCase):
    """Testa regras de ciclo, progresso, streak e ações do Cliente."""
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome_completo='Cliente Teste',
            idade=30,
            email='cliente@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Leitura',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=1,
            frequencia_desejada_periodo='dia',
        )
        self.meta = Meta.objects.create(
            habito=self.habito,
            quantidade_minima=2,
            periodo='dia',
            data_inicio=date.today(),
        )

    def test_ciclo_ativo_mostra_progresso_e_meta_cumprida_atualiza_streak(self):
        RegistroAtividade.objects.create(habito=self.habito, data=date.today(), quantidade=1)
        atualizar_ciclos_meta(self.meta, hoje=date.today())
        ciclo = MetaCiclo.objects.get(meta=self.meta, inicio=date.today())
        self.assertEqual(ciclo.estado, MetaCiclo.ESTADO_ATIVA)
        self.assertEqual(ciclo.progresso, 1)
        self.assertEqual(self.meta.streak, 0)

        RegistroAtividade.objects.filter(habito=self.habito, data=date.today()).update(quantidade=2)
        atualizar_ciclos_meta(self.meta, hoje=date.today())
        ciclo.refresh_from_db()
        self.meta.refresh_from_db()
        self.assertEqual(ciclo.estado, MetaCiclo.ESTADO_CUMPRIDA)
        self.assertEqual(ciclo.progresso, 2)
        self.assertEqual(self.meta.streak, 0)
        self.assertEqual(ciclo.percentual, 100)

        atualizar_ciclos_meta(self.meta, hoje=date.today() + timedelta(days=1))
        self.meta.refresh_from_db()
        self.assertEqual(self.meta.streak, 1)

    def test_progresso_percentual_e_limitado_a_cem(self):
        RegistroAtividade.objects.create(habito=self.habito, data=date.today(), quantidade=1)
        ciclos = atualizar_ciclos_meta(self.meta, hoje=date.today())
        self.assertEqual(ciclos[-1].percentual, 50)

        RegistroAtividade.objects.filter(habito=self.habito, data=date.today()).update(quantidade=5)
        ciclos = atualizar_ciclos_meta(self.meta, hoje=date.today())
        self.assertEqual(ciclos[-1].percentual, 100)
        self.assertIsNotNone(ciclos[-1].data_cumprimento)

        RegistroAtividade.objects.filter(habito=self.habito, data=date.today()).update(quantidade=1)
        ciclos = atualizar_ciclos_meta(self.meta, hoje=date.today())
        self.assertEqual(ciclos[-1].estado, MetaCiclo.ESTADO_ATIVA)
        self.assertEqual(ciclos[-1].percentual, 50)
        self.assertIsNone(ciclos[-1].data_cumprimento)

    def test_periodos_semanais_mensais_e_anuais_seguem_calendario_civil(self):
        self.assertEqual(inicio_periodo(date(2026, 10, 22), 'semana'), date(2026, 10, 19))
        self.assertEqual(inicio_periodo(date(2026, 10, 22), 'mes'), date(2026, 10, 1))
        self.assertEqual(inicio_periodo(date(2026, 10, 22), 'ano'), date(2026, 1, 1))

    def test_fechamento_mensal_incrementa_streak_uma_vez(self):
        self.meta.periodo = 'mes'
        self.meta.quantidade_minima = 1
        self.meta.data_inicio = date(2026, 1, 18)
        self.meta.save()
        RegistroAtividade.objects.create(habito=self.habito, data=date(2026, 1, 20), quantidade=1)

        ciclos = atualizar_ciclos_meta(self.meta, hoje=date(2026, 1, 31))
        self.assertEqual(ciclos[0].inicio, date(2026, 1, 1))
        self.assertEqual(ciclos[0].fim, date(2026, 1, 31))
        self.assertEqual(self.meta.streak, 0)

        atualizar_ciclos_meta(self.meta, hoje=date(2026, 2, 1))
        self.meta.refresh_from_db()
        self.assertEqual(self.meta.streak, 1)
        atualizar_ciclos_meta(self.meta, hoje=date(2026, 2, 1))
        self.meta.refresh_from_db()
        self.assertEqual(self.meta.streak, 1)

    def test_ciclo_encerrado_sem_meta_cumprida_reinicia_streak(self):
        anteontem = date.today() - timedelta(days=2)
        ontem = date.today() - timedelta(days=1)
        self.meta.data_inicio = anteontem
        self.meta.save(update_fields=['data_inicio'])
        RegistroAtividade.objects.create(habito=self.habito, data=anteontem, quantidade=2)
        atualizar_ciclos_meta(self.meta, hoje=anteontem)
        self.assertEqual(self.meta.streak, 0)

        atualizar_ciclos_meta(self.meta, hoje=date.today())
        ciclo_cumprido = MetaCiclo.objects.get(meta=self.meta, inicio=anteontem)
        ciclo_perdido = MetaCiclo.objects.get(meta=self.meta, inicio=ontem)
        ciclo_atual = MetaCiclo.objects.get(meta=self.meta, inicio=date.today())
        self.meta.refresh_from_db()
        self.assertEqual(ciclo_cumprido.estado, MetaCiclo.ESTADO_CUMPRIDA)
        self.assertEqual(ciclo_perdido.estado, MetaCiclo.ESTADO_NAO_CUMPRIDA)
        self.assertEqual(ciclo_atual.estado, MetaCiclo.ESTADO_ATIVA)
        self.assertEqual(self.meta.streak, 0)

    def test_todos_os_periodos_suportados_criam_ciclo_ativo(self):
        for periodo in ('dia', 'semana', 'mes', 'ano'):
            with self.subTest(periodo=periodo):
                habito = Habito.objects.create(
                    cliente=self.cliente,
                    tipo_habito='positivo',
                    nome_habito=f'Hábito {periodo}',
                    frequencia_atual_valor=1,
                    frequencia_atual_periodo='dia',
                    frequencia_desejada_valor=1,
                    frequencia_desejada_periodo='dia',
                )
                meta = Meta.objects.create(
                    habito=habito,
                    quantidade_minima=1,
                    periodo=periodo,
                    data_inicio=date.today(),
                )
                ciclos = atualizar_ciclos_meta(meta, hoje=date.today())
                self.assertEqual(len(ciclos), 1)
                self.assertEqual(ciclos[0].estado, MetaCiclo.ESTADO_ATIVA)

    def test_registro_diario_atualiza_ciclo_e_streak(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        response = self.client.post(
            reverse('registrar_atividade'),
            data=f'{{"habito_id": {self.habito.id}, "quantidade": 2, "data": "{date.today().isoformat()}"}}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        ciclo = MetaCiclo.objects.get(meta=self.meta, inicio=date.today())
        self.meta.refresh_from_db()
        self.assertEqual(ciclo.progresso, 2)
        self.assertEqual(ciclo.estado, MetaCiclo.ESTADO_CUMPRIDA)
        self.assertEqual(self.meta.streak, 0)

    def test_api_registro_atividade_com_csrf_recalcula_meta(self):
        client = Client(enforce_csrf_checks=True)
        login_page = client.get(reverse('login'))
        csrf_token = login_page.cookies['csrftoken'].value
        client.post(reverse('login'), {
            'csrfmiddlewaretoken': csrf_token,
            'email': self.cliente.email,
            'password': 'senha123',
        })
        response = client.post(
            reverse('registrar_atividade'),
            data=f'{{"habito_id": {self.habito.id}, "quantidade": 2, "data": "{date.today().isoformat()}"}}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 200)
        ciclo = MetaCiclo.objects.get(meta=self.meta, inicio=date.today())
        self.assertEqual(ciclo.estado, MetaCiclo.ESTADO_CUMPRIDA)
        self.assertIsNotNone(ciclo.data_cumprimento)

    def test_cliente_cria_meta_para_habito_proprio(self):
        habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Alongamento',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=1,
            frequencia_desejada_periodo='dia',
        )
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        response = self.client.post(reverse('metas'), {
            'habito': habito.id,
            'quantidade_minima': 3,
            'periodo': 'semana',
        })
        self.assertRedirects(response, reverse('metas'))
        criada = Meta.objects.get(habito=habito, quantidade_minima=3)
        self.assertEqual(criada.periodo, 'semana')
        self.assertEqual(
            criada.ciclos.get(inicio=inicio_periodo(date.today(), 'semana')).estado,
            MetaCiclo.ESTADO_ATIVA,
        )
        response = self.client.get(reverse('metas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alongamento')
        self.assertContains(response, '0 / 3')

    def test_nao_permite_meta_para_habito_negativo_ou_meta_duplicada(self):
        from apps.pagina_interna.forms import MetaForm

        negativo = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='negativo',
            nome_habito='Refrigerante',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=0,
            frequencia_desejada_periodo='dia',
        )
        form_negativa = MetaForm({
            'habito': negativo.id,
            'quantidade_minima': 1,
            'periodo': 'dia',
        }, cliente=self.cliente)
        self.assertFalse(form_negativa.is_valid())
        with self.assertRaises(ValidationError):
            Meta.objects.create(
                habito=negativo,
                quantidade_minima=1,
                periodo='dia',
            )

        form_duplicada = MetaForm({
            'habito': self.habito.id,
            'quantidade_minima': 3,
            'periodo': 'semana',
        }, cliente=self.cliente)
        self.assertFalse(form_duplicada.is_valid())

    def test_nao_permite_converter_para_negativo_habito_com_meta(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        response = self.client.post(reverse('editar_habito', args=[self.habito.id]), {
            'tipo_habito': 'negativo',
            'nome_habito': self.habito.nome_habito,
            'frequencia_valor': 1,
            'periodo': 'dia',
            'frequencia_desejada_valor': 1,
            'periodo_desejado': 'dia',
        })
        self.assertEqual(response.status_code, 200)
        self.habito.refresh_from_db()
        self.assertEqual(self.habito.tipo_habito, 'positivo')

    def test_comando_processa_fechamento_de_ciclo(self):
        self.meta.periodo = 'mes'
        self.meta.quantidade_minima = 1
        self.meta.data_inicio = date(2026, 1, 18)
        self.meta.save()
        RegistroAtividade.objects.create(habito=self.habito, data=date(2026, 1, 20), quantidade=1)

        with patch('apps.pagina_interna.services.timezone.localdate', return_value=date(2026, 2, 1)):
            call_command('atualizar_ciclos_metas', verbosity=0)

        self.meta.refresh_from_db()
        self.assertEqual(self.meta.streak, 1)
        ciclo = MetaCiclo.objects.get(meta=self.meta, inicio=date(2026, 1, 1))
        self.assertEqual(ciclo.estado, MetaCiclo.ESTADO_CUMPRIDA)

    def test_cliente_partilha_meta_pelo_formulario_e_parceiro_visualiza(self):
        parceiro = Parceiro.objects.create(
            nome_completo='Parceiro Compartilhado',
            email='acompanhante@teste.com',
            password='senhaParceiro123',
        )
        habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Meditação',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=1,
            frequencia_desejada_periodo='dia',
        )
        cliente_browser = Client(enforce_csrf_checks=True)
        login_page = cliente_browser.get(reverse('login'))
        login_token = login_page.cookies['csrftoken'].value
        cliente_browser.post(reverse('login'), {
            'csrfmiddlewaretoken': login_token,
            'email': self.cliente.email,
            'password': 'senha123',
        })

        metas_page = cliente_browser.get(reverse('metas'))
        csrf_token = metas_page.cookies['csrftoken'].value
        response = cliente_browser.post(reverse('metas'), {
            'csrfmiddlewaretoken': csrf_token,
            'habito': habito.id,
            'quantidade_minima': 4,
            'periodo': 'semana',
            'parceiros': [parceiro.id],
        })
        self.assertRedirects(response, reverse('metas'))
        meta = Meta.objects.get(habito=habito)
        self.assertQuerySetEqual(meta.parceiros.all(), [parceiro])

        parceiro_browser = Client(enforce_csrf_checks=True)
        partner_login_page = parceiro_browser.get(reverse('login_parceiro'))
        csrf_token = partner_login_page.cookies['csrftoken'].value
        response = parceiro_browser.post(reverse('login_parceiro'), {
            'csrfmiddlewaretoken': csrf_token,
            'email': parceiro.email,
            'password': 'senhaParceiro123',
        })
        self.assertRedirects(response, reverse('metas_partilhadas'))
        response = parceiro_browser.get(reverse('metas_partilhadas'))
        self.assertContains(response, 'Meditação')

    def test_cliente_exclui_meta_sem_apagar_habito_ou_atividades(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        atividade = RegistroAtividade.objects.create(
            habito=self.habito,
            data=date.today(),
            quantidade=2,
        )
        response = self.client.post(reverse('excluir_meta', args=[self.meta.id]))
        self.assertRedirects(response, reverse('metas'))
        self.assertFalse(Meta.objects.filter(pk=self.meta.pk).exists())
        self.assertTrue(Habito.objects.filter(pk=self.habito.pk).exists())
        self.assertTrue(RegistroAtividade.objects.filter(pk=atividade.pk).exists())


class ParceiroAcompanhamentoTest(TestCase):
    """Testa partilha de metas e limites de leitura do Parceiro."""
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome_completo='Cliente Compartilhado',
            idade=28,
            email='dono@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.parceiro = Parceiro.objects.create(
            nome_completo='Parceiro Teste',
            email='parceiro@teste.com',
            password='senha123',
        )
        self.habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Caminhada',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=1,
            frequencia_desejada_periodo='dia',
        )
        self.meta = Meta.objects.create(
            habito=self.habito,
            quantidade_minima=1,
            periodo='dia',
            data_inicio=date.today(),
        )
        self.meta.parceiros.add(self.parceiro)

    def test_parceiro_autentica_e_visualiza_metas_partilhadas(self):
        client = Client(enforce_csrf_checks=True)
        cadastro = client.get(reverse('cadastro_parceiro'))
        csrf_token = cadastro.cookies['csrftoken'].value
        response_cadastro = client.post(reverse('cadastro_parceiro'), {
            'csrfmiddlewaretoken': csrf_token,
            'nome_completo': 'Parceiro Novo',
            'email': 'novo@teste.com',
            'password': 'senhaParceiro123',
        })
        self.assertRedirects(response_cadastro, reverse('login_parceiro'))

        login_page = client.get(reverse('login_parceiro'))
        csrf_token = login_page.cookies['csrftoken'].value
        response_login = client.post(reverse('login_parceiro'), {
            'csrfmiddlewaretoken': csrf_token,
            'email': 'NOVO@TESTE.COM',
            'password': 'senhaParceiro123',
        })
        self.assertRedirects(response_login, reverse('metas_partilhadas'))

        self.meta.parceiros.add(Parceiro.objects.get(email='novo@teste.com'))
        response = client.get(reverse('metas_partilhadas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Caminhada')
        self.assertContains(response, 'Cliente Compartilhado')

    def test_parceiro_nao_pode_escrever_dados_de_cliente(self):
        self.client.post(reverse('login_parceiro'), {
            'email': self.parceiro.email,
            'password': 'senha123',
        })
        response = self.client.get(reverse('editar_habito', args=[self.habito.id]))
        self.assertRedirects(response, reverse('login'))
        response = self.client.post(
            reverse('update_cliente'),
            data='{"field":"idade","value":99}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.post(reverse('editar_habito', args=[self.habito.id]), {'excluir': '1'})
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(Habito.objects.filter(pk=self.habito.pk).exists())
        response = self.client.post(
            reverse('registrar_atividade'),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.post(reverse('metas'), {
            'habito': self.habito.id,
            'quantidade_minima': 4,
            'periodo': 'dia',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(Meta.objects.filter(habito=self.habito, quantidade_minima=4).exists())

    def test_login_cliente_limpa_sessao_de_parceiro(self):
        self.client.post(reverse('login_parceiro'), {
            'email': self.parceiro.email,
            'password': 'senha123',
        })
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        self.assertEqual(self.client.session.get('cliente_email'), self.cliente.email)
        self.assertNotIn('parceiro_email', self.client.session)

    def test_parceiro_nao_visualiza_meta_de_outra_pessoa(self):
        outro = Parceiro.objects.create(
            nome_completo='Outro Parceiro',
            email='outro@teste.com',
            password='senha123',
        )
        self.client.post(reverse('login_parceiro'), {
            'email': outro.email,
            'password': 'senha123',
        })
        response = self.client.get(reverse('metas_partilhadas'))
        self.assertNotContains(response, 'Caminhada')
