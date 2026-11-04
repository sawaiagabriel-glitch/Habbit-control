from datetime import date
import json
from unittest.mock import MagicMock, patch

import httpx
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.login_cadastro_app.models import Cliente, Parceiro
from apps.pagina_interna.meta_assistant import (
    HISTORICO_MAX_MENSAGENS,
    LIMITES_SEGURANCA,
    MAX_PERGUNTAS_ACOMPANHAMENTO,
    MENSAGEM_MAX_CHARS,
    MetaAssistantIAError,
    OBJETIVO_TEXTO_MAX_CHARS,
    _validar_plano,
    contar_perguntas_assistente,
    conversar_meta_assistente,
    sanitizar_historico,
    sanitizar_mensagem,
    sanitizar_objetivo_texto,
    sugerir_meta,
    sugerir_meta_com_ia,
    sugerir_meta_deterministica,
    validar_payload_criacao_meta_assistente,
)
from apps.pagina_interna.models import Habito, Meta, MetaCiclo, PlanoMetaAssistente
from apps.pagina_interna.services import obter_resumo_meta


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
        self.assertEqual(obtido['estado'], 'meta_pronta')
        self.assertNotIn('etapas', obtido.get('meta') or {})

    def test_fallback_deterministico_nao_exige_plano(self):
        res = sugerir_meta_deterministica(frequencia_atual=2, nivel='confortavel', periodo='semana')
        self.assertEqual(res['origem'], 'deterministico')
        self.assertNotIn('plano', res)
        self.assertIn('quantidade_sugerida', res)
        self.assertIn('mensagem', res)


def _plano_valido(**overrides):
    base = {
        'duracao_semanas': 8,
        'criterio_sucesso': 'Cumprir pelo menos 80% das sessões planejadas.',
        'etapas': [
            {
                'titulo': 'Adaptação',
                'inicio_semana': 1,
                'fim_semana': 2,
                'descricao': 'Realizar 2 treinos leves e 1 treino mais longo por semana.',
            },
            {
                'titulo': 'Progressão',
                'inicio_semana': 3,
                'fim_semana': 5,
                'descricao': 'Manter 3 treinos semanais e aumentar gradualmente a distância.',
            },
            {
                'titulo': 'Consolidação',
                'inicio_semana': 6,
                'fim_semana': 8,
                'descricao': 'Aproximar progressivamente o treino longo do objetivo.',
            },
        ],
        'plano_recuperacao': 'Se não cumprir uma semana, repita a última etapa antes de avançar.',
    }
    base.update(overrides)
    return base


def _meta_pronta_valida(**overrides):
    base = {
        'titulo_meta': 'Correr 10 km continuamente',
        'objetivo_principal': 'Completar uma corrida contínua de 10 km',
        'quantidade_sugerida': 3,
        'periodo': 'semana',
        'nivel': 'equilibrada',
        'mensagem': 'Vamos construir sua capacidade para correr 10 km progressivamente.',
        'justificativa': 'Você já corre 4 km e treina 3 vezes por semana.',
    }
    base.update(_plano_valido())
    base.update(overrides)
    return base


def _resposta_coletando(mensagem='Qual é a maior distância que você corre hoje?'):
    return {
        'estado': 'coletando_contexto',
        'mensagem': mensagem,
        'meta': None,
    }


def _resposta_meta_pronta(**overrides):
    meta = _meta_pronta_valida(**overrides)
    return {
        'estado': 'meta_pronta',
        'mensagem': meta['mensagem'],
        'meta': meta,
    }


def _resposta_ia_mock(payload: dict) -> MagicMock:
    response = MagicMock()
    response.output_text = json.dumps(payload)
    response.output = []
    return response


class MetaAssistantPlanoValidacaoTest(TestCase):
    """Validação isolada do plano flat (falha soft)."""

    def test_plano_valido_e_aceito(self):
        plano = _validar_plano(_plano_valido())
        self.assertIsNotNone(plano)
        self.assertEqual(plano['duracao_semanas'], 8)
        self.assertEqual(len(plano['etapas']), 3)

    def test_plano_aceita_entre_1_e_4_etapas(self):
        for n in (1, 2, 3, 4):
            with self.subTest(n=n):
                etapas = [
                    {
                        'titulo': f'Etapa {i}',
                        'inicio_semana': i,
                        'fim_semana': i,
                        'descricao': f'Descrição {i}',
                    }
                    for i in range(1, n + 1)
                ]
                plano = _validar_plano(_plano_valido(duracao_semanas=n, etapas=etapas))
                self.assertIsNotNone(plano)
                self.assertEqual(len(plano['etapas']), n)

    def test_plano_rejeita_zero_ou_mais_de_quatro_etapas(self):
        self.assertIsNone(_validar_plano(_plano_valido(etapas=[])))
        etapas_cinco = [
            {
                'titulo': f'E{i}',
                'inicio_semana': i,
                'fim_semana': i,
                'descricao': f'D{i}',
            }
            for i in range(1, 6)
        ]
        self.assertIsNone(_validar_plano(_plano_valido(duracao_semanas=5, etapas=etapas_cinco)))

    def test_prazo_valido_aceito_com_etapas_nao_contiguas(self):
        plano = _validar_plano(_plano_valido(
            duracao_semanas=8,
            etapas=[
                {'titulo': 'A', 'inicio_semana': 1, 'fim_semana': 2, 'descricao': 'Primeira'},
                {'titulo': 'B', 'inicio_semana': 5, 'fim_semana': 7, 'descricao': 'Segunda'},
            ],
        ))
        self.assertIsNotNone(plano)

    def test_etapa_invalida_rejeita_apenas_o_plano(self):
        self.assertIsNone(_validar_plano(_plano_valido(
            etapas=[{'titulo': '', 'inicio_semana': 1, 'fim_semana': 2, 'descricao': 'x'}],
        )))
        self.assertIsNone(_validar_plano(None))


class MetaAssistantHistoricoTest(TestCase):
    """Sanitização e limites do histórico/mensagem."""

    def test_mensagem_limitada_e_sanitizada(self):
        longo = 'a' * (MENSAGEM_MAX_CHARS + 50)
        self.assertEqual(len(sanitizar_mensagem(longo)), MENSAGEM_MAX_CHARS)
        self.assertEqual(sanitizar_mensagem('  Olá\x00 mundo\n\n  '), 'Olá mundo')
        self.assertEqual(sanitizar_objetivo_texto('x' * (OBJETIVO_TEXTO_MAX_CHARS + 10)), 'x' * OBJETIVO_TEXTO_MAX_CHARS)

    def test_historico_e_limitado_e_sanitizado(self):
        bruto = [
            {'role': 'user', 'content': 'Quero correr', 'extra': 'ignorar'},
            {'role': 'system', 'content': 'não deve passar'},
            {'role': 'assistant', 'content': 'Qual distância?'},
            'nao-e-objeto',
            {'role': 'user', 'content': ''},
            {'role': 'USER', 'content': '  4 km  '},
        ]
        limpo = sanitizar_historico(bruto)
        self.assertEqual(len(limpo), 3)
        self.assertEqual(limpo[0], {'role': 'user', 'content': 'Quero correr'})
        self.assertEqual(limpo[1]['role'], 'assistant')
        self.assertEqual(limpo[2], {'role': 'user', 'content': '4 km'})
        self.assertNotIn('extra', limpo[0])

    def test_historico_respeita_maximo_de_mensagens(self):
        bruto = [
            {'role': 'user' if i % 2 == 0 else 'assistant', 'content': f'msg {i}'}
            for i in range(HISTORICO_MAX_MENSAGENS + 5)
        ]
        limpo = sanitizar_historico(bruto)
        self.assertEqual(len(limpo), HISTORICO_MAX_MENSAGENS)

    def test_contar_perguntas_assistente(self):
        historico = [
            {'role': 'user', 'content': 'Quero correr 10 km'},
            {'role': 'assistant', 'content': 'Qual distância atual?'},
            {'role': 'user', 'content': '4 km'},
            {'role': 'assistant', 'content': 'Quantas vezes por semana?'},
        ]
        self.assertEqual(contar_perguntas_assistente(historico), 2)


@override_settings(OPENAI_API_KEY='sk-test-fake-key-not-real', OPENAI_META_ASSISTANT_MODEL='gpt-test-model')
class MetaAssistantIATest(TestCase):
    """Integração híbrida conversacional com mocks."""

    @patch('openai.OpenAI')
    def test_objetivo_insuficiente_retorna_coletando_contexto(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_coletando())

        res = conversar_meta_assistente(
            mensagem='Quero correr 10 km',
            historico=[],
            nome_habito='Corrida',
            frequencia_atual=2,
            periodo_habito='semana',
        )
        self.assertEqual(res['estado'], 'coletando_contexto')
        self.assertIsNone(res['meta'])
        self.assertIn('distância', res['mensagem'].lower())
        self.assertEqual(res['origem'], 'ia')

    @patch('openai.OpenAI')
    def test_ia_faz_pergunta_de_acompanhamento(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        pergunta = 'Quantas vezes por semana você consegue treinar?'
        client.responses.create.return_value = _resposta_ia_mock(_resposta_coletando(pergunta))

        res = sugerir_meta_com_ia(
            frequencia_atual=2,
            nivel='equilibrada',
            periodo='semana',
            mensagem='Quero correr 10 km',
        )
        self.assertEqual(res['estado'], 'coletando_contexto')
        self.assertEqual(res['mensagem'], pergunta)
        self.assertIsNone(res['meta'])

    @patch('openai.OpenAI')
    def test_historico_e_enviado_a_openai(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_coletando('Ok, e o prazo?'))

        historico = [
            {'role': 'user', 'content': 'Quero correr 10 km'},
            {'role': 'assistant', 'content': 'Qual distância atual?'},
        ]
        conversar_meta_assistente(
            mensagem='4 km',
            historico=historico,
            nome_habito='Corrida',
        )
        kwargs = client.responses.create.call_args.kwargs
        input_enviado = kwargs.get('input')
        self.assertIsInstance(input_enviado, list)
        self.assertEqual(input_enviado[0]['content'], 'Quero correr 10 km')
        self.assertEqual(input_enviado[1]['role'], 'assistant')
        self.assertEqual(input_enviado[-1], {'role': 'user', 'content': '4 km'})
        self.assertEqual(kwargs.get('store'), False)
        schema = kwargs['text']['format']['schema']
        self.assertIn('estado', schema['properties'])
        self.assertIn('coletando_contexto', schema['properties']['estado']['enum'])

    @patch('openai.OpenAI')
    def test_ia_pode_fazer_mais_de_uma_pergunta(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(
            _resposta_coletando('Você tem prazo específico?')
        )
        historico = [
            {'role': 'user', 'content': 'Quero correr 10 km'},
            {'role': 'assistant', 'content': 'Qual distância atual?'},
            {'role': 'user', 'content': '4 km'},
            {'role': 'assistant', 'content': 'Quantas vezes por semana?'},
        ]
        res = conversar_meta_assistente(mensagem='3 vezes', historico=historico)
        self.assertEqual(res['estado'], 'coletando_contexto')
        self.assertIn('prazo', res['mensagem'].lower())

    @patch('openai.OpenAI')
    def test_contexto_suficiente_retorna_meta_pronta(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta())

        historico = [
            {'role': 'user', 'content': 'Quero correr 10 km'},
            {'role': 'assistant', 'content': 'Qual distância atual?'},
            {'role': 'user', 'content': '4 km'},
            {'role': 'assistant', 'content': 'Quantas vezes por semana?'},
            {'role': 'user', 'content': '3'},
            {'role': 'assistant', 'content': 'Tem prazo?'},
        ]
        res = conversar_meta_assistente(mensagem='Em dois meses', historico=historico)
        self.assertEqual(res['estado'], 'meta_pronta')
        self.assertIsNotNone(res['meta'])
        self.assertEqual(res['meta']['quantidade_sugerida'], 3)
        self.assertEqual(res['quantidade_sugerida'], 3)
        self.assertEqual(len(res['etapas']), 3)

    @patch('openai.OpenAI')
    def test_resposta_final_usa_schema_completo(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta())
        res = conversar_meta_assistente(mensagem='Quero correr 10 km em 8 semanas com 3 treinos')
        meta = res['meta']
        for campo in (
            'titulo_meta', 'objetivo_principal', 'quantidade_sugerida', 'periodo',
            'duracao_semanas', 'nivel', 'mensagem', 'justificativa',
            'criterio_sucesso', 'plano_recuperacao', 'etapas',
        ):
            self.assertIn(campo, meta)

    @patch('openai.OpenAI')
    def test_plano_invalido_soft_fail_preserva_meta_principal(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        payload = _resposta_meta_pronta(etapas=[])
        client.responses.create.return_value = _resposta_ia_mock(payload)
        res = conversar_meta_assistente(mensagem='Quero correr 10 km')
        self.assertEqual(res['estado'], 'meta_pronta')
        self.assertEqual(res['titulo_meta'], 'Correr 10 km continuamente')
        self.assertNotIn('etapas', res['meta'])

    @patch('openai.OpenAI')
    def test_meta_principal_invalida_aciona_fallback(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        payload = _resposta_meta_pronta(quantidade_sugerida=0)
        client.responses.create.return_value = _resposta_ia_mock(payload)
        res = conversar_meta_assistente(
            mensagem='Quero correr',
            frequencia_atual=2,
            periodo_habito='semana',
            nivel_fallback='equilibrada',
        )
        self.assertEqual(res['origem'], 'deterministico')
        self.assertEqual(res['estado'], 'meta_pronta')

    @override_settings(OPENAI_API_KEY='')
    @patch('openai.OpenAI')
    def test_chave_ausente_aciona_fallback(self, mock_openai_cls):
        res = conversar_meta_assistente(mensagem='Quero correr 10 km', frequencia_atual=2)
        self.assertEqual(res['origem'], 'deterministico')
        self.assertEqual(res['estado'], 'meta_pronta')
        mock_openai_cls.assert_not_called()

    @patch('openai.OpenAI')
    def test_timeout_aciona_fallback(self, mock_openai_cls):
        from openai import APITimeoutError
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.side_effect = APITimeoutError(
            request=httpx.Request('POST', 'https://api.openai.com/v1/responses'),
        )
        res = conversar_meta_assistente(mensagem='Quero correr', frequencia_atual=2)
        self.assertEqual(res['origem'], 'deterministico')
        self.assertEqual(res['estado'], 'meta_pronta')
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
        res = conversar_meta_assistente(mensagem='Quero ler mais', frequencia_atual=2)
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_excecao_generica_aciona_fallback(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.side_effect = RuntimeError('falha inesperada')
        res = conversar_meta_assistente(mensagem='Quero estudar', frequencia_atual=2)
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_resposta_estruturada_invalida_aciona_fallback(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        broken = MagicMock()
        broken.output_text = 'isto não é json'
        broken.output = []
        client.responses.create.return_value = broken
        res = conversar_meta_assistente(mensagem='Quero correr', frequencia_atual=2)
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_quantidade_acima_do_limite_rejeitada(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta(
            quantidade_sugerida=LIMITES_SEGURANCA['semana'] + 10,
        ))
        res = conversar_meta_assistente(mensagem='Quero exagerar', frequencia_atual=2)
        self.assertEqual(res['origem'], 'deterministico')
        self.assertLessEqual(res['quantidade_sugerida'], LIMITES_SEGURANCA['semana'])

    @patch('openai.OpenAI')
    def test_limite_de_perguntas_forca_meta_pronta_ou_fallback(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        # IA tenta perguntar além do limite → validação falha → fallback
        client.responses.create.return_value = _resposta_ia_mock(_resposta_coletando('Mais uma?'))
        historico = []
        for i in range(MAX_PERGUNTAS_ACOMPANHAMENTO):
            historico.append({'role': 'user', 'content': f'resposta {i}'})
            historico.append({'role': 'assistant', 'content': f'pergunta {i}'})
        res = conversar_meta_assistente(mensagem='ok', historico=historico, frequencia_atual=2)
        self.assertEqual(res['estado'], 'meta_pronta')
        self.assertEqual(res['origem'], 'deterministico')

    @patch('openai.OpenAI')
    def test_dados_pessoais_nao_sao_enviados_a_openai(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_coletando())
        conversar_meta_assistente(
            mensagem='Quero correr mais.',
            nome_habito='Corrida',
        )
        kwargs = client.responses.create.call_args.kwargs
        blob = f"{kwargs.get('input')}\n{kwargs.get('instructions')}".lower()
        for vazado in (
            'cpf', 'senha', 'password', 'email', 'assistente@teste.com',
            'endereço', 'endereco', 'sk-test-fake-key',
        ):
            self.assertNotIn(vazado, blob)

    @patch('openai.OpenAI')
    def test_sugerir_meta_com_ia_levanta_quando_schema_invalido(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta(
            quantidade_sugerida=0,
        ))
        with self.assertRaises(MetaAssistantIAError):
            sugerir_meta_com_ia(
                frequencia_atual=2,
                nivel='equilibrada',
                periodo='semana',
                mensagem='Quero correr',
            )

    @patch('openai.OpenAI')
    def test_meta_pronta_nao_cria_meta(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta())
        metas_antes = Meta.objects.count()
        res = conversar_meta_assistente(mensagem='Quero correr 10 km')
        self.assertEqual(res['estado'], 'meta_pronta')
        self.assertEqual(Meta.objects.count(), metas_antes)


@override_settings(OPENAI_API_KEY='')
class MetaAssistantEndpointTest(TestCase):
    """Endpoint conversacional: autenticação, titularidade e fallback."""

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

    def _post_assistente(self, payload, client=None):
        c = client or self.client
        return c.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_cliente_autenticado_recebe_sugestao_com_sucesso(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_positivo.id,
            'mensagem': 'Quero treinar com mais constância.',
            'historico': [],
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertEqual(data['habito_id'], self.habito_positivo.id)
        self.assertEqual(data['estado'], 'meta_pronta')
        self.assertEqual(data.get('origem'), 'deterministico')
        self.assertGreaterEqual(data['quantidade_sugerida'], 3)
        self.assertEqual(data['periodo'], 'semana')

    def test_usuario_anonimo_rejeitado_com_401(self):
        res = self._post_assistente({
            'habito_id': self.habito_positivo.id,
            'mensagem': 'Quero correr',
        }, client=Client())
        self.assertEqual(res.status_code, 401)

    def test_habito_de_outro_usuario_rejeitado(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_alheio.id,
            'mensagem': 'Quero nadar mais',
        })
        self.assertEqual(res.status_code, 404)

    def test_habito_negativo_rejeitado(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_negativo.id,
            'mensagem': 'Quero parar',
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('positivos', res.json()['erro'])

    def test_habito_com_meta_existente_rejeitado(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_com_meta.id,
            'mensagem': 'Quero evoluir',
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('já possui uma meta', res.json()['erro'])

    def test_mensagem_vazia_rejeitada(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_positivo.id,
            'mensagem': '   ',
        })
        self.assertEqual(res.status_code, 400)

    def test_assistente_nao_cria_meta_no_banco(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        metas_antes = Meta.objects.count()
        res = self._post_assistente({
            'habito_id': self.habito_positivo.id,
            'mensagem': 'Quero evoluir sem exagerar.',
            'historico': [],
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Meta.objects.count(), metas_antes)

    def test_objetivo_texto_nao_e_persistido(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_positivo.id,
            'mensagem': 'Quero ler mais durante a semana.',
        })
        self.assertEqual(res.status_code, 200)
        for meta in Meta.objects.all():
            serializado = json.dumps(meta.__dict__, default=str)
            self.assertNotIn('Quero ler mais', serializado)

    def test_tela_de_metas_contem_chat_do_assistente(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.get(reverse('metas'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Me ajude a criar uma meta')
        self.assertContains(res, 'assistente-modal')
        self.assertContains(res, 'assistant-chat-log')
        self.assertContains(res, 'assistant-chat-input')
        self.assertContains(res, 'O que você quer alcançar com esse hábito?')
        self.assertContains(res, 'Usar e criar esta meta')
        self.assertContains(res, 'Começar novamente')
        self.assertContains(res, 'enviarMensagemAssistente')
        self.assertContains(res, 'historicoAssistente')
        self.assertContains(res, 'usarECriarMetaAssistente')
        self.assertContains(res, f'data-freq-valor="{self.habito_positivo.frequencia_atual_valor}"')

    def test_usar_e_criar_meta_chama_endpoint_de_criacao(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self.client.get(reverse('metas'))
        conteudo = res.content.decode('utf-8')
        self.assertIn('usarECriarMetaAssistente', conteudo)
        self.assertIn('assistente/criar', conteudo)
        self.assertNotIn('aplicarSugestaoNoFormulario', conteudo)

    def test_endpoint_fallback_responde_meta_pronta_sem_etapas(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })
        res = self._post_assistente({
            'habito_id': self.habito_positivo.id,
            'mensagem': 'Quero melhorar',
        })
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertEqual(data['estado'], 'meta_pronta')
        self.assertEqual(data['origem'], 'deterministico')
        self.assertNotIn('etapas', data)
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
    """Endpoint com IA mockada no fluxo conversacional."""

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

    def _login(self):
        self.client.post(reverse('login'), {
            'email': self.cliente.email,
            'password': 'senha123',
        })

    @patch('openai.OpenAI')
    def test_endpoint_retorna_coletando_contexto(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(
            _resposta_coletando('Quantos livros você lê por ano hoje?')
        )
        self._login()
        metas_antes = Meta.objects.count()
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps({
                'habito_id': self.habito.id,
                'mensagem': 'Quero ler mais',
                'historico': [],
            }),
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['estado'], 'coletando_contexto')
        self.assertIsNone(data['meta'])
        self.assertIn('livros', data['mensagem'].lower())
        self.assertEqual(Meta.objects.count(), metas_antes)

    @patch('openai.OpenAI')
    def test_endpoint_usa_meta_pronta_sem_criar_meta(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta(
            titulo_meta='Ler 12 livros no ano',
            quantidade_sugerida=1,
        ))
        self._login()
        metas_antes = Meta.objects.count()
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps({
                'habito_id': self.habito.id,
                'mensagem': 'Em dois meses',
                'historico': [
                    {'role': 'user', 'content': 'Quero ler 12 livros'},
                    {'role': 'assistant', 'content': 'Qual seu ritmo atual?'},
                    {'role': 'user', 'content': '4 por ano'},
                    {'role': 'assistant', 'content': 'Tem prazo?'},
                ],
            }),
            content_type='application/json',
        )
        data = res.json()
        self.assertEqual(data['estado'], 'meta_pronta')
        self.assertEqual(data['titulo_meta'], 'Ler 12 livros no ano')
        self.assertEqual(data['quantidade_sugerida'], 1)
        self.assertIn('etapas', data)
        self.assertEqual(Meta.objects.count(), metas_antes)

        kwargs = client.responses.create.call_args.kwargs
        input_enviado = kwargs.get('input')
        self.assertTrue(any('Quero ler 12 livros' in str(m.get('content', '')) for m in input_enviado))
        blob = json.dumps(input_enviado)
        self.assertNotIn(self.cliente.email, blob)
        self.assertNotIn('senha123', blob)
        self.assertNotIn(self.cliente.nome_completo, blob)

    @patch('openai.OpenAI')
    def test_plano_nao_e_persistido_no_banco(self, mock_openai_cls):
        client = MagicMock()
        mock_openai_cls.return_value = client
        client.responses.create.return_value = _resposta_ia_mock(_resposta_meta_pronta(
            criterio_sucesso='Texto unico do plano XYZ123 nao deve ir ao banco.',
        ))
        self._login()
        metas_antes = Meta.objects.count()
        res = self.client.post(
            reverse('assistente_sugerir_meta'),
            data=json.dumps({
                'habito_id': self.habito.id,
                'mensagem': 'Quero ler 12 livros no ano',
            }),
            content_type='application/json',
        )
        data = res.json()
        self.assertEqual(data['estado'], 'meta_pronta')
        self.assertEqual(Meta.objects.count(), metas_antes)
        self.assertEqual(PlanoMetaAssistente.objects.count(), 0)
        for meta in Meta.objects.all():
            serializado = json.dumps(meta.__dict__, default=str)
            self.assertNotIn('XYZ123', serializado)
            self.assertNotIn('plano_recuperacao', serializado)


class ValidacaoPayloadCriacaoMetaTest(TestCase):
    def test_payload_sem_plano_rico_cria_apenas_campos_operacionais(self):
        resultado = validar_payload_criacao_meta_assistente({
            'quantidade_sugerida': 3,
            'periodo': 'semana',
        })
        self.assertEqual(resultado['quantidade_minima'], 3)
        self.assertEqual(resultado['periodo'], 'semana')
        self.assertIsNone(resultado['plano'])

    def test_payload_com_plano_completo_normaliza_plano(self):
        resultado = validar_payload_criacao_meta_assistente(_meta_pronta_valida())
        self.assertIsNotNone(resultado['plano'])
        self.assertEqual(resultado['plano']['titulo_meta'], 'Correr 10 km continuamente')
        self.assertEqual(len(resultado['plano']['etapas']), 3)

    def test_payload_com_plano_incompleto_rejeita(self):
        with self.assertRaises(ValueError):
            validar_payload_criacao_meta_assistente({
                'quantidade_sugerida': 3,
                'periodo': 'semana',
                'titulo_meta': 'Só título',
            })


@override_settings(OPENAI_API_KEY='')
class AssistenteCriarMetaEndpointTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(
            nome_completo='Cliente Criar Meta',
            idade=28,
            email='criar.meta@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.outro = Cliente.objects.create(
            nome_completo='Outro Criar Meta',
            idade=33,
            email='outro.criar@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Corrida',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=4,
            frequencia_desejada_periodo='semana',
        )
        self.habito_outro = Habito.objects.create(
            cliente=self.outro,
            tipo_habito='positivo',
            nome_habito='Natação',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=3,
            frequencia_desejada_periodo='semana',
        )

    def _login(self, cliente=None):
        cliente = cliente or self.cliente
        self.client.post(reverse('login'), {
            'email': cliente.email,
            'password': 'senha123',
        })

    def _post_criar(self, payload):
        return self.client.post(
            reverse('assistente_criar_meta'),
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_cria_meta_manual_sem_plano_quando_payload_simples(self):
        self._login()
        res = self._post_criar({
            'habito_id': self.habito.id,
            'quantidade_minima': 3,
            'periodo': 'semana',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertFalse(data['tem_plano'])
        meta = Meta.objects.get(pk=data['meta_id'])
        self.assertEqual(meta.quantidade_minima, 3)
        self.assertFalse(PlanoMetaAssistente.objects.filter(meta=meta).exists())

    def test_cria_meta_com_plano_assistente_em_transacao(self):
        self._login()
        payload = {
            'habito_id': self.habito.id,
            **_meta_pronta_valida(),
        }
        res = self._post_criar(payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['sucesso'])
        self.assertTrue(data['tem_plano'])
        meta = Meta.objects.get(pk=data['meta_id'])
        plano = PlanoMetaAssistente.objects.get(meta=meta)
        self.assertEqual(plano.titulo_meta, 'Correr 10 km continuamente')
        self.assertEqual(plano.objetivo_principal, 'Completar uma corrida contínua de 10 km')
        self.assertEqual(plano.duracao_semanas, 8)
        self.assertEqual(len(plano.etapas), 3)
        self.assertEqual(data['redirect_url'], f'/metas/#meta-{meta.id}')

    def test_excluir_meta_remove_plano_por_cascade(self):
        self._login()
        res = self._post_criar({
            'habito_id': self.habito.id,
            **_meta_pronta_valida(),
        })
        meta_id = res.json()['meta_id']
        self.assertEqual(PlanoMetaAssistente.objects.filter(meta_id=meta_id).count(), 1)
        Meta.objects.get(pk=meta_id).delete()
        self.assertEqual(PlanoMetaAssistente.objects.filter(meta_id=meta_id).count(), 0)

    def test_nao_cria_meta_de_outro_cliente(self):
        self._login()
        res = self._post_criar({
            'habito_id': self.habito_outro.id,
            'quantidade_minima': 2,
            'periodo': 'semana',
        })
        self.assertEqual(res.status_code, 404)
        self.assertEqual(Meta.objects.filter(habito=self.habito_outro).count(), 0)

    @patch('apps.pagina_interna.meta_views.conversar_meta_assistente')
    def test_endpoint_criar_nao_chama_openai(self, mock_conversar):
        self._login()
        res = self._post_criar({
            'habito_id': self.habito.id,
            **_meta_pronta_valida(),
        })
        self.assertEqual(res.status_code, 200)
        mock_conversar.assert_not_called()

    def test_pagina_metas_exibe_plano_completo_e_ancora(self):
        self._login()
        criar = self._post_criar({
            'habito_id': self.habito.id,
            **_meta_pronta_valida(),
        })
        meta_id = criar.json()['meta_id']
        res = self.client.get(reverse('metas'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f'id="meta-{meta_id}"')
        self.assertContains(res, 'Correr 10 km continuamente')
        self.assertContains(res, 'Completar uma corrida contínua de 10 km')
        self.assertContains(res, '8 semanas')
        self.assertContains(res, 'Adaptação')
        self.assertContains(res, 'destacarMetaPorHash')


class ObterResumoMetaHelperTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome_completo='Cliente Resumo',
            idade=30,
            email='resumo@teste.com',
            password='senha123',
            lgpd=True,
        )
        self.habito = Habito.objects.create(
            cliente=self.cliente,
            tipo_habito='positivo',
            nome_habito='Academia',
            frequencia_atual_valor=2,
            frequencia_atual_periodo='semana',
            frequencia_desejada_valor=4,
            frequencia_desejada_periodo='semana',
        )
        self.meta = Meta.objects.create(
            habito=self.habito,
            quantidade_minima=3,
            periodo='semana',
        )

    def test_resumo_readonly_nao_cria_ciclo(self):
        ciclos_antes = MetaCiclo.objects.count()
        resumo = obter_resumo_meta(self.meta)
        self.assertEqual(MetaCiclo.objects.count(), ciclos_antes)
        self.assertEqual(resumo['quantidade_minima'], 3)
        self.assertEqual(resumo['habito_nome'], 'Academia')
        self.assertFalse(resumo['tem_plano'])
        self.assertIn('progresso', resumo)
        self.assertIn('percentual', resumo)

    def test_resumo_com_plano_assistente(self):
        PlanoMetaAssistente.objects.create(
            meta=self.meta,
            titulo_meta='Correr 10 km continuamente',
            objetivo_principal='Completar uma corrida contínua de 10 km.',
            duracao_semanas=8,
            nivel='equilibrada',
            justificativa='Baseado no histórico.',
            criterio_sucesso='Completar a prova.',
            plano_recuperacao='Repetir a etapa.',
            etapas=[{'titulo': 'Adaptação', 'inicio_semana': 1, 'fim_semana': 2, 'descricao': 'Leve'}],
        )
        resumo = obter_resumo_meta(self.meta)
        self.assertTrue(resumo['tem_plano'])
        self.assertEqual(resumo['titulo_meta'], 'Correr 10 km continuamente')
        self.assertEqual(resumo['prazo_semanas'], 8)
        self.assertEqual(resumo['url_plano'], f'/metas/#meta-{self.meta.id}')
