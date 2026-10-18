import json
import importlib
import os
from unittest import mock
from django.test import TestCase, Client, SimpleTestCase
from django.urls import reverse
from apps.login_cadastro_app.models import Cliente


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
            profissao="Designer",
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
        campos_bloqueados = ['id', 'data_criacao', 'lgpd', 'is_superuser', 'campo_inexistente']
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

        # Login com a nova senha deve ter sucesso e redirecionar
        resp_nova = novo_client.post(login_url, {
            'email': self.cliente.email,
            'password': nova_senha
        })
        self.assertRedirects(resp_nova, reverse('alterar_dados'))
        self.assertEqual(novo_client.session.get('cliente_email'), self.cliente.email)


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
