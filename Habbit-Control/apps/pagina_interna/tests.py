import json
import importlib
import os
from datetime import date
from unittest import mock
from django.test import TestCase, Client, SimpleTestCase
from django.urls import reverse
from apps.login_cadastro_app.models import Cliente
from apps.pagina_interna.models import Habito, RegistroAtividade


class PerfilClienteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.alterar_dados_url = reverse('alterar_dados')
        self.update_url = reverse('update_cliente')
        self.cliente = Cliente.objects.create(
            nome_completo="Maria Silva",
            idade=28,
            email="maria.silva@example.com",
            password="senhaSegura123",
            cidade="Curitiba",
            estado="PR",
            lgpd=True
        )

    def _autenticar(self):
        session = self.client.session
        session['cliente_email'] = self.cliente.email
        session.save()

    def test_alterar_dados_autenticado_retorna_200_e_campos_editaveis(self):
        self._autenticar()
        response = self.client.get(self.alterar_dados_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Curitiba')
        self.assertContains(response, 'PR')
        # Verifica que os campos Cidade e Estado possuem o ícone de edição
        content = response.content.decode('utf-8')
        self.assertIn('Cidade', content)
        self.assertIn('Estado', content)

    def test_editar_cidade_sucesso(self):
        self._autenticar()
        payload = {'field': 'cidade', 'value': 'Campinas'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('message'), 'Dados atualizados com sucesso')
        
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.cidade, 'Campinas')

    def test_editar_estado_sucesso(self):
        self._autenticar()
        payload = {'field': 'estado', 'value': 'SP'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('message'), 'Dados atualizados com sucesso')
        
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado, 'SP')

    def test_editar_pais_rejeitado(self):
        self._autenticar()
        payload = {'field': 'pais', 'value': 'Brasil'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('error'), 'Campo pais não permitido')

    def test_campos_nao_autorizados_bloqueados(self):
        self._autenticar()
        campos_bloqueados = ['id', 'data_criacao', 'lgpd', 'is_superuser', 'campo_inexistente', 'profissao']
        for campo in campos_bloqueados:
            with self.subTest(campo=campo):
                payload = {'field': campo, 'value': 'valor_qualquer'}
                response = self.client.post(
                    self.update_url,
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 400)
                data = response.json()
                self.assertFalse(data.get('success'))
                self.assertEqual(data.get('error'), f'Campo {campo} não permitido')

    def test_editar_nome_sucesso(self):
        self._autenticar()
        payload = {'field': 'nome_completo', 'value': 'Maria Silva Santos'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nome_completo, 'Maria Silva Santos')

    def test_editar_idade_sucesso(self):
        self._autenticar()
        payload = {'field': 'idade', 'value': 31}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.idade, 31)

    def test_editar_email_valido_sucesso(self):
        self._autenticar()
        payload = {'field': 'email', 'value': '  NOVO.EMAIL@Example.COM '}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.email, 'novo.email@example.com')
        self.assertEqual(self.client.session.get('cliente_email'), 'novo.email@example.com')

    def test_email_duplicado_e_rejeitado(self):
        Cliente.objects.create(
            nome_completo='Outro Usuario',
            idade=40,
            email='jaexiste@example.com',
            password='senhaOutra123',
            lgpd=True
        )
        self._autenticar()
        payload = {'field': 'email', 'value': 'jaexiste@example.com'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('já está cadastrado', data.get('error', ''))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.email, 'maria.silva@example.com')

    def test_profissao_inexistente_e_nao_pode_ser_alterada(self):
        self._autenticar()
        self.assertFalse(
            any(f.name == 'profissao' for f in Cliente._meta.get_fields())
        )
        payload = {'field': 'profissao', 'value': 'Designer'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('error'), 'Campo profissao não permitido')

    def test_pagina_alterar_dados_tem_controles_de_edicao(self):
        self._autenticar()
        response = self.client.get(self.alterar_dados_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('data-field="nome_completo"', content)
        self.assertIn('data-field="idade"', content)
        self.assertIn('data-field="cidade"', content)
        self.assertIn('data-field="estado"', content)
        self.assertIn('data-field="email"', content)
        self.assertIn('data-field="password"', content)
        self.assertIn('edit_profile.js', content)
        self.assertIn('********', content)
        self.assertNotIn('profissao', content.lower())
        self.assertNotIn('Profissão', content)

    def test_update_cliente_nao_autenticado_retorna_401(self):
        payload = {'field': 'cidade', 'value': 'Campinas'}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_senha_valida_pode_ser_alterada(self):
        self._autenticar()
        nova_senha = "NovaSenhaForte@2026"
        payload = {'field': 'password', 'value': nova_senha}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('message'), 'Dados atualizados com sucesso')

        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.check_password(nova_senha))

    def test_senha_invalida_e_rejeitada(self):
        self._autenticar()
        senha_antiga = "senhaSegura123"
        senhas_invalidas = [
            '123',                     # muito curta e inteiramente numérica
            'password',                # senha muito comum
            'maria.silva@example.com', # similar ao email do usuário
            '',                        # vazia
            '   ',                     # apenas espaços
        ]
        for senha_inv in senhas_invalidas:
            with self.subTest(senha=senha_inv):
                payload = {'field': 'password', 'value': senha_inv}
                response = self.client.post(
                    self.update_url,
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 400)
                data = response.json()
                self.assertFalse(data.get('success'))
                self.assertTrue(len(data.get('error', '')) > 0)

                # Confirma que a senha não foi modificada no banco
                self.cliente.refresh_from_db()
                self.assertTrue(self.cliente.check_password(senha_antiga))

    def test_senha_salva_nao_corresponde_ao_texto_puro_informado(self):
        self._autenticar()
        nova_senha = "OutraSenhaSegura#987"
        payload = {'field': 'password', 'value': nova_senha}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        self.cliente.refresh_from_db()
        # Senha salva nunca deve ser igual ao texto puro informado
        self.assertNotEqual(self.cliente.password, nova_senha)
        # Senha salva deve utilizar hash seguro pbkdf2_sha256
        self.assertTrue(self.cliente.password.startswith('pbkdf2_sha256$'))

    def test_login_funciona_com_nova_senha_apos_alteracao(self):
        self._autenticar()
        nova_senha = "NovaSenhaForte@2026"
        payload = {'field': 'password', 'value': nova_senha}
        response = self.client.post(
            self.update_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Cria um novo client deslogado
        novo_client = Client()
        login_url = reverse('login')

        # Login com senha antiga deve falhar
        resp_antiga = novo_client.post(login_url, {
            'email': self.cliente.email,
            'password': 'senhaSegura123'
        })
        self.assertEqual(resp_antiga.status_code, 200)
        self.assertNotIn('cliente_email', novo_client.session)

        # Login com a nova senha deve ter sucesso e redirecionar para a Dashboard
        resp_nova = novo_client.post(login_url, {
            'email': self.cliente.email,
            'password': nova_senha
        })
        self.assertRedirects(resp_nova, reverse('dashboard'))
        self.assertEqual(novo_client.session.get('cliente_email'), self.cliente.email)


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        self.login_url = reverse('login')

        self.cliente = Cliente.objects.create(
            nome_completo="Usuario Dashboard",
            idade=30,
            email="dashboard@example.com",
            password="senhaDashboard123",
            lgpd=True
        )
        self.outro_cliente = Cliente.objects.create(
            nome_completo="Outro Usuario",
            idade=35,
            email="outro@example.com",
            password="senhaOutro123",
            lgpd=True
        )

        self.habito_positivo = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Academia',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=4,
            frequencia_desejada_periodo='semana'
        )
        self.habito_negativo = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='negativo',
            nome_habito='Fumar',
            frequencia_atual_valor=5,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=0,
            frequencia_desejada_periodo='dia'
        )
        self.habito_outro = Habito.objects.create(
            cliente=self.outro_cliente,
            tipo_habito='positivo',
            nome_habito='Hábito Secreto',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=3,
            frequencia_desejada_periodo='dia'
        )

        RegistroAtividade.objects.create(
            habito=self.habito_positivo,
            data=date.today(),
            quantidade=3
        )
        RegistroAtividade.objects.create(
            habito=self.habito_outro,
            data=date.today(),
            quantidade=9
        )

    def _autenticar(self, cliente=None):
        if cliente is None:
            cliente = self.cliente
        session = self.client.session
        session['cliente_email'] = cliente.email
        session.save()

    def test_nao_autenticado_nao_acessa_dashboard(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

    def test_autenticado_acessa_dashboard(self):
        self._autenticar()
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertTemplateUsed(response, 'pagina_interna/dashboard.html')

    def test_dashboard_mostra_somente_habitos_do_usuario(self):
        self._autenticar()
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Academia')
        self.assertContains(response, 'Fumar')
        self.assertNotContains(response, 'Hábito Secreto')
        habitos = list(response.context['habitos'])
        self.assertEqual(len(habitos), 2)
        self.assertTrue(all(h.cliente_id == self.cliente.id for h in habitos))

    def test_contagem_total_habitos_correta(self):
        self._autenticar()
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.context['total_habitos'], 2)

    def test_contagem_positivos_e_negativos_correta(self):
        self._autenticar()
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.context['habitos_positivos'], 1)
        self.assertEqual(response.context['habitos_negativos'], 1)

    def test_registros_de_outro_usuario_nao_aparecem(self):
        self._autenticar()
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

        # Atividade de hoje só do próprio usuário
        nomes_hoje = [item['habito'].nome_habito for item in response.context['atividade_hoje']]
        self.assertIn('Academia', nomes_hoje)
        self.assertIn('Fumar', nomes_hoje)
        self.assertNotIn('Hábito Secreto', nomes_hoje)

        # Atividade recente só do próprio usuário
        for registro in response.context['atividades_recentes']:
            self.assertEqual(registro.habito.cliente_id, self.cliente.id)
            self.assertNotEqual(registro.habito.nome_habito, 'Hábito Secreto')

        self.assertNotContains(response, 'Hábito Secreto')

    def test_login_redireciona_para_dashboard(self):
        response = self.client.post(self.login_url, {
            'email': 'dashboard@example.com',
            'password': 'senhaDashboard123'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.session.get('cliente_email'), 'dashboard@example.com')


class ConfiguracoesSegurancaTest(SimpleTestCase):
    def tearDown(self):
        clean_env = {k: v for k, v in os.environ.items() if k not in ('SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS')}
        with mock.patch.dict(os.environ, clean_env, clear=True):
            import habit_control.settings as s
            importlib.reload(s)

    def test_secret_key_obtida_por_variavel_ambiente(self):
        with mock.patch.dict(os.environ, {'SECRET_KEY': 'segredo-de-teste-12345'}):
            import habit_control.settings as s
            importlib.reload(s)
            self.assertEqual(s.SECRET_KEY, 'segredo-de-teste-12345')

    def test_debug_configuravel_por_variavel_ambiente(self):
        for valor_env, esperado in [('False', False), ('0', False), ('True', True), ('1', True)]:
            with self.subTest(valor=valor_env):
                with mock.patch.dict(os.environ, {'DEBUG': valor_env}):
                    import habit_control.settings as s
                    importlib.reload(s)
                    self.assertEqual(s.DEBUG, esperado)

    def test_allowed_hosts_configuravel_por_variavel_ambiente(self):
        with mock.patch.dict(os.environ, {'ALLOWED_HOSTS': 'app.exemplo.com, api.exemplo.com'}):
            import habit_control.settings as s
            importlib.reload(s)
            self.assertEqual(s.ALLOWED_HOSTS, ['app.exemplo.com', 'api.exemplo.com'])

    def test_configuracao_padrao_desenvolvimento_local(self):
        clean_env = {k: v for k, v in os.environ.items() if k not in ('SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS')}
        with mock.patch.dict(os.environ, clean_env, clear=True):
            import habit_control.settings as s
            importlib.reload(s)
            self.assertTrue(s.DEBUG)
            self.assertEqual(s.ALLOWED_HOSTS, ['*'])
            self.assertTrue(len(s.SECRET_KEY) > 0)
