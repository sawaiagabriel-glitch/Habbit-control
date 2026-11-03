from datetime import date

from django.test import Client, TestCase
from django.urls import reverse

from apps.login_cadastro_app.models import Cliente, Parceiro
from apps.pagina_interna.models import Habito, Meta, RegistroAtividade


class MetaCompartilhamentoPublicoTest(TestCase):
    """Testa a geração de link público, controle de acesso e visualização anônima de Metas."""

    def setUp(self):
        self.dono = Cliente.objects.create(
            nome_completo='Cliente Proprietario',
            idade=25,
            email='dono@teste.com',
            password='senha123',
            cidade='Campinas',
            estado='SP',
            lgpd=True,
        )
        self.outro_cliente = Cliente.objects.create(
            nome_completo='Outro Cliente',
            idade=35,
            email='outro@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.parceiro = Parceiro.objects.create(
            nome_completo='Parceiro Teste',
            email='parceiro.meta@teste.com',
            password='senha123',
        )
        self.habito = Habito.objects.create(
            cliente=self.dono,
            tipo_habito='positivo',
            nome_habito='Academia e Corrida',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=4,
            frequencia_desejada_periodo='semana',
        )
        self.outro_habito = Habito.objects.create(
            cliente=self.dono,
            tipo_habito='positivo',
            nome_habito='Habito Privado Dono',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=1,
            frequencia_desejada_periodo='dia',
        )
        self.meta = Meta.objects.create(
            habito=self.habito,
            quantidade_minima=4,
            periodo='semana',
            data_inicio=date.today(),
        )
        self.meta.parceiros.add(self.parceiro)

    def test_dono_consegue_ativar_e_desativar_compartilhamento(self):
        self.client.post(reverse('login'), {
            'email': self.dono.email,
            'password': 'senha123',
        })
        response_ativar = self.client.post(reverse('ativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(response_ativar, reverse('metas'))
        self.meta.refresh_from_db()
        self.assertTrue(self.meta.compartilhamento_ativo)
        self.assertIsNotNone(self.meta.token_publico)
        self.assertGreater(len(self.meta.token_publico), 20)
        token_inicial = self.meta.token_publico

        response_desativar = self.client.post(reverse('desativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(response_desativar, reverse('metas'))
        self.meta.refresh_from_db()
        self.assertFalse(self.meta.compartilhamento_ativo)
        self.assertEqual(self.meta.token_publico, token_inicial)

        response_reativar = self.client.post(reverse('ativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(response_reativar, reverse('metas'))
        self.meta.refresh_from_db()
        self.assertTrue(self.meta.compartilhamento_ativo)
        self.assertEqual(self.meta.token_publico, token_inicial)

    def test_usuario_diferente_nao_consegue_ativar_ou_desativar_meta(self):
        self.client.post(reverse('login'), {
            'email': self.outro_cliente.email,
            'password': 'senha123',
        })
        response = self.client.post(reverse('ativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(response, reverse('metas'))
        self.meta.refresh_from_db()
        self.assertFalse(self.meta.compartilhamento_ativo)
        self.assertIsNone(self.meta.token_publico)

        self.meta.ativar_compartilhamento()
        self.assertTrue(self.meta.compartilhamento_ativo)

        response = self.client.post(reverse('desativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(response, reverse('metas'))
        self.meta.refresh_from_db()
        self.assertTrue(self.meta.compartilhamento_ativo)

    def test_usuario_anonimo_redirecionado_ao_tentar_ativar_ou_desativar(self):
        anonimo = Client()
        res_ativar = anonimo.post(reverse('ativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(res_ativar, reverse('login'))

        self.meta.ativar_compartilhamento()
        res_desativar = anonimo.post(reverse('desativar_compartilhamento_meta', args=[self.meta.id]))
        self.assertRedirects(res_desativar, reverse('login'))
        self.meta.refresh_from_db()
        self.assertTrue(self.meta.compartilhamento_ativo)

    def test_pagina_publica_funciona_sem_login(self):
        token = self.meta.ativar_compartilhamento()
        anonimo = Client()
        url_publica = reverse('meta_publica', args=[token])
        response = anonimo.get(url_publica)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Academia e Corrida')
        self.assertContains(response, 'Objetivo:')
        self.assertContains(response, '4 atividades por semana')
        self.assertContains(response, 'Meta criada no')
        self.assertContains(response, 'Habbit-Control')

    def test_token_invalido_retorna_404(self):
        anonimo = Client()
        response = anonimo.get(reverse('meta_publica', args=['token-inexistente-12345']))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Meta indisponível', status_code=404)

    def test_link_desativado_deixa_de_funcionar_e_retorna_404(self):
        token = self.meta.ativar_compartilhamento()
        self.meta.desativar_compartilhamento()
        anonimo = Client()
        response = anonimo.get(reverse('meta_publica', args=[token]))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Meta indisponível', status_code=404)

    def test_dados_pessoais_do_cliente_nao_aparecem_na_resposta_publica(self):
        token = self.meta.ativar_compartilhamento()
        anonimo = Client()
        response = anonimo.get(reverse('meta_publica', args=[token]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.dono.nome_completo)
        self.assertNotContains(response, self.dono.email)
        self.assertNotContains(response, 'Campinas')
        self.assertNotContains(response, 'senha123')
        self.assertNotContains(response, 'Habito Privado Dono')

    def test_progresso_exibido_usa_calculo_real_sem_efeitos_colaterais_de_escrita(self):
        self.meta.ativar_compartilhamento()
        RegistroAtividade.objects.create(
            habito=self.habito,
            data=date.today(),
            quantidade=3,
        )
        anonimo = Client()
        response = anonimo.get(reverse('meta_publica', args=[self.meta.token_publico]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '3 / 4')
        conteudo = response.content.decode('utf-8')
        self.assertTrue('75,0%' in conteudo or '75.0%' in conteudo or '75%' in conteudo)

    def test_funcionalidades_de_parceiro_continuam_funcionando(self):
        self.meta.ativar_compartilhamento()
        self.client.post(reverse('login_parceiro'), {
            'email': self.parceiro.email,
            'password': 'senha123',
        })
        response = self.client.get(reverse('metas_partilhadas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Academia e Corrida')
        self.assertContains(response, self.dono.nome_completo)
