import json
from django.test import TestCase, Client
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
