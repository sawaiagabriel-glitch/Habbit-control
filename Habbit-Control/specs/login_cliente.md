# Especificação: Login e Autenticação de Cliente

## Visão Geral do Módulo
O módulo de autenticação é responsável por verificar a identidade dos clientes cadastrados no Habbit-Control por meio do par de credenciais e-mail e senha. Ele estabelece e encerra sessões de usuário baseadas em cookies de sessão do Django, utilizando a chave customizada `cliente_email` em `request.session`.

---

## Requisitos do Sistema

### REQ-LOGIN-01 — Renderização da Interface de Login

**Descrição EARS:**  
WHEN a user accesses the URL `/login/` via HTTP GET, THE SYSTEM SHALL render the login interface displaying the `LoginForm` with Email and Senha fields, clearing previously stored flash messages before rendering.

**Objetivo:**  
Apresentar a tela de login limpa e desprovida de notificações residuais de navegações anteriores.

**Ator:**  
Visitante ou cliente desautenticado.

**Pré-condições:**
- A aplicação web deve estar ativa e acessível.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. A rota `/login/` deve aceitar requisições HTTP GET.
2. Antes de renderizar a página, todas as mensagens pendentes no framework de mensagens do Django (`messages.get_messages(request)`) devem ser marcadas como consumidas (`storage.used = True`).
3. O formulário `LoginForm` deve ser instanciado vazio, contendo os campos `email` e `password`.
4. O campo `password` deve ser exibido com caracteres ocultos (`type="password"`).
5. A resposta deve ter código HTTP 200 e utilizar o template `login_cadastro_app/login.html`.

**Fluxo principal:**
1. O usuário requisita `/login/` via HTTP GET.
2. A view `login` acessa o repositório de mensagens e define `storage.used = True`.
3. A view cria uma instância vazia de `LoginForm`.
4. O sistema renderiza o template `login.html` com status HTTP 200.

**Fluxos alternativos e de erro:**
- Não há fluxos alternativos definidos para o método GET.

**Resultado esperado:**
- Formulário de login exibido com campos de e-mail e senha vazios e nenhuma mensagem prévia na tela.

**Persistência:**
- Nenhuma alteração persistida em banco de dados.

**Critérios de aceitação:**
- GIVEN que um usuário acessa `/login/` via HTTP GET
  WHEN a página é processada pela view
  THEN o código de status HTTP retornado deve ser 200
  AND os campos `email` e `password` devem estar presentes no formulário
  AND qualquer mensagem pré-existente no storage de mensagens não deve ser exibida.

**Casos-limite:**
- Acesso à tela de login com sessão ativa existente: a página é renderizada exibindo o formulário sem encerramento automático da sessão prévia.

**Fora de escopo:**
- Bloqueio de múltiplos acessos simultâneos por IP.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/urls.py`, `apps/login_cadastro_app/views.py` (`login`), `apps/login_cadastro_app/forms.py` (`LoginForm`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-LOGIN-02 — Autenticação Bem-Sucedida de Credenciais

**Descrição EARS:**  
WHEN the user submits valid email and password credentials via HTTP POST to `/login/`, THE SYSTEM SHALL verify the password against the stored PBKDF2 hash using `Cliente.check_password`, store the authenticated email in `request.session['cliente_email']`, create a welcome success flash message ("Bem-vindo(a), [PrimeiroNome]!"), and redirect the user to `/alterar_dados/`.

**Objetivo:**  
Autenticar o cliente que possui registro cadastrado, iniciar sua sessão no servidor e redirecioná-lo para a área restrita do sistema.

**Ator:**  
Cliente cadastrado.

**Pré-condições:**
- O cliente possui cadastro prévio na tabela `Cliente` com senha criptografada em PBKDF2 SHA-256.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `email` | String | Sim | Formato de e-mail válido. |
| `password` | String | Sim | Senha do usuário em texto plano. |

**Regras de negócio:**
1. O e-mail recebido deve ser normalizado para letras minúsculas e sem espaços laterais (`email.lower().strip()`).
2. O sistema deve localizar o cliente único na tabela `Cliente` pelo e-mail normalizado.
3. A verificação da senha deve ser efetuada chamando o método `cliente.check_password(password)`, que delega à função `check_password` do Django com o algoritmo PBKDF2 SHA-256.
4. Quando a verificação for positiva:
   - As mensagens anteriores do storage devem ser marcadas como usadas;
   - O e-mail do cliente deve ser registrado na sessão HTTP na chave `request.session['cliente_email'] = cliente.email`;
   - Uma mensagem de sucesso deve ser registrada no framework de mensagens com o formato: `"Bem-vindo(a), {primeiro_nome}!"`, onde `primeiro_nome` é o primeiro elemento resultante de `cliente.nome_completo.split()[0]`;
   - A resposta deve ser um redirecionamento HTTP 302 para a rota `alterar_dados` (`/alterar_dados/`).

**Fluxo principal:**
1. O usuário submete o formulário com e-mail e senha corretos via HTTP POST para `/login/`.
2. O `LoginForm` valida a presença e formato dos campos.
3. A view `login` busca o registro do cliente correspondente ao e-mail.
4. O método `cliente.check_password(password)` retorna `True`.
5. A view grava `request.session['cliente_email'] = cliente.email`.
6. A view adiciona a mensagem flash `"Bem-vindo(a), [PrimeiroNome]!"`.
7. O sistema retorna redirecionamento HTTP 302 para `/alterar_dados/`.

**Fluxos alternativos e de erro:**
- Token CSRF ausente ou inválido: requisição rejeitada com HTTP 403 Forbidden.
- E-mail não encontrado ou senha incorreta: processado conforme REQ-LOGIN-04.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/alterar_dados/`.
- Sessão criada contendo a chave `cliente_email`.
- Cookie de sessão `sessionid` enviado ao navegador.

**Persistência:**
- Registro de sessão atualizado na tabela de sessões do Django (`django_session`). Nenhuma alteração nos dados do modelo `Cliente`.

**Critérios de aceitação:**
- GIVEN um cliente cadastrado com `nome_completo="Ana Souza"`, `email="ana@example.com"` e senha `"senhaCerta123"`
  WHEN submeter requisição POST para `/login/` com `email="ana@example.com"` e `password="senhaCerta123"`
  THEN o sistema deve redirecionar para `/alterar_dados/` com HTTP 302
  AND a chave `cliente_email` na sessão do cliente deve conter o valor `"ana@example.com"`.

**Casos-limite:**
- Nome do cliente contendo apenas uma palavra: a mensagem utiliza essa palavra única como primeiro nome.
- Nome contendo múltiplos sobrenomes: a mensagem utiliza estritamente a primeira palavra.

**Fora de escopo:**
- Funcionalidade "Lembrar-me" com tempo estendido de expiração de cookie.
- Autenticação de dois fatores (2FA).

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/models.py` (`Cliente.check_password`), `apps/login_cadastro_app/views.py` (`login`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`LoginViewTest.test_login_sucesso_com_email_e_senha`)

---

### REQ-LOGIN-03 — Normalização de E-mail na Autenticação

**Descrição EARS:**  
WHEN the user submits an email address with mixed uppercase or leading/trailing whitespace to `/login/`, THE SYSTEM SHALL normalize the email string to lowercase and trimmed characters prior to executing the database lookup.

**Objetivo:**  
Permitir que o cliente efetue login com sucesso independentemente do uso de caracteres maiúsculos ou de espaços acidentais antes ou depois do e-mail.

**Ator:**  
Cliente cadastrado.

**Pré-condições:**
- O cliente possui cadastro prévio com e-mail já normalizado no banco de dados.

**Entradas:**
| Campo | Tipo | Valor |
|---|---|---|
| `email` | String | String com caracteres maiúsculos ou espaços nas extremidades (ex.: `"  ANA@EXAMPLE.COM  "`). |
| `password` | String | Senha correta do usuário. |

**Regras de negócio:**
1. O método `clean_email()` do `LoginForm` deve aplicar `email.lower().strip()`.
2. A view `login` deve reaplicar a normalização `email = email.lower().strip()` no e-mail obtido de `cleaned_data`.
3. A consulta de busca `Cliente.objects.get(email=email)` deve ser executada com o valor estritamente normalizado.

**Fluxo principal:**
1. O usuário digita `"  ANA@EXAMPLE.COM  "` e a senha correta e envia o formulário.
2. O formulário limpa e normaliza a string para `"ana@example.com"`.
3. A view busca `Cliente.objects.get(email="ana@example.com")` com êxito.
4. A senha é verificada e a sessão é iniciada com o e-mail `"ana@example.com"`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Login concluído com sucesso e redirecionamento para `/alterar_dados/`.

**Persistência:**
- Nenhuma alteração no modelo de dados.

**Critérios de aceitação:**
- GIVEN um cliente registrado com e-mail `"ana@example.com"` e senha `"senhaCerta123"`
  WHEN enviar POST para `/login/` com `email="ANA@EXAMPLE.COM"` e `password="senhaCerta123"`
  THEN o sistema deve autenticar com sucesso e redirecionar para `/alterar_dados/`
  AND a sessão deve registrar `cliente_email="ana@example.com"`.

**Casos-limite:**
- E-mail com espaços múltiplos no início e no final: todos os espaços das pontas devem ser eliminados.

**Fora de escopo:**
- Normalização de domínios com caracteres internacionais (IDN).

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/forms.py` (`LoginForm.clean_email`), `apps/login_cadastro_app/views.py` (`login`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`LoginViewTest.test_login_insensivel_a_maiusculas_email`)

---

### REQ-LOGIN-04 — Rejeição de Credenciais Inválidas ou Inexistentes

**Descrição EARS:**  
IF the submitted email does not exist in the `Cliente` database OR the password does not match the stored hash, THEN THE SYSTEM SHALL reject authentication, clear message storage, keep the user unauthenticated without session cookies, and re-render the login page with HTTP 200.

**Objetivo:**  
Impedir o acesso não autorizado de invasores ou usuários com dados incorretos, garantindo a segurança das contas.

**Ator:**  
Visitante ou usuário com dados incorretos.

**Pré-condições:**
- Requisição POST enviada para `/login/`.

**Entradas:**
| Campo | Tipo | Condição |
|---|---|---|
| `email` | String | E-mail não cadastrado na base de dados, OU |
| `password` | String | Senha não condizente com o hash armazenado. |

**Regras de negócio:**
1. Se a consulta `Cliente.objects.get(email=email)` disparar `Cliente.DoesNotExist`:
   - A view deve marcar as mensagens antigas como consumidas (`storage.used = True`);
   - A view não deve criar a chave `cliente_email` na sessão;
   - O template `login.html` deve ser re-renderizado com código HTTP 200 passando o formulário recebido.
2. Se o cliente for encontrado, porém `cliente.check_password(password)` retornar `False`:
   - A view deve marcar as mensagens antigas como consumidas (`storage.used = True`);
   - A view não deve criar a chave `cliente_email` na sessão;
   - O template `login.html` deve ser re-renderizado com código HTTP 200 passando o formulário recebido.
3. Se o formulário for inválido (campos vazios ou formato inválido):
   - A view limpa as mensagens antigas e re-renderiza o formulário com HTTP 200 exibindo os erros dos campos.
4. DECISÃO PENDENTE: No código atual da view `login`, quando a busca por e-mail falha (`Cliente.DoesNotExist`) ou a senha está incorreta, nenhuma mensagem de erro explícita (como "E-mail ou senha incorretos") é adicionada ao `messages` ou ao formulário; a view apenas limpa as mensagens e re-renderiza o template. Definir se deve ser exibida a mensagem amigável de erro "E-mail ou senha inválidos" para o usuário.

**Fluxo principal:**
1. O usuário submete credenciais erradas via POST para `/login/`.
2. A view verifica a ausência do cliente ou a divergência do hash da senha.
3. A view limpa o storage de mensagens.
4. A view re-renderiza `login.html` com código HTTP 200.
5. O usuário permanece sem autenticação e sem chave `cliente_email` na sessão.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Resposta HTTP 200 com a página de login.
- Nenhuma sessão criada em `request.session`.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um cliente cadastrado com `email="ana@example.com"` e senha `"senhaCerta123"`
  WHEN submeter POST com `email="ana@example.com"` e `password="senhaErrada"`
  THEN o código HTTP de resposta deve ser 200
  AND a chave `cliente_email` não deve constar em `request.session`.
- GIVEN que o e-mail `"naoexiste@example.com"` não está cadastrado
  WHEN submeter POST com esse e-mail e qualquer senha
  THEN o código HTTP de resposta deve ser 200
  AND a chave `cliente_email` não deve constar em `request.session`.

**Casos-limite:**
- Submissão com strings de ataque de SQL Injection ou tamanhos excessivos: tratadas de forma segura pelo ORM do Django.

**Fora de escopo:**
- Bloqueio temporário de conta após N tentativas falhas (rate limiting / brute force protection).

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/views.py` (`login`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- Testes existentes: `apps/login_cadastro_app/tests.py` (`LoginViewTest.test_login_senha_incorreta`, `LoginViewTest.test_login_email_inexistente`)

---

### REQ-LOGIN-05 — Alternância de Visibilidade da Senha na Interface de Login

**Descrição EARS:**  
WHEN the user clicks the password toggle button on the login form, THE SYSTEM SHALL alternate the password input field type between `password` and `text`, toggling the open-eye and slash-eye icon display.

**Objetivo:**  
Permitir que o usuário inspecione a senha digitada no formulário de login antes de submeter a requisição.

**Ator:**  
Visitante ou cliente.

**Pré-condições:**
- A página de login está carregada no navegador com JavaScript habilitado.

**Entradas:**
| Elemento | Evento | Ação |
|---|---|---|
| `#togglePassword` | `click` | Inverte o tipo do elemento `#id_password`. |

**Regras de negócio:**
1. O clique não deve disparar o envio do formulário (`e.preventDefault()`).
2. Se o campo de senha possuir `type="password"`, ele deve ser alterado para `type="text"`:
   - `#eye-slash` recebe estilo `display = 'block'`;
   - `#eye-open` recebe estilo `opacity = '0.3'`.
3. Se o campo de senha possuir `type="text"`, ele deve retornar para `type="password"`:
   - `#eye-slash` recebe estilo `display = 'none'`;
   - `#eye-open` recebe estilo `opacity = '1'`.

**Fluxo principal:**
1. O usuário clica no botão com ícone de olho no campo de senha.
2. O script inline de `login.html` intercepta o evento.
3. O tipo do input é alternado para `text`.
4. Os caracteres da senha tornam-se legíveis na tela.
5. Um novo clique restaura o tipo `password`, ocultando os caracteres.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Alternância imediata da visibilidade do texto da senha na tela.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN que o campo `#id_password` está com `type="password"`
  WHEN o botão `#togglePassword` for clicado
  THEN o atributo `type` de `#id_password` deve se tornar `"text"`.
- GIVEN que o campo `#id_password` está com `type="text"`
  WHEN o botão `#togglePassword` for clicado
  THEN o atributo `type` de `#id_password` deve retornar a `"password"`.

**Casos-limite:**
- Clique sem texto digitado no campo: o comportamento visual é executado sem erros de script.

**Fora de escopo:**
- Ocultação temporizada automática após N segundos.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/templates/login_cadastro_app/login.html` (script embutido)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-LOGIN-06 — Validação em Tempo Real de E-mail no Formulário de Login

**Descrição EARS:**  
WHILE the user is editing the email field on the login form, THE SYSTEM SHALL validate on `blur` whether the content matches standard email regex format (`/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/`) and apply `valid` or `invalid` CSS classes to the enclosing form group.

**Objetivo:**  
Orientar visualmente o usuário quanto à formatação sintática correta do e-mail no login antes da submissão do formulário.

**Ator:**  
Visitante ou cliente.

**Pré-condições:**
- A página de login está carregada no navegador com JavaScript habilitado.

**Entradas:**
| Elemento | Evento | Expressão Regular |
|---|---|---|
| `#id_email` | `blur` | `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` |

**Regras de negócio:**
1. Ao retirar o foco (`blur`) do campo `#id_email`:
   - Se o valor for vazio, as classes `valid` e `invalid` devem ser removidas do `.form-group`.
   - Se o valor for preenchido e casar com a expressão regular, adiciona a classe `valid` e remove `invalid`.
   - Se o valor for preenchido e não casar com a expressão regular, adiciona a classe `invalid` e remove `valid`.
2. Ao receber foco (`focus`), o `.form-group` recebe a classe `focused`. Ao perder foco (`blur`), a classe `focused` é removida.
3. Ao submeter o formulário (`submit`), o botão `.btn-submit` recebe a classe `loading` e a propriedade `disabled = true`.

**Fluxo principal:**
1. O usuário digita o e-mail no campo correspondente.
2. O usuário clica fora do campo ou pressiona Tab.
3. O script valida o formato do texto inserido.
4. A classe visual adequada é atribuída ao elemento pai.

**Fluxos alternativos e de erro:**
- Usuário com JavaScript desabilitado: a validação visual não é acionada; a validação ocorre no backend durante o POST.

**Resultado esperado:**
- Atualização dinâmica da estilização visual da borda do campo de e-mail.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN que o usuário digita `"email_invalido"` no campo `#id_email`
  WHEN disparar o evento `blur`
  THEN o elemento pai `.form-group` deve possuir a classe `invalid`.
- GIVEN que o usuário digita `"usuario@exemplo.com"` no campo `#id_email`
  WHEN disparar o evento `blur`
  THEN o elemento pai `.form-group` deve possuir a classe `valid`.

**Casos-limite:**
- Campo esvaziado pelo usuário: o sistema retira ambas as classes `valid` e `invalid`.

**Fora de escopo:**
- Verificação assíncrona prévia se o e-mail existe no banco durante o preenchimento.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/templates/login_cadastro_app/login.html` (script embutido)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-LOGIN-07 — Encerramento de Sessão (Logout)

**Descrição EARS:**  
WHEN the user accesses the URL `/logout/` via HTTP GET, IF `cliente_email` exists in the session, THEN THE SYSTEM SHALL delete `cliente_email` from `request.session`, issue a success flash message ("Logout realizado com sucesso!"), and redirect the user to `/`; OTHERWISE, THE SYSTEM SHALL emit an info flash message ("Você não estava logado.") and redirect to `/`.

**Objetivo:**  
Encerrar a sessão autenticada do cliente de forma segura, removendo suas credenciais de sessão ativas e retornando-o à página inicial pública.

**Ator:**  
Cliente autenticado ou visitante anônimo.

**Pré-condições:**
- Acesso à rota `/logout/`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. A rota `/logout/` deve responder a requisições HTTP GET.
2. O sistema deve verificar a existência da chave `'cliente_email'` no dicionário `request.session`.
3. Caso a chave `'cliente_email'` exista:
   - O item deve ser removido da sessão (`del request.session['cliente_email']`);
   - Deve ser registrada uma mensagem de sucesso no framework de mensagens: `"Logout realizado com sucesso!"`;
   - O sistema deve redirecionar com HTTP 302 para a rota `index` (`/`).
4. Caso a chave `'cliente_email'` não exista:
   - Deve ser registrada uma mensagem informativa no framework de mensagens: `"Você não estava logado."`;
   - O sistema deve redirecionar com HTTP 302 para a rota `index` (`/`).

**Fluxo principal:**
1. O cliente autenticado clica no link de logout ou requisita `/logout/` via HTTP GET.
2. A view `logout_view` localiza a chave `'cliente_email'` na sessão.
3. A view exclui a chave `'cliente_email'`.
4. A mensagem de sucesso `"Logout realizado com sucesso!"` é adicionada ao storage de mensagens.
5. O sistema emite resposta de redirecionamento HTTP 302 para `/`.

**Fluxos alternativos e de erro:**
- **Usuário não logado requisita `/logout/`:**
  1. A view `logout_view` detecta que `'cliente_email'` não está em `request.session`.
  2. Adiciona a mensagem informativa `"Você não estava logado."`.
  3. Redireciona com HTTP 302 para a rota `index` (`/`).

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/`.
- Sessão do usuário desprovida do atributo `cliente_email`.
- Notificação de logout exibida na página inicial.

**Persistência:**
- Atualização ou purga da sessão no mecanismo de armazenamento de sessões do Django. Nenhuma alteração nos registros de `Cliente`.

**Critérios de aceitação:**
- GIVEN que uma sessão contém `cliente_email="cliente@exemplo.com"`
  WHEN o usuário enviar requisição GET para `/logout/`
  THEN o sistema deve redirecionar para `/` com HTTP 302
  AND a chave `cliente_email` não deve mais existir na sessão
  AND a mensagem `"Logout realizado com sucesso!"` deve ser adicionada.
- GIVEN que não há usuário logado na sessão
  WHEN enviar requisição GET para `/logout/`
  THEN o sistema deve redirecionar para `/` com HTTP 302
  AND a mensagem `"Você não estava logado."` deve ser adicionada.

**Casos-limite:**
- Requisições repetidas de logout em sequência: a primeira executa o fluxo principal e as subsequentes executam o fluxo alternativo sem erros.

**Fora de escopo:**
- Invalidação de tokens OAuth ou encerramento de sessões em outros dispositivos simultâneos.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/urls.py`, `apps/login_cadastro_app/views.py` (`logout_view`)
- Template/JS: `apps/login_cadastro_app/templates/login_cadastro_app/index.html`
- Testes existentes: Não coberto por teste automatizado
