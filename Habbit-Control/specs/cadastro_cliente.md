# Especificação: Cadastro de Cliente

## Visão Geral do Módulo
O módulo de cadastro de cliente gerencia o registro de novos usuários no sistema Habbit-Control. Ele assegura a coleta de dados cadastrais essenciais, a validação de formato e integridade, o armazenamento seguro de credenciais criptografadas via PBKDF2 SHA-256 e o consentimento explícito aos termos da Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018).

---

## Requisitos do Sistema

### REQ-CAD-01 — Renderização da Página de Cadastro

**Descrição EARS:**  
WHEN an unauthenticated user or visitor requests the URL `/cadastro/cliente/` via HTTP GET, THE SYSTEM SHALL render the client registration interface displaying the `ClienteForm` with all defined input fields, selection elements, and the mandatory LGPD consent checkbox.

**Objetivo:**  
Permitir que qualquer visitante acesse a interface visual de criação de conta contendo os campos necessários para o fornecimento de seus dados cadastrais.

**Ator:**  
Visitante (usuário não autenticado).

**Pré-condições:**
- A aplicação web deve estar em execução e acessível.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. A rota `/cadastro/cliente/` deve responder a requisições com o método HTTP GET.
2. A resposta deve renderizar o formulário HTML `ClienteForm` instanciado sem dados prévios.
3. O formulário deve expor os campos: `nome_completo`, `idade`, `email`, `password`, `estado`, `cidade`, `profissao` e `lgpd`.
4. O campo `password` deve ser renderizado como campo de entrada com ocultação de caracteres (`type="password"`).
5. O campo `estado` deve ser renderizado inicialmente com a opção padrão "Selecione o estado".
6. O campo `cidade` deve ser renderizado inicialmente desabilitado com o texto "Selecione primeiro o estado".
7. Nenhum campo correspondente a CPF deve ser exibido ou aceito.

**Fluxo principal:**
1. O visitante envia uma requisição HTTP GET para `/cadastro/cliente/`.
2. A view `cadastro_cliente` instancia um `ClienteForm` vazio.
3. O sistema renderiza o template `login_cadastro_app/cadastro_cliente.html` com código de status HTTP 200.
4. A página é apresentada com os campos em branco e o botão "Criar Conta".

**Fluxos alternativos e de erro:**
- Não há fluxos alternativos definidos para o método GET.

**Resultado esperado:**
- Página HTML carregada contendo o formulário de cadastro estruturado em seções ("Dados Pessoais e Acesso", "Localização", "Profissão", "Consentimentos").

**Persistência:**
- Nenhuma alteração é persistida no banco de dados.

**Critérios de aceitação:**
- GIVEN que um visitante acessa a aplicação
  WHEN enviar uma requisição HTTP GET para `/cadastro/cliente/`
  THEN o sistema deve responder com código HTTP 200
  AND o corpo da resposta deve conter o formulário com os campos `nome_completo`, `idade`, `email`, `password`, `estado`, `cidade`, `profissao` e `lgpd`
  AND o campo ou máscara de CPF não deve estar presente no conteúdo retornado.

**Casos-limite:**
- Acesso à rota por usuário já detentor de sessão ativa: o sistema renderiza a página de cadastro exibindo o formulário sem redirecionamento automático.

**Fora de escopo:**
- Cadastro via login social (OAuth / Google / Facebook).
- Pré-preenchimento automático com base em geolocalização IP.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/views.py` (`cadastro_cliente`), `apps/login_cadastro_app/forms.py` (`ClienteForm`), `apps/login_cadastro_app/urls.py`
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`CadastroClienteViewTest.test_get_cadastro_retorna_200`, `ClienteFormTest.test_formulario_sem_campo_cpf`)

---

### REQ-CAD-02 — Submissão de Cadastro com Dados Válidos

**Descrição EARS:**  
WHEN a visitor submits valid registration data via HTTP POST to `/cadastro/cliente/` with `nome_completo`, `idade`, `email`, `password`, and accepted `lgpd` terms, THE SYSTEM SHALL persist a new `Cliente` record, normalize the email to lowercase and trimmed string, hash the password using PBKDF2 SHA-256, and redirect the user to `/login/`.

**Objetivo:**  
Registrar um novo cliente no banco de dados com credenciais seguras e redirecioná-lo para a tela de autenticação.

**Ator:**  
Visitante.

**Pré-condições:**
- O visitante preencheu todos os campos obrigatórios com valores válidos.
- O e-mail informado não está em uso por outro cliente.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `nome_completo` | String | Sim | Máximo de 255 caracteres. |
| `idade` | Inteiro | Sim | Inteiro maior ou igual a 0. |
| `email` | String | Sim | Formato de e-mail válido, máximo de 254 caracteres. |
| `password` | String | Sim | Texto da senha em texto plano; máximo de 100 caracteres no formulário. |
| `estado` | String | Não | Sigla de UF brasileira com até 2 caracteres, ou vazio/nulo. |
| `cidade` | String | Não | Máximo de 100 caracteres, ou vazio/nulo. |
| `profissao` | String | Não | Máximo de 100 caracteres, ou vazio/nulo. |
| `lgpd` | Booleano | Sim | Deve ser estritamente `True` (marcado). |

**Regras de negócio:**
1. O e-mail fornecido deve ser normalizado no método `clean_email()` do formulário e no método `save()` do modelo, convertendo todos os caracteres para letras minúsculas e eliminando espaços em branco nas extremidades (`email.lower().strip()`).
2. A senha submetida deve ser convertida em hash seguro utilizando o algoritmo PBKDF2 com digest SHA-256 (`pbkdf2_sha256$`) antes de ser persistida no banco de dados.
3. A senha em texto plano nunca deve ser persistida nem registrada em logs.
4. O consentimento `lgpd` deve ser armazenado como booleano `True` no registro do `Cliente`.
5. A data e hora de criação (`data_criacao`) devem ser geradas automaticamente pelo sistema via `auto_now_add=True`.
6. Após a persistência bem-sucedida, o sistema deve responder com redirecionamento HTTP 302 para a rota `login` (`/login/`).
7. Nenhum campo ou menção a CPF deve ser processado ou salvo.

**Fluxo principal:**
1. O visitante submete o formulário com dados válidos via HTTP POST para `/cadastro/cliente/`.
2. A view valida o token CSRF da requisição.
3. O `ClienteForm` valida a conformidade dos dados informados.
4. O método `clean_email` normaliza o e-mail e valida a ausência de duplicidade.
5. A view chama `form.save()`, que dispara o método `save()` do modelo `Cliente`.
6. O modelo assegura a normalização do e-mail e aplica o hash PBKDF2 SHA-256 na senha.
7. O registro é persistido na tabela `login_cadastro_app_cliente`.
8. O sistema emite resposta HTTP 302 redirecionando o navegador para `/login/`.

**Fluxos alternativos e de erro:**
- Se o token CSRF for ausente ou inválido, o middleware do Django rejeita a requisição com HTTP 403 Forbidden.
- Se algum campo obrigatório for omitido ou inválido, o sistema executa o fluxo de erro documentado no REQ-CAD-04 e nas validações do formulário.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/login/`.
- Registro do cliente inserido no banco de dados com hash de senha e e-mail normalizado.

**Persistência:**
- Tabela `login_cadastro_app_cliente`: inserção de 1 novo registro contendo `nome_completo`, `idade`, `email` (em minúsculas), `password` (iniciando com prefixo `pbkdf2_sha256$`), `estado`, `cidade`, `profissao`, `lgpd=True` e `data_criacao`.

**Critérios de aceitação:**
- GIVEN que um visitante preenche o formulário com `nome_completo="Carlos Pereira"`, `idade=40`, `email="  CARLOS@GMAIL.COM  "`, `password="senhaForte@123"` e `lgpd=True`
  WHEN enviar a requisição HTTP POST para `/cadastro/cliente/`
  THEN o sistema deve redirecionar com HTTP 302 para `/login/`
  AND o banco de dados deve conter exatamente 1 registro com `email="carlos@gmail.com"`
  AND o atributo `password` armazenado deve iniciar com `pbkdf2_sha256$`
  AND o método `cliente.check_password("senhaForte@123")` deve retornar `True`.

**Casos-limite:**
- E-mail com espaços no início e no fim e caracteres em maiúsculas: o sistema deve remover os espaços e converter tudo para minúsculas.
- Campos opcionais (`estado`, `cidade`, `profissao`) não preenchidos: o sistema deve persistir com valores nulos/vazios sem falha.

**Fora de escopo:**
- Envio de e-mail de ativação de conta ou confirmação de cadastro.
- Autenticação e criação de sessão automática imediatamente após o cadastro.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/models.py` (`Cliente.save`, `Cliente.check_password`), `apps/login_cadastro_app/forms.py` (`ClienteForm`), `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`ClienteModelTest.test_criar_cliente_sem_cpf`, `CadastroClienteViewTest.test_post_cadastro_sucesso`)

---

### REQ-CAD-03 — Rejeição de E-mail Duplicado

**Descrição EARS:**  
IF a user submits a registration request with an email address that already belongs to an existing `Cliente` (evaluated case-insensitively and trimmed), THEN THE SYSTEM SHALL reject the registration, prevent creation of duplicate records, re-render the registration form with HTTP 200, and display the error message: "Este email já está cadastrado. Por favor, use outro email ou faça login."

**Objetivo:**  
Garantir a unicidade da credencial de e-mail no sistema, impedindo que contas distintas compartilhem o mesmo endereço de correio eletrônico.

**Ator:**  
Visitante.

**Pré-condições:**
- Já existe um registro na tabela `Cliente` cujo e-mail normalizado coincide com o e-mail informado na requisição.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `email` | String | Sim | Endereço idêntico ao de um registro pré-existente após `lower().strip()`. |
| Demais campos cadastrais | Diversos | Conforme formulário | Preenchidos ou não. |

**Regras de negócio:**
1. A comparação de e-mail para verificação de unicidade deve ser insensível a maiúsculas/minúsculas (*case-insensitive*) e desconsiderar espaços antes e depois do texto.
2. A validação de unicidade deve ocorrer em três camadas de defesa:
   - No formulário `ClienteForm.clean_email()`;
   - Na view `cadastro_cliente` antes do salvamento (`Cliente.objects.filter(email=email).exists()`);
   - Na restrição de banco de dados `models.EmailField(unique=True)`, capturada por bloco `except IntegrityError`.
3. Quando a duplicidade for detectada, o sistema deve impedir a criação do registro.
4. A mensagem exibida ao usuário deve ser exatamente: `"Este email já está cadastrado. Por favor, use outro email ou faça login."`.
5. A página de cadastro deve ser re-renderizada preservando os dados já preenchidos no formulário (exceto senhas, por padrão do widget `PasswordInput`).
6. O status HTTP retornado deve ser 200 OK.

**Fluxo principal:**
1. O visitante submete o formulário via HTTP POST para `/cadastro/cliente/` informando um e-mail já cadastrado.
2. O método `clean_email()` do `ClienteForm` normaliza o e-mail e consulta `Cliente.objects.filter(email=email)`.
3. Constatada a existência prévia, o formulário adiciona um `forms.ValidationError` com a mensagem `"Este email já está cadastrado. Por favor, use outro email ou faça login."`.
4. O formulário é avaliado como inválido (`form.is_valid() == False`).
5. A view itera sobre os erros e adiciona a mensagem flash via `messages.error(request, ...)`.
6. A view renderiza `cadastro_cliente.html` com o formulário contendo os erros e código HTTP 200.

**Fluxos alternativos e de erro:**
- **Condição de concorrência (Race condition):** Dois cadastros com o mesmo e-mail submetidos simultaneamente passam pela validação do formulário. A segunda operação dispara `IntegrityError` no banco de dados. A view captura a exceção no bloco `except IntegrityError`, adiciona a mensagem `"Este email já está cadastrado. Por favor, use outro email ou faça login."` ao `messages` e re-renderiza o formulário com HTTP 200.

**Resultado esperado:**
- Formulário re-renderizado com código HTTP 200.
- Exibição da mensagem de erro de e-mail duplicado em notificação toast e na lista de erros do campo.
- Nenhum registro criado no banco de dados.

**Persistência:**
- Nenhuma alteração persistida no banco de dados. O número total de registros de `Cliente` permanece inalterado.

**Critérios de aceitação:**
- GIVEN que existe um cliente com e-mail `"original@gmail.com"`
  WHEN um visitante submeter cadastro com `email="ORIGINAL@GMAIL.COM"`
  THEN o sistema deve responder com código HTTP 200
  AND a contagem de clientes com e-mail `"original@gmail.com"` deve permanecer igual a 1
  AND a resposta deve conter a mensagem de erro `"Este email já está cadastrado. Por favor, use outro email ou faça login."`.

**Casos-limite:**
- E-mail com espaços e caixa mista (`"  OriGiNal@GMail.com  "`): deve colidir com `"original@gmail.com"` e ser rejeitado.

**Fora de escopo:**
- Link direto de recuperação de senha incorporado à mensagem de erro.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/models.py` (`Cliente.email`), `apps/login_cadastro_app/forms.py` (`ClienteForm.clean_email`), `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`ClienteModelTest.test_email_unico_no_modelo`, `ClienteFormTest.test_formulario_rejeita_email_duplicado`, `CadastroClienteViewTest.test_post_cadastro_email_duplicado`)

---

### REQ-CAD-04 — Validação em Tempo Real no Cliente (Frontend)

**Descrição EARS:**  
WHILE the user is interacting with form inputs on the registration page, THE SYSTEM SHALL validate on `blur` that the email matches `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` and that the age is an integer between 0 and 150, toggling the CSS classes `valid` or `invalid` on the enclosing form group.

**Objetivo:**  
Fornecer feedback visual instantâneo ao usuário enquanto preenche o formulário, sinalizando conformidade ou irregularidade nos campos antes da submissão.

**Ator:**  
Visitante.

**Pré-condições:**
- A página de cadastro foi carregada no navegador com suporte a JavaScript habilitado.

**Entradas:**
| Campo | Evento | Expressão / Regra |
|---|---|---|
| `#id_email` | `blur` | Expressão regular: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` |
| `#id_idade` | `blur` | `!isNaN(parseInt(value)) && age >= 0 && age <= 150` |

**Regras de negócio:**
1. Se o campo for desprovido de foco (`blur`) e o valor for vazio após remoção de espaços em branco, as classes `valid` e `invalid` devem ser removidas do elemento pai `.form-group`.
2. Se o campo contiver valor não vazio e a validação for verdadeira:
   - A classe `valid` deve ser adicionada ao elemento pai `.form-group`.
   - A classe `invalid` deve ser removida do elemento pai `.form-group`.
3. Se o campo contiver valor não vazio e a validação falhar:
   - A classe `invalid` deve ser adicionada ao elemento pai `.form-group`.
   - A classe `valid` deve ser removida do elemento pai `.form-group`.
4. Ao focar (`focus`) em qualquer campo de entrada, a classe `focused` deve ser adicionada ao `.form-group`. Ao perder o foco (`blur`), a classe `focused` deve ser removida.
5. Na submissão do formulário, o botão `.btn-submit` deve receber a classe `loading` e a propriedade `disabled = true`.
6. DECISÃO PENDENTE: A idade máxima de 150 anos está implementada apenas no script de frontend (`masks.js`). O backend (`forms.py` e `models.py`) não valida o limite superior de idade, aceitando qualquer inteiro suportado pelo `PositiveIntegerField`. Definir se um validador de idade máxima de 150 anos deve ser adicionado explicitamente ao `ClienteForm` no backend.

**Fluxo principal:**
1. O usuário digita um valor no campo de e-mail ou de idade.
2. O usuário retira o foco do campo disparando o evento `blur`.
3. O script `masks.js` intercepta o evento, remove listas de erro anteriores do Django (`.errorlist`) dentro do grupo e executa o validador.
4. O container `.form-group` recebe a classe CSS `valid` caso atenda ao padrão, ou `invalid` caso não atenda.

**Fluxos alternativos e de erro:**
- Usuário com JavaScript desabilitado: a validação dinâmica em tempo real não é executada; a validação é realizada exclusivamente pelo backend na submissão.

**Resultado esperado:**
- Atualização imediata das classes CSS nos elementos DOM do formulário com feedback visual (bordas/cores).

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN que o usuário está no campo de idade
  WHEN digitar `"160"` e disparar o evento `blur`
  THEN o container `.form-group` do campo idade deve conter a classe `invalid`
  AND não deve conter a classe `valid`.
- GIVEN que o usuário está no campo de e-mail
  WHEN digitar `"teste@valido.com"` e disparar o evento `blur`
  THEN o container `.form-group` do campo e-mail deve conter a classe `valid`
  AND não deve conter a classe `invalid`.

**Casos-limite:**
- Campo esvaziado pelo usuário: o sistema deve remover tanto `valid` quanto `invalid`.
- Idade `"0"`: deve ser considerada válida (`valid`), pois respeita `age >= 0`.

**Fora de escopo:**
- Consulta assíncrona ao servidor para verificar se o e-mail já existe durante a digitação.

**Rastreabilidade:**
- Implementação: `static/login_cadastro_app/js/masks.js`
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: Não coberto por teste automatizado (validação visual em cliente JS).

---

### REQ-CAD-05 — Carregamento Dinâmico de Estados e Cidades

**Descrição EARS:**  
WHEN the user selects a Brazilian state from the Estado dropdown, THE SYSTEM SHALL dynamically populate the Cidade dropdown with the cities associated with that state and enable the Cidade select element.

**Objetivo:**  
Permitir a seleção consistente de localização geográfica brasileira, vinculando a lista de cidades disponíveis ao estado escolhido pelo usuário.

**Ator:**  
Visitante.

**Pré-condições:**
- Página de cadastro renderizada no navegador com o script `estados_cidades.js` carregado.

**Entradas:**
| Campo | Tipo | Valores permitidos |
|---|---|---|
| Select `#id_estado` | String (sigla UF) | Uma das 27 siglas federativas: `AC`, `AL`, `AP`, `AM`, `BA`, `CE`, `DF`, `ES`, `GO`, `MA`, `MT`, `MS`, `MG`, `PA`, `PB`, `PR`, `PE`, `PI`, `RJ`, `RN`, `RS`, `RO`, `RR`, `SC`, `SP`, `SE`, `TO`. |

**Regras de negócio:**
1. Na inicialização da página, o select `#id_estado` deve ser populado com as 27 Unidades Federativas em ordem alfabética do nome do estado.
2. O select `#id_cidade` deve iniciar desabilitado (`disabled=true`) contendo a opção selecionada `"Selecione primeiro o estado"`.
3. Ao selecionar um estado válido:
   - O select `#id_cidade` deve ser habilitado (`disabled=false`);
   - Seu conteúdo anterior deve ser limpo;
   - Uma opção desabilitada `"Selecione a cidade"` deve ser inserida como padrão;
   - As cidades cadastradas para aquela UF no dicionário `estadosECidades` devem ser inseridas em ordem alfabética como opções válidas (`<option value="Nome">Nome</option>`).
4. Se o usuário desmarcar o estado ou selecionar opção vazia:
   - O select `#id_cidade` deve ser esvaziado e desabilitado novamente.

**Fluxo principal:**
1. O usuário clica no dropdown `#id_estado` e escolhe o estado `"SP"`.
2. O evento `change` é disparado.
3. O script localiza o vetor de cidades correspondente à chave `"SP"`.
4. As cidades são ordenadas alfabeticamente.
5. O elemento `#id_cidade` tem seu atributo `disabled` removido e suas opções preenchidas.
6. O usuário seleciona sua cidade na lista.

**Fluxos alternativos e de erro:**
- Usuário não preenche estado nem cidade: a submissão é processada com sucesso, pois os campos são opcionais no modelo (`blank=True, null=True`).

**Resultado esperado:**
- Dropdown de cidades liberado e populado de acordo com a UF escolhida.

**Persistência:**
- Nenhuma alteração direta. Na submissão, os valores selecionados são persistidos nos atributos `estado` e `cidade` do modelo `Cliente`.

**Critérios de aceitação:**
- GIVEN que o formulário está carregado
  WHEN o usuário selecionar o estado `"RJ"`
  THEN o campo `#id_cidade` deve se tornar habilitado
  AND deve conter entre as opções a cidade `"Rio de Janeiro"`.

**Casos-limite:**
- Troca de estado após ter selecionado uma cidade: a cidade anterior deve ser descartada e a nova lista de cidades deve ser recarregada com o placeholder `"Selecione a cidade"`.

**Fora de escopo:**
- Integração com API externa de CEP (ViaCEP) ou base completa de todos os municípios do IBGE além do dicionário estático existente.

**Rastreabilidade:**
- Implementação: `static/login_cadastro_app/js/estados_cidades.js`
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: Não coberto por teste automatizado (interação puramente client-side).

---

### REQ-CAD-06 — Alternância de Visibilidade da Senha

**Descrição EARS:**  
WHEN the user clicks the toggle password button on the registration form, THE SYSTEM SHALL alternate the password input type between `password` and `text` and update the eye icon visibility state.

**Objetivo:**  
Permitir que o usuário confira visualmente a senha digitada para evitar erros de digitação antes de submeter o cadastro.

**Ator:**  
Visitante.

**Pré-condições:**
- O formulário de cadastro deve estar visível no navegador.

**Entradas:**
| Elemento | Evento | Ação |
|---|---|---|
| Botão `#togglePassword` | `click` | Inverte o estado do atributo `type` de `#id_password`. |

**Regras de negócio:**
1. O clique no botão não deve submeter o formulário (deve executar `e.preventDefault()`).
2. Se o atributo `type` do campo `#id_password` for `"password"`, deve ser alterado para `"text"`:
   - O elemento visual `#eye-slash` deve receber `display = 'block'`;
   - O elemento visual `#eye-open` deve receber `opacity = '0.3'`.
3. Se o atributo `type` do campo `#id_password` for `"text"`, deve ser alterado para `"password"`:
   - O elemento visual `#eye-slash` deve receber `display = 'none'`;
   - O elemento visual `#eye-open` deve receber `opacity = '1'`.

**Fluxo principal:**
1. O usuário clica no botão `#togglePassword`.
2. O script identifica o tipo atual do campo de senha.
3. O tipo é invertido para `text`, permitindo visualizar a senha.
4. O ícone é alterado para representar que a senha está visível.
5. O usuário clica novamente, revertendo o tipo para `password`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Alternância instantânea da legibilidade da senha digitada no campo.

**Persistência:**
- Nenhuma alteração em banco de dados.

**Critérios de aceitação:**
- GIVEN que o campo de senha possui `type="password"`
  WHEN o usuário clicar no botão `#togglePassword`
  THEN o campo `#id_password` deve passar a ter o atributo `type="text"`.
- GIVEN que o campo de senha possui `type="text"`
  WHEN o usuário clicar no botão `#togglePassword`
  THEN o campo `#id_password` deve retornar ao atributo `type="password"`.

**Casos-limite:**
- Clique com o campo vazio: o tipo é alternado sem lançar exceções.

**Fora de escopo:**
- Medidor de força de senha complexo em tempo real.

**Rastreabilidade:**
- Implementação: `static/login_cadastro_app/js/masks.js`
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: Não coberto por teste automatizado.

---

### REQ-CAD-07 — Rejeição de Submissão sem Aceite dos Termos LGPD

**Descrição EARS:**  
IF the user submits the registration form without agreeing to the LGPD terms (`lgpd` checkbox unmarked), THEN THE SYSTEM SHALL reject the form submission, prevent account persistence, re-render the registration page with HTTP 200, and display a validation error.

**Objetivo:**  
Garantir conformidade jurídica estrita com a Lei Geral de Proteção de Dados, impedindo o processamento de cadastros sem o consentimento afirmativo do titular.

**Ator:**  
Visitante.

**Pré-condições:**
- O formulário de cadastro foi submetido via POST.

**Entradas:**
| Campo | Tipo | Valor |
|---|---|---|
| `lgpd` | Booleano | Ausente ou `False` (desmarcado). |

**Regras de negócio:**
1. O campo `lgpd` no `ClienteForm` é obrigatório para a validação positiva do formulário.
2. Caso o checkbox não seja marcado no formulário enviado, o Django avalia o campo como inválido e gera um erro de validação.
3. A view `cadastro_cliente` deve impedir a criação do registro `Cliente`.
4. O formulário deve ser retornado ao visitante com código de status HTTP 200.
5. Uma mensagem de erro de campo ("Este campo é obrigatório." ou respectiva mensagem de validação do Django) deve ser associada ao campo `lgpd`.

**Fluxo principal:**
1. O visitante preenche os dados cadastrais, porém deixa desmarcada a opção de consentimento da LGPD.
2. O visitante clica em "Criar Conta".
3. A view submete os dados ao `ClienteForm`.
4. `form.is_valid()` retorna `False` devido à ausência do consentimento obrigatório.
5. A view adiciona as mensagens de erro em `messages.error`.
6. A página `cadastro_cliente.html` é re-renderizada com código HTTP 200 contendo a indicação de erro junto ao checkbox.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Formulário re-renderizado com HTTP 200 e mensagem de erro indicando a obrigatoriedade do aceite da LGPD.
- Nenhum registro criado no banco de dados.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um visitante que submete todos os dados obrigatórios preenchidos
  WHEN o campo `lgpd` for omitido ou enviado como `False`
  THEN o formulário não deve ser salvo
  AND a resposta deve ter código HTTP 200
  AND a contagem de clientes no banco não deve aumentar.

**Casos-limite:**
- Submissão via requisição direta (sem navegador) com payload sem a chave `lgpd`: o sistema deve rejeitar no backend com erro de validação de formulário.

**Fora de escopo:**
- Assinatura digital de termos ou geração de documento PDF assinado.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/forms.py` (`ClienteForm`), `apps/login_cadastro_app/models.py` (`Cliente.lgpd`), `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`ClienteFormTest.test_formulario_valido`)
