from datetime import date
import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.login_cadastro_app.models import Cliente, Parceiro
from apps.pagina_interna.meta_assistant import sugerir_meta
from apps.pagina_interna.models import Habito, Meta


class MetaAssistantUnitTest(TestCase):
    """Testa a lógica determinística isolada em sugerir_meta."""

    def test_rejeita_frequencia_invalida(self):
        with self.assertRaises(ValueError):
            sugerir_meta(frequencia_atual=0, nivel='confortavel', periodo='semana')
        with self.assertRaises(ValueError):
            sugerir_meta(frequencia_atual=-5, nivel='confortavel', periodo='semana')

    def test_rejeita_nivel_invalido(self):
        with self.assertRaises(ValueError):
            sugerir_meta(frequencia_atual=2, nivel='impossivel', periodo='semana')

    def test_rejeita_periodo_invalido(self):
        with self.assertRaises(ValueError):
            sugerir_meta(frequencia_atual=2, nivel='confortavel', periodo='seculox')

    def test_nivel_confortavel_gera_sugestao_esperada(self):
        res = sugerir_meta(frequencia_atual=2, nivel='confortavel', periodo='semana')
        self.assertIn(res['quantidade_sugerida'], (2, 3))
        self.assertEqual(res['periodo'], 'semana')
        self.assertEqual(res['nivel'], 'confortavel')
        self.assertIn('confortável', res['mensagem'])

    def test_nivel_equilibrada_gera_sugestao_moderada(self):
        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertIn(res['quantidade_sugerida'], (3, 4))
        self.assertGreater(res['quantidade_sugerida'], 2)
        self.assertIn('equilibrada', res['mensagem'])

    def test_nivel_desafiadora_gera_sugestao_elevada(self):
        res = sugerir_meta(frequencia_atual=2, nivel='desafiadora', periodo='semana')
        self.assertIn(res['quantidade_sugerida'], (4, 5))
        self.assertGreaterEqual(res['quantidade_sugerida'], 4)
        self.assertIn('desafiadora', res['mensagem'])

    def test_sugestoes_respeitam_limites_de_seguranca_por_periodo(self):
        # Para dia, não deve ultrapassar 24 mesmo se o usuário informar frequência gigante
        res_dia = sugerir_meta(frequencia_atual=50, nivel='desafiadora', periodo='dia')
        self.assertLessEqual(res_dia['quantidade_sugerida'], 24)

        # Para semana, permite hábitos de múltiplas ocorrências diárias (até 70) sem estourar
        res_semana = sugerir_meta(frequencia_atual=100, nivel='desafiadora', periodo='semana')
        self.assertLessEqual(res_semana['quantidade_sugerida'], 70)


class MetaAssistantEndpointTest(TestCase):
    """Testa o endpoint POST /metas/assistente/sugerir/ e suas validações de segurança."""

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome_completo='Cliente Teste Assistente',
            idade=29,
            email='assistente@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.outro_cliente = Cliente.objects.create(
            nome_completo='Outro Cliente',
            idade=31,
            email='outro.assistente@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.parceiro = Parceiro.objects.create(
            nome_completo='Parceiro Teste',
            email='parceiro.assistente@teste.com',
            password='senha123',
        )
        self.habito_positivo = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Academia',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=4,
            frequencia_desejada_periodo='semana',
        )
        self.habito_negativo = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='negativo',
            nome_habito='Fumar',
            frequencia_atual_valor=5,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=0,
            frequencia_desejada_periodo='dia',
        )
        self.habito_com_meta = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Corrida',
            frequencia_atual_valor=1,
            frequencia_atual_periodo='dia',
            frequencia_desejada_valor=1,
            frequencia_desejada_periodo='dia',
        )
        self.meta_existente = Meta.objects.create(
            habito=self.habito_com_meta,
            quantidade_minima=1,
            periodo='dia',
            data_inicio=date.today(),
        )
        self.meta_existente.parceiros.add(self.parceiro)

        self.habito_alheio = Habito.objects.create(
            cliente=self.outro_cliente,
            tipo_habito='positivo',
            nome_habito='Natação Alheia',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=3,
            frequencia_desejada_periodo='semana',
        )

    def test_cliente_autenticado_recebe_sugestao_com_sucesso(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        payload = {
            'habito_id': self.habito_positivo.id,
            'frequencia_atual': 2,
            'periodo': 'semana',
            'nivel': 'equilibrada',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertEqual(data['habito_id'], self.habito_positivo.id)
        self.assertEqual(data['nome_habito'], 'Academia')
        self.assertGreaterEqual(data['quantidade_sugerida'], 3)
        self.assertEqual(data['periodo'], 'semana')
        self.assertIn('mensagem', data)

    def test_usuario_anonimo_rejeitado_com_401(self):
        anonimo = Client()
        payload = {
            'habito_id': self.habito_positivo.id,
            'frequencia_atual': 2,
            'periodo': 'semana',
            'nivel': 'equilibrada',
        }
        res = anonimo.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertFalse(data['sucesso'])

    def test_habito_de_outro_usuario_rejeitado(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        payload = {
            'habito_id': self.habito_alheio.id,
            'frequencia_atual': 2,
            'periodo': 'semana',
            'nivel': 'equilibrada',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertFalse(data['sucesso'])

    def test_habito_negativo_rejeitado(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        payload = {
            'habito_id': self.habito_negativo.id,
            'frequencia_atual': 5,
            'periodo': 'dia',
            'nivel': 'confortavel',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['sucesso'])
        self.assertIn('positivos', data['erro'])

    def test_habito_com_meta_existente_rejeitado(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        payload = {
            'habito_id': self.habito_com_meta.id,
            'frequencia_atual': 1,
            'periodo': 'dia',
            'nivel': 'confortavel',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['sucesso'])
        self.assertIn('já possui uma meta', data['erro'])

    def test_frequencia_atual_zero_ou_negativa_rejeitada(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        for freq in (0, -2):
            with self.subTest(freq=freq):
                payload = {
                    'habito_id': self.habito_positivo.id,
                    'frequencia_atual': freq,
                    'periodo': 'semana',
                    'nivel': 'equilibrada',
                }
                res = self.client.post(
                    reverse('assistente_sugerir_meta'),
                    data=json.dumps(payload),
                    content_type='application/json',
                )
                self.assertEqual(res.status_code, 400)
                data = res.json()
                self.assertFalse(data['sucesso'])

    def test_assistente_nao_cria_meta_no_banco(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        metas_antes = Meta.objects.count()
        payload = {
            'habito_id': self.habito_positivo.id,
            'frequencia_atual': 3,
            'periodo': 'semana',
            'nivel': 'desafiadora',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Meta.objects.count(), metas_antes)

    def test_tela_de_metas_contem_botao_e_dados_iniciais_do_assistente(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.get(reverse('metas'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Me ajude a criar uma meta')
        self.assertContains(res, 'assistente-modal')
        # Verifica que o hábito elegível está com os atributos data-freq
        self.assertContains(res, f'data-freq-valor="{self.habito_positivo.frequencia_atual_valor}"')
        self.assertContains(res, f'data-freq-periodo="{self.habito_positivo.frequencia_atual_periodo}"')

    def test_criacao_normal_compartilhamento_e_parceiro_continuam_intactos(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        # Criação normal via POST do formulário
        res = self.client.post(reverse('metas'), {
            'habito': self.habito_positivo.id,
            'quantidade_minima': 3,
            'periodo': 'semana',
            'parceiros': [self.parceiro.id],
        })
        self.assertRedirects(res, reverse('metas'))
        meta_criada = Meta.objects.get(habito=self.habito_positivo)
        self.assertEqual(meta_criada.quantidade_minima, 3)

        # Compartilhamento público continua funcionando
        token = meta_criada.ativar_compartilhamento()
        anonimo = Client()
        res_publico = anonimo.get(reverse('meta_publica', args=[token]))
        self.assertEqual(res_publico.status_code, 200)
        self.assertContains(res_publico, 'Academia')

        # Parceiro continua funcionando
        self.client.post(reverse('login_parceiro'), {
            'email': self.parceiro.email,
            'password': 'senha123',
        })
        res_parceiro = self.client.get(reverse('metas_partilhadas'))
        self.assertEqual(res_parceiro.status_code, 200)
        self.assertContains(res_parceiro, 'Academia')
