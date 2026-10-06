from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from apps.login_cadastro_app.models import Cliente
from apps.login_cadastro_app.forms import ClienteForm, LoginForm


class ClienteModelTest(TestCase):
    def test_criar_cliente_sem_cpf(self):
        cliente = Cliente.objects.create(
            nome_completo="Gabriel Silva",
            idade=25,
            email="GABRIEL@EXAMPLE.COM ",
            password="minhasenha123",
            lgpd=True
        )
        self.assertIsNotNone(cliente.id)
        # Verifica normalização do email
        self.assertEqual(cliente.email, "gabriel@example.com")
        # Verifica que a senha foi hasheada
        self.assertTrue(cliente.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(cliente.check_password("minhasenha123"))
        # Verifica __str__
        self.assertEqual(str(cliente), "Gabriel Silva - gabriel@example.com")

    def test_email_unico_no_modelo(self):
        Cliente.objects.create(
            nome_completo="Usuario 1",
            idade=30,
            email="duplicado@example.com",
            password="senha",
            lgpd=True
        )
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nome_completo="Usuario 2",
                idade=28,
                email="duplicado@example.com",
                password="outrasenha",
                lgpd=True
            )


class ClienteFormTest(TestCase):
    def test_formulario_sem_campo_cpf(self):
        form = ClienteForm()
        self.assertNotIn('cpf', form.fields)
        self.assertIn('nome_completo', form.fields)
        self.assertIn('idade', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('password', form.fields)

    def test_formulario_valido(self):
        data = {
            'nome_completo': 'Maria Santos',
            'idade': 22,
            'email': '  MARIA@TEST.COM ',
            'password': 'senhaSegura123',
            'lgpd': True,
        }
        form = ClienteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['email'], 'maria@test.com')

    def test_formulario_rejeita_email_duplicado(self):
        Cliente.objects.create(
            nome_completo="Existente",
            idade=35,
            email="existente@test.com",
            password="123",
            lgpd=True
        )
        data = {
            'nome_completo': 'Novo Usuario',
            'idade': 29,
            'email': 'EXISTENTE@test.com',
            'password': 'outrasenha',
            'lgpd': True,
        }
        form = ClienteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('já está cadastrado', form.errors['email'][0])


class CadastroClienteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cadastro_url = reverse('cadastro_cliente')

    def test_get_cadastro_retorna_200(self):
        response = self.client.get(self.cadastro_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '000.000.000-00')
        self.assertNotContains(response, 'id_cpf')

    def test_post_cadastro_sucesso(self):
        data = {
            'nome_completo': 'Carlos Pereira',
            'idade': 40,
            'email': '  CARLOS@GMAIL.COM  ',
            'password': 'senhaForte@123',
            'lgpd': True
        }
        response = self.client.post(self.cadastro_url, data)
        self.assertRedirects(response, reverse('login'))
        cliente = Cliente.objects.get(email='carlos@gmail.com')
        self.assertEqual(cliente.nome_completo, 'Carlos Pereira')
        self.assertTrue(cliente.check_password('senhaForte@123'))

    def test_post_cadastro_email_duplicado(self):
        Cliente.objects.create(
            nome_completo='Usuario Original',
            idade=30,
            email='original@gmail.com',
            password='123',
            lgpd=True
        )
        data = {
            'nome_completo': 'Usuario Duplicado',
            'idade': 25,
            'email': 'ORIGINAL@GMAIL.COM',
            'password': '456',
            'lgpd': True
        }
        response = self.client.post(self.cadastro_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cliente.objects.filter(email='original@gmail.com').count(), 1)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.cliente = Cliente.objects.create(
            nome_completo='Ana Souza',
            idade=27,
            email='ana@example.com',
            password='senhaCerta123',
            lgpd=True
        )

    def test_login_sucesso_com_email_e_senha(self):
        response = self.client.post(self.login_url, {
            'email': 'ana@example.com',
            'password': 'senhaCerta123'
        })
        self.assertRedirects(response, reverse('alterar_dados'))
        self.assertEqual(self.client.session.get('cliente_email'), 'ana@example.com')

    def test_login_insensivel_a_maiusculas_email(self):
        response = self.client.post(self.login_url, {
            'email': 'ANA@EXAMPLE.COM',
            'password': 'senhaCerta123'
        })
        self.assertRedirects(response, reverse('alterar_dados'))
        self.assertEqual(self.client.session.get('cliente_email'), 'ana@example.com')

    def test_login_senha_incorreta(self):
        response = self.client.post(self.login_url, {
            'email': 'ana@example.com',
            'password': 'senhaErrada'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('cliente_email', self.client.session)

    def test_login_email_inexistente(self):
        response = self.client.post(self.login_url, {
            'email': 'naoexiste@example.com',
            'password': 'qualquersenha'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('cliente_email', self.client.session)
