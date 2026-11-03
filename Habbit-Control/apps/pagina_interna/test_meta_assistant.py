from datetime import date
import json
from unittest.mock import MagicMock, patch

import httpx
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.login_cadastro_app.models import Cliente, Parceiro
from apps.pagina_interna.meta_assistant import (
    LIMITES_SEGURANCA,
    MetaAssistantIAError,
    OBJETIVO_TEXTO_MAX_CHARS,
    _validar_plano,
    sanitizar_objetivo_texto,
    sugerir_meta,
    sugerir_meta_com_ia,
    sugerir_meta_deterministica,
)
from apps.pagina_interna.models import Habito, Meta


class MetaAssistantUnitTest(TestCase):
    """Testa a lógica determinística isolada."""

    def test_rejeita_frequencia_invalida(self):
        with self.assertRaises(ValueError):
            sugerir_meta_deterministica(frequencia_atual=0, nivel='confortavel', periodo='semana')
        with self.assertRaises(ValueError):
            sugerir_meta_deterministica(frequencia_atual=-5, nivel='confortavel', periodo='semana')

    def test_rejeita_nivel_invalido(self):
        with self.assertRaises(ValueError):
            sugerir_meta_deterministica(frequencia_atual=2, nivel='impossivel', periodo='semana')

    def test_rejeita_periodo_invalido(self):
        with self.assertRaises(ValueError):
            sugerir_meta_deterministica(frequencia_atual=2, nivel='confortavel', periodo='seculox')

    def test_nivel_confortavel_gera_sugestao_esperada(self):
        res = sugerir_meta_deterministica(frequencia_atual=2, nivel='confortavel', periodo='semana')
        self.assertIn(res['quantidade_sugerida'], (2, 3))
        self.assertEqual(res['periodo'], 'semana')
        self.assertEqual(res['nivel'], 'confortavel')
        self.assertIn('confortável', res['mensagem'])
        self.assertEqual(res['origem'], 'deterministico')

    def test_nivel_equilibrada_gera_sugestao_moderada(self):
        res = sugerir_meta_deterministica(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertIn(res['quantidade_sugerida'], (3, 4))
        self.assertGreater(res['quantidade_sugerida'], 2)
        self.assertIn('equilibrada', res['mensagem'])

    def test_nivel_desafiadora_gera_sugestao_elevada(self):
        res = sugerir_meta_deterministica(frequencia_atual=2, nivel='desafiadora', periodo='semana')
        self.assertIn(res['quantidade_sugerida'], (4, 5))
        self.assertGreaterEqual(res['quantidade_sugerida'], 4)
        self.assertIn('desafiadora', res['mensagem'])

    def test_sugestoes_respeitam_limites_de_seguranca_por_periodo(self):
        res_dia = sugerir_meta_deterministica(frequencia_atual=50, nivel='desafiadora', periodo='dia')
        self.assertLessEqual(res_dia['quantidade_sugerida'], 24)

        res_semana = sugerir_meta_deterministica(frequencia_atual=100, nivel='desafiadora', periodo='semana')
        self.assertLessEqual(res_semana['quantidade_sugerida'], 70)

    @override_settings(OPENAI_API_KEY='')
    def test_sugerir_meta_sem_chave_usa_deterministico(self):
        esperado = sugerir_meta_deterministica(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        obtido = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(obtido['quantidade_sugerida'], esperado['quantidade_sugerida'])
        self.assertEqual(obtido['origem'], 'deterministico')
        self.assertNotIn('plano', obtido)

    def test_fallback_deterministico_nao_exige_plano(self):
        res = sugerir_meta_deterministica(frequencia_atual=2, nivel='confortavel', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')
        self.assertNotIn('plano', res)
        self.assertIn('quantidade_sugerida', res)
        self.assertIn('mensagem', res)


def _plano_valido(**overrides):
    base = {
        'duracao_sugerida_semanas': 6,
        'criterio_sucesso': 'Cumprir pelo menos 80% das sessões planejadas.',
        'etapas': [
            {
                'titulo': 'Adaptação',
                'duracao_semanas': 2,
                'descricao': 'Mantenha 2 sessões obrigatórias e uma terceira opcional.',
            },
            {
                'titulo': 'Consolidação',
                'duracao_semanas': 2,
                'descricao': 'Realize 3 sessões por semana.',
            },
            {
                'titulo': 'Manutenção',
                'duracao_semanas': 2,
                'descricao': 'Mantenha 3 sessões por semana com consistência.',
            },
        ],
        'plano_recuperacao': 'Se não cumprir uma semana, retome a etapa anterior.',
        'dica': 'Priorize consistência antes de aumentar quantidade.',
    }
    base.update(overrides)
    return base


def _resposta_ia_mock(payload: dict) -> MagicMock:
    response = MagicMock()
    response.output_text = json.dumps(payload)
    response.output = []
    return response


class MetaAssistantPlanoValidacaoTest(TestCase):
    """Validação isolada do plano estruturado (falha soft)."""

    def test_plano_valido_e_aceito(self):
        plano = _validar_plano(_plano_valido())
        self.assertIsNotNone(plano)
        self.assertEqual(plano['duracao_sugerida_semanas'], 6)
        self.assertEqual(len(plano['etapas']), 3)
        self.assertIn('criterio_sucesso', plano)

    def test_plano_aceita_entre_1_e_4_etapas(self):
        for n in (1, 2, 3, 4):
            with self.subTest(n=n):
                etapas = [
                    {
                        'titulo': f'Etapa {i}',
                        'duracao_semanas': 1,
                        'descricao': f'Descrição {i}',
                    }
                    for i in range(1, n + 1)
                ]
                plano = _validar_plano(_plano_valido(
                    duracao_sugerida_semanas=n,
                    etapas=etapas,
                ))
                self.assertIsNotNone(plano)
                self.assertEqual(len(plano['etapas']), n)

    def test_plano_rejeita_zero_ou_mais_de_quatro_etapas(self):
        self.assertIsNone(_validar_plano(_plano_valido(etapas=[])))
        etapas_cinco = [
            {'titulo': f'E{i}', 'duracao_semanas': 1, 'descricao': f'D{i}'}
            for i in range(5)
        ]
        self.assertIsNone(_validar_plano(_plano_valido(
            duracao_sugerida_semanas=5,
            etapas=etapas_cinco,
        )))

    def test_pequena_diferenca_entre_soma_e_duracao_total_nao_invalida(self):
        # Soma das etapas = 5; duração sugerida = 6 — diferença pequena ok.
        plano = _validar_plano(_plano_valido(
            duracao_sugerida_semanas=6,
            etapas=[
                {'titulo': 'A', 'duracao_semanas': 2, 'descricao': 'Primeira'},
                {'titulo': 'B', 'duracao_semanas': 3, 'descricao': 'Segunda'},
            ],
        ))
        self.assertIsNotNone(plano)
        self.assertEqual(plano['duracao_sugerida_semanas'], 6)
        self.assertEqual(sum(e['duracao_semanas'] for e in plano['etapas']), 5)

    def test_etapa_invalida_rejeita_apenas_o_plano(self):
        self.assertIsNone(_validar_plano(_plano_valido(
            etapas=[{'titulo': '', 'duracao_semanas': 2, 'descricao': 'x'}],
        )))
        self.assertIsNone(_validar_plano(_plano_valido(
            etapas=[{'titulo': 'A', 'duracao_semanas': 0, 'descricao': 'x'}],
        )))
        self.assertIsNone(_validar_plano(None))
        self.assertIsNone(_validar_plano('nao-e-objeto'))


@override_settings(OPENAI_API_KEY='sk-test-fake-key-not-real', OPENAI_META_ASSISTANT_MODEL='gpt-test-model')
class MetaAssistantIATest(TestCase):
    """Testa integração híbrida com a OpenAI via mocks (sem chamadas reais)."""

    def _payload_valido(self, **overrides):
        base = {
            'quantidade_sugerida': 3,
            'periodo': 'semana',
            'nivel': 'equilibrada',
            'mensagem': 'Uma meta de 3 vezes por semana é um avanço gradual.',
            'justificativa': 'Aumento moderado em relação às 2 vezes atuais.',
        }
        base.update(overrides)
        return base

    def _payload_com_plano(self, **overrides):
        base = self._payload_valido(plano=_plano_valido())
        base.update(overrides)
        return base

    @patch('openai.OpenAI')
    def test_ia_resposta_valida_e_utilizada(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(self._payload_valido())

        res = sugerir_meta(
            frequencia_atual=2,
            nivel='equilibrada',
            periodo='semana',
            nome_habito='Corrida',
            objetivo_texto='Quero voltar a correr sem exagerar.',
        )
        self.assertEqual(res['origem'], 'ia')
        self.assertEqual(res['quantidade_sugerida'], 3)
        self.assertEqual(res['periodo'], 'semana')
        self.assertIn('gradual', res['mensagem'])
        client.responses.create.assert_called_once()

    @override_settings(OPENAI_API_KEY='')
    @patch('openai.OpenAI')
    def test_chave_ausente_aciona_fallback(self, mock_openai_cls):
        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')
        mock_openai_cls.assert_not_called()

    @patch('openai.OpenAI')
    def test_timeout_aciona_fallback(self, mock_openai_cls):
        from openai import APITimeoutError

        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.side_effect = APITimeoutError(
            request=httpx.Request('POST', 'https://api.openai.com/v1/responses'),
        )

        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')
        self.assertGreaterEqual(res['quantidade_sugerida'], 3)

    @patch('openai.OpenAI')
    def test_erro_autenticacao_aciona_fallback(self, mock_openai_cls):
        from openai import AuthenticationError

        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.side_effect = AuthenticationError(
            message='invalid api key',
            response=httpx.Response(
                401,
                request=httpx.Request('POST', 'https://api.openai.com/v1/responses'),
            ),
            body=None,
        )

        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_excecao_generica_aciona_fallback(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.side_effect = RuntimeError('falha inesperada')

        res = sugerir_meta(frequencia_atual=2, nivel='desafiadora', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_resposta_estruturada_invalida_aciona_fallback(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        broken = MagicMock()
        broken.output_text = 'isto não é json'
        broken.output = []
        client.responses.create.return_value = broken

        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_quantidade_zero_ou_negativa_rejeitada(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client

        for qtd in (0, -3):
            with self.subTest(qtd=qtd):
                client.responses.create.return_value = _resposta_ia_mock(
                    self._payload_valido(quantidade_sugerida=qtd)
                )
                res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
                self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_periodo_invalido_rejeitado(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(
            self._payload_valido(periodo='seculo')
        )
        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_quantidade_acima_do_limite_rejeitada(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(
            self._payload_valido(
                quantidade_sugerida=LIMITES_SEGURANCA['semana'] + 10,
                periodo='semana',
            )
        )
        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')
        self.assertLessEqual(res['quantidade_sugerida'], LIMITES_SEGURANCA['semana'])

    @patch('openai.OpenAI')
    def test_dados_pessoais_nao_sao_enviados_a_openai(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(self._payload_valido())

        sugerir_meta_com_ia(
            frequencia_atual=2,
            nivel='equilibrada',
            periodo='semana',
            nome_habito='Corrida',
            objetivo_texto='Quero correr mais.',
        )
        kwargs = client.responses.create.call_args.kwargs
        input_enviado = kwargs.get('input', '')
        instructions = kwargs.get('instructions', '')
        blob = f'{input_enviado}\n{instructions}'.lower()

        for vazado in (
            'cpf',
            'senha',
            'password',
            'email',
            'assistente@teste.com',
            'endereço',
            'endereco',
            'sk-test-fake-key',
        ):
            self.assertNotIn(vazado, blob)

        self.assertIn('corrida', input_enviado.lower())
        self.assertEqual(kwargs.get('store'), False)

    def test_objetivo_texto_limitado_e_sanitizado(self):
        longo = 'a' * (OBJETIVO_TEXTO_MAX_CHARS + 50)
        limpo = sanitizar_objetivo_texto(longo)
        self.assertEqual(len(limpo), OBJETIVO_TEXTO_MAX_CHARS)

        sujo = '  Quero\tler\x00 mais\n\n  '
        self.assertEqual(sanitizar_objetivo_texto(sujo), 'Quero ler mais')
        self.assertEqual(sanitizar_objetivo_texto(None), '')
        self.assertEqual(sanitizar_objetivo_texto(''), '')

    @patch('openai.OpenAI')
    def test_sugerir_meta_com_ia_levanta_quando_schema_invalido(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(
            self._payload_valido(quantidade_sugerida=0)
        )
        with self.assertRaises(MetaAssistantIAError):
            sugerir_meta_com_ia(frequencia_atual=2, nivel='equilibrada', periodo='semana')

    @patch('openai.OpenAI')
    def test_ia_retorna_plano_valido(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(self._payload_com_plano())

        res = sugerir_meta(
            frequencia_atual=2,
            nivel='equilibrada',
            periodo='semana',
            nome_habito='Corrida',
        )
        self.assertEqual(res['origem'], 'ia')
        self.assertEqual(res['quantidade_sugerida'], 3)
        self.assertIn('plano', res)
        self.assertEqual(res['plano']['duracao_sugerida_semanas'], 6)
        self.assertEqual(len(res['plano']['etapas']), 3)
        self.assertTrue(1 <= len(res['plano']['etapas']) <= 4)

    @patch('openai.OpenAI')
    def test_plano_com_etapas_invalidas_nao_quebra_sugestao_principal(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(
            self._payload_com_plano(plano=_plano_valido(etapas=[]))
        )

        res = sugerir_meta(
            frequencia_atual=2,
            nivel='equilibrada',
            periodo='semana',
        )
        self.assertEqual(res['origem'], 'ia')
        self.assertEqual(res['quantidade_sugerida'], 3)
        self.assertEqual(res['periodo'], 'semana')
        self.assertIn('mensagem', res)
        self.assertNotIn('plano', res)

    @patch('openai.OpenAI')
    def test_campos_obrigatorios_da_meta_continuam_validados(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        # Plano válido não salva a sugestão se quantidade for inválida.
        client.responses.create.return_value = _resposta_ia_mock(
            self._payload_com_plano(quantidade_sugerida=0)
        )
        res = sugerir_meta(frequencia_atual=2, nivel='equilibrada', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')
        self.assertNotIn('plano', res)


@override_settings(OPENAI_API_KEY='')
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
        self.assertEqual(data.get('origem'), 'deterministico')

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
            'objetivo_texto': 'Quero evoluir sem exagerar.',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Meta.objects.count(), metas_antes)

    def test_objetivo_texto_nao_e_persistido(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        payload = {
            'habito_id': self.habito_positivo.id,
            'frequencia_atual': 2,
            'periodo': 'semana',
            'nivel': 'equilibrada',
            'objetivo_texto': 'Quero ler mais durante a semana.',
        }
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        # Nenhum campo de Meta/Habito deve guardar o texto livre
        for meta in Meta.objects.all():
            serializado = json.dumps(meta.__dict__, default=str)
            self.assertNotIn('Quero ler mais', serializado)

    def test_tela_de_metas_contem_botao_e_dados_iniciais_do_assistente(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.get(reverse('metas'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Me ajude a criar uma meta')
        self.assertContains(res, 'assistente-modal')
        self.assertContains(res, 'assistant-objetivo')
        self.assertContains(res, 'Usar esta meta')
        self.assertContains(res, 'assistant-plan')
        self.assertContains(res, 'Plano sugerido')
        self.assertContains(res, 'renderizarPlanoSugerido')
        self.assertContains(res, f'data-freq-valor="{self.habito_positivo.frequencia_atual_valor}"')
        self.assertContains(res, f'data-freq-periodo="{self.habito_positivo.frequencia_atual_periodo}"')

    def test_usar_esta_meta_preenche_apenas_campos_existentes(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.get(reverse('metas'))
        self.assertEqual(res.status_code, 200)
        conteudo = res.content.decode('utf-8')
        # Botão continua mapeando só habito / quantidade / periodo
        self.assertIn('aplicarSugestaoNoFormulario', conteudo)
        self.assertIn("getElementById('id_habito')", conteudo)
        self.assertIn("getElementById('id_quantidade_minima')", conteudo)
        self.assertIn("getElementById('id_periodo')", conteudo)
        self.assertIn('sugestaoMetaAtual.quantidade_sugerida', conteudo)
        self.assertIn('sugestaoMetaAtual.periodo', conteudo)
        # Não tenta gravar campos do plano no formulário
        self.assertNotIn("getElementById('id_plano')", conteudo)
        self.assertNotIn('sugestaoMetaAtual.plano', conteudo.split('function aplicarSugestaoNoFormulario')[1].split('function ')[0])

    def test_endpoint_fallback_responde_sem_plano(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps({
                'habito_id': self.habito_positivo.id,
                'frequencia_atual': 2,
                'periodo': 'semana',
                'nivel': 'equilibrada',
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertEqual(data.get('origem'), 'deterministico')
        self.assertNotIn('plano', data)
        self.assertIn('quantidade_sugerida', data)

    def test_criacao_normal_compartilhamento_e_parceiro_continuam_intactos(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.post(reverse('metas'), {
            'habito': self.habito_positivo.id,
            'quantidade_minima': 3,
            'periodo': 'semana',
            'parceiros': [self.parceiro.id],
        })
        self.assertRedirects(res, reverse('metas'))
        meta_criada = Meta.objects.get(habito=self.habito_positivo)
        self.assertEqual(meta_criada.quantidade_minima, 3)

        token = meta_criada.ativar_compartilhamento()
        anonimo = Client()
        res_publico = anonimo.get(reverse('meta_publica', args=[token]))
        self.assertEqual(res_publico.status_code, 200)
        self.assertContains(res_publico, 'Academia')

        self.client.post(reverse('login_parceiro'), {
            'email': self.parceiro.email,
            'password': 'senha123',
        })
        res_parceiro = self.client.get(reverse('metas_partilhadas'))
        self.assertEqual(res_parceiro.status_code, 200)
        self.assertContains(res_parceiro, 'Academia')


@override_settings(OPENAI_API_KEY='sk-test-fake-key-not-real', OPENAI_META_ASSISTANT_MODEL='gpt-test-model')
class MetaAssistantEndpointIATest(TestCase):
    """Endpoint com IA mockada: usa sugestão da API e nunca persiste Meta."""

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome_completo='Cliente IA Endpoint',
            idade=30,
            email='ia.endpoint@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Leitura',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=5,
            frequencia_desejada_periodo='semana',
        )

    @patch('openai.OpenAI')
    def test_endpoint_usa_resposta_ia_valida_sem_criar_meta(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock({
            'quantidade_sugerida': 4,
            'periodo': 'semana',
            'nivel': 'equilibrada',
            'mensagem': 'Leia 4 vezes por semana para evoluir com constância.',
            'justificativa': 'Aumento gradual e sustentável.',
            'plano': _plano_valido(),
        })

        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        metas_antes = Meta.objects.count()
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps({
                'habito_id': self.habito.id,
                'frequencia_atual': 2,
                'periodo': 'semana',
                'nivel': 'equilibrada',
                'objetivo_texto': 'Quero ler mais durante a semana.',
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertEqual(data['origem'], 'ia')
        self.assertEqual(data['quantidade_sugerida'], 4)
        self.assertIn('plano', data)
        self.assertEqual(len(data['plano']['etapas']), 3)
        self.assertEqual(Meta.objects.count(), metas_antes)

        kwargs = client.responses.create.call_args.kwargs
        input_enviado = kwargs.get('input', '')
        self.assertNotIn(self.cliente.email, input_enviado)
        self.assertNotIn('senha123', input_enviado)
        self.assertNotIn(self.cliente.nome_completo, input_enviado)

    @patch('openai.OpenAI')
    def test_plano_nao_e_persistido_no_banco(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock({
            'quantidade_sugerida': 3,
            'periodo': 'semana',
            'nivel': 'equilibrada',
            'mensagem': 'Leia 3 vezes por semana.',
            'justificativa': 'Avanço gradual.',
            'plano': _plano_valido(
                criterio_sucesso='Texto unico do plano XYZ123 nao deve ir ao banco.',
            ),
        })

        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        metas_antes = Meta.objects.count()
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps({
                'habito_id': self.habito.id,
                'frequencia_atual': 2,
                'periodo': 'semana',
                'nivel': 'equilibrada',
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('plano', data)
        self.assertEqual(Meta.objects.count(), metas_antes)
        for meta in Meta.objects.all():
            serializado = json.dumps(meta.__dict__, default=str)
            self.assertNotIn('XYZ123', serializado)
            self.assertNotIn('plano_recuperacao', serializado)
