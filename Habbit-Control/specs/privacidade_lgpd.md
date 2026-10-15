# Especificação: Privacidade e Conformidade LGPD

## Visão Geral do Módulo
O módulo de privacidade e conformidade assegura o atendimento à Lei Geral de Proteção de Dados Pessoais do Brasil (LGPD — Lei Federal nº 13.709/2018). Ele disponibiliza publicamente a política de privacidade da plataforma, exige o consentimento explícito e afirmativo do titular durante o cadastro e garante a rastreabilidade do aceite no banco de dados.

---

## Requisitos do Sistema

### REQ-LGPD-01 — Página Pública de Política de Privacidade e Consentimento

**Descrição EARS:**  
WHEN any user accesses the route `/consentimento/` via HTTP GET, THE SYSTEM SHALL render the LGPD privacy policy page (`consentimento.html`) detailing the categories of personal data collected, the purposes of data collection, technical data protection measures, and statutory user rights under Brazilian Federal Law 13.709/2018 with HTTP 200.

**Objetivo:**  
Garantir o direito à informação e a transparência ativa, permitindo a qualquer visitante ou cliente consultar a política completa de tratamento de dados pessoais da aplicação.

**Ator:**  
Qualquer usuário (visitante anônimo ou cliente autenticado).

**Pré-condições:**
- A aplicação web está em execução.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. A rota `/consentimento/` deve ser pública e não exigir autenticação nem sessão ativa.
2. A resposta deve ter código de status HTTP 200 e utilizar o template `login_cadastro_app/consentimento.html`.
3. O documento exibido deve discriminar com precisão:
   - **Categorias de dados coletados:** Nome completo, Idade, Email, Cidade e residência, Profissão (opcional);
   - **Finalidades de tratamento:** Segurança da plataforma (prevenção a fraudes e bots), Estudos acadêmicos anonimizados e Melhoria dos serviços;
   - **Medidas técnicas de proteção:** Armazenamento em servidores com criptografia e hash PBKDF2 SHA-256 para credenciais;
   - **Direitos do titular previstos na LGPD:** Acesso, correção de dados incompletos ou desatualizados, exclusão de dados, revogação do consentimento, portabilidade e não submissão a decisões automatizadas;
   - **Compartilhamento de dados:** Proibição de repasse a terceiros sem consentimento prévio, exceto obrigação legal ou dados anonimizados para fins acadêmicos.
4. A página deve conter links de navegação para retornar ao formulário de cadastro (`javascript:history.back()`) e para a página inicial (`/`).

**Fluxo principal:**
1. O usuário clica no link "termos da Lei Geral de Proteção de Dados (LGPD)" no cadastro ou acessa diretamente `/consentimento/`.
2. A view `consentimento` processa a requisição GET.
3. O sistema renderiza o template `consentimento.html` com status HTTP 200.
4. O usuário visualiza o texto integral da política de privacidade.

**Fluxos alternativos e de erro:**
- Não há fluxos alternativos definidos para o método GET.

**Resultado esperado:**
- Página HTML carregada com status HTTP 200 contendo o texto legal estruturado em seções numeradas.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um visitante não autenticado
  WHEN enviar requisição HTTP GET para `/consentimento/`
  THEN o sistema deve responder com código de status HTTP 200
  AND o corpo da resposta deve conter as seções "1. Dados Coletados", "2. Finalidades da Coleta de Dados", "3. Proteção de Dados" e "4. Seus Direitos"
  AND deve fazer referência explícita à "Lei nº 13.709".

**Casos-limite:**
- Acesso por usuário logado ou deslogado: a renderização ocorre sem distinção.

**Fora de escopo:**
- Aceite de termos em formato de modal bloqueante dentro da rota de consentimento.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/urls.py`, `apps/login_cadastro_app/views.py` (`consentimento`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/consentimento.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-LGPD-02 — Exibição de Checkbox de Consentimento Obrigatório com Link Direto

**Descrição EARS:**  
THE SYSTEM SHALL display a mandatory consent checkbox on the client registration page (`cadastro_cliente.html`) containing an explicit hyperlink targeting `/consentimento/` with `target="_blank"`, accompanied by descriptive text outlining the processing of personal data in accordance with the LGPD.

**Objetivo:**  
Assegurar que o formulário de cadastro forneça o meio para a manifestação livre, informada e inequívoca do consentimento do titular no exato momento da coleta dos dados.

**Ator:**  
Visitante preenchendo o cadastro.

**Pré-condições:**
- Acesso à rota `/cadastro/cliente/`.

**Entradas:**
| Elemento Visual | Tipo | Obrigatório |
|---|---|---|
| Checkbox `lgpd` | HTML Checkbox Input | Sim |

**Regras de negócio:**
1. O formulário `ClienteForm` deve expor o campo `lgpd` como campo booleano obrigatório (`required=True` por padrão de campos não nulos no Django).
2. No template `cadastro_cliente.html`, o elemento de marcação deve ser acompanhado pelo texto descritivo:
   - Rótulo principal com indicador de obrigatoriedade (`*`): `"Aceito os termos da Lei Geral de Proteção de Dados (LGPD)"`;
   - O trecho `"termos da Lei Geral de Proteção de Dados (LGPD)"` deve ser um elemento hiperlink (`<a>`) apontando para a URL reversa `{% url 'consentimento' %}`;
   - O hiperlink deve conter o atributo `target="_blank"`, garantindo que a política de privacidade seja aberta em nova aba do navegador sem descarregar os dados já preenchidos no formulário de cadastro;
   - Subtexto explicativo: `"Concordo com o tratamento dos meus dados pessoais conforme a LGPD."`.
3. O checkbox deve ser renderizado inicialmente desmarcado (`default=False`), impedindo consentimento presumido ou pré-assinalado.

**Fluxo principal:**
1. O visitante acessa a tela de cadastro `/cadastro/cliente/`.
2. A seção "Consentimentos" exibe o checkbox desmarcado e o link destacado.
3. O visitante clica no link e a política abre em nova aba.
4. O visitante retorna à aba de cadastro e marca a caixa de seleção.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Checkbox de consentimento renderizado com hiperlink funcional para abertura da política em nova aba.

**Persistência:**
- Nenhuma alteração no banco de dados durante a exibição.

**Critérios de aceitação:**
- GIVEN a página de cadastro carregada
  WHEN o HTML renderizado for inspecionado
  THEN o campo de entrada do checkbox `lgpd` deve estar presente
  AND deve existir uma tag `<a href="/consentimento/" target="_blank">` associada ao texto explicativo.

**Casos-limite:**
- Navegador com bloqueador de pop-ups: como o link possui `target="_blank"` disparado por clique de usuário, a abertura de nova aba é permitida pelos navegadores modernos.

**Fora de escopo:**
- Registro de logs com hash da versão dos termos de uso aceitos em tabela dedicada de auditoria de consentimento.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/forms.py` (`ClienteForm`), `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-LGPD-03 — Persistência do Consentimento Afirmativo

**Descrição EARS:**  
WHEN a client registration is successfully processed, THE SYSTEM SHALL persist the affirmative consent state as a boolean `True` value in the `lgpd` attribute of the `Cliente` database model.

**Objetivo:**  
Registrar permanentemente no banco de dados a evidência de que o titular concedeu autorização formal para o tratamento de seus dados pessoais.

**Ator:**  
Visitante submetendo cadastro válido.

**Pré-condições:**
- O visitante preencheu todos os campos obrigatórios e marcou o checkbox `lgpd`.

**Entradas:**
| Campo | Tipo | Valor |
|---|---|---|
| `lgpd` | Booleano | `True` (checkbox assinalado no POST). |

**Regras de negócio:**
1. O modelo `Cliente` define a coluna `lgpd = models.BooleanField(default=False, verbose_name="Aceitou Termos LGPD")`.
2. Quando a submissão de cadastro for concluída com sucesso via `form.save()`, a coluna `lgpd` no banco de dados deve registrar o valor `True`.
3. O valor padrão a nível de modelo é `False`, garantindo que nenhuma entidade seja instanciada com consentimento presumido no banco de dados.

**Fluxo principal:**
1. O visitante submete o formulário com o checkbox `lgpd` marcado.
2. O formulário avalia `form.cleaned_data['lgpd'] == True`.
3. A instância de `Cliente` é persistida no banco de dados com a coluna `lgpd=True`.
4. O usuário é redirecionado para `/login/`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Novo registro na tabela `login_cadastro_app_cliente` com a coluna `lgpd` gravada como `True`.

**Persistência:**
- Tabela `login_cadastro_app_cliente`: coluna `lgpd` com valor booleano `True` (armazenado como `1` em bancos relacionais como SQLite ou PostgreSQL).

**Critérios de aceitação:**
- GIVEN um cadastro submetido com o consentimento LGPD aceito
  WHEN o registro for salvo no banco de dados
  THEN o atributo `cliente.lgpd` deve ser estritamente igual a `True`.

**Casos-limite:**
- Criação programática via `Cliente.objects.create` sem passar o parâmetro `lgpd`: assume `False` por padrão (`default=False`).

**Fora de escopo:**
- Armazenamento de carimbo temporal (*timestamp*) específico e endereço IP da concessão do consentimento em tabela dedicada.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/models.py` (`Cliente.lgpd`), `apps/login_cadastro_app/forms.py` (`ClienteForm`), `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`ClienteModelTest.test_criar_cliente_sem_cpf`, `CadastroClienteViewTest.test_post_cadastro_sucesso`)

---

### REQ-LGPD-04 — Rejeição de Cadastro sem Consentimento do Titular

**Descrição EARS:**  
IF a client registration request is submitted without the user checking the `lgpd` agreement checkbox, THEN THE SYSTEM SHALL invalidate the submission, prevent account persistence, re-render the registration form with HTTP 200, and display the appropriate field validation error.

**Objetivo:**  
Impedir a coleta e tratamento de dados de usuários que não concederam permissão formal nos termos da legislação brasileira vigente.

**Ator:**  
Visitante.

**Pré-condições:**
- Requisição HTTP POST enviada para `/cadastro/cliente/` com o campo `lgpd` desmarcado ou ausente.

**Entradas:**
| Campo | Tipo | Condição |
|---|---|---|
| `lgpd` | Booleano | Ausente do payload ou com valor `False`. |

**Regras de negócio:**
1. A validação do campo `lgpd` no `ClienteForm` falha caso o valor recebido não seja afirmativo.
2. O formulário deve adicionar um erro de validação ao campo `lgpd` (mensagem padrão do Django: `"Este campo é obrigatório."`).
3. A view `cadastro_cliente` não deve prosseguir para a etapa de gravação (`form.save()` não é chamado).
4. O sistema não deve criar registros na tabela `Cliente`.
5. A página de cadastro `cadastro_cliente.html` deve ser re-renderizada com código de status HTTP 200.
6. A notificação de erro deve ser exibida ao usuário alertando sobre a pendência de aceite.

**Fluxo principal:**
1. O visitante preenche seus dados pessoais e de acesso, mas não marca o checkbox de consentimento.
2. O visitante clica em "Criar Conta".
3. A view `cadastro_cliente` recebe o POST e executa `form.is_valid()`, que retorna `False`.
4. A view adiciona as mensagens de erro dos campos em `messages.error`.
5. O template `cadastro_cliente.html` é re-renderizado com código HTTP 200.
6. A mensagem de erro é exibida junto ao campo de consentimentos e na notificação superior.
7. A conta não é cadastrada.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Formulário re-renderizado com HTTP 200.
- Exibição de erro de validação específico no campo de consentimento.
- Nenhum registro persistido no banco de dados.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um visitante que fornece todos os campos obrigatórios válidos
  WHEN deixar de assinalar o campo `lgpd` no formulário
  THEN o código HTTP de resposta deve ser 200
  AND o formulário deve conter erro de validação no campo `lgpd`
  AND a contagem de registros na tabela `Cliente` deve permanecer inalterada.

**Casos-limite:**
- Requisição direta via API/cURL contendo payload JSON ou formulário sem a chave `lgpd`: rejeição idêntica com código HTTP 200 re-renderizando a mensagem de erro do formulário.

**Fora de escopo:**
- Notificação legal por e-mail sobre a recusa do consentimento.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/forms.py` (`ClienteForm`), `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`ClienteFormTest.test_formulario_valido`)
