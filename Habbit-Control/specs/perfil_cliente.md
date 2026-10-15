# Especificação: Perfil do Cliente

## Visão Geral do Módulo
O módulo de perfil do cliente permite a visualização e atualização dos dados cadastrais do cliente autenticado. A interface provê edição em linha (*inline editing*) via JavaScript, comunicando-se com a API assíncrona `/api/cliente/update/` com controle de permissões por lista branca (*whitelist*), proteção contra CSRF e validação de sessão ativa.

---

## Requisitos do Sistema

### REQ-PERFIL-01 — Controle de Acesso e Validação de Sessão

**Descrição EARS:**  
WHEN an unauthenticated user requests `/alterar_dados/` without a valid `cliente_email` session key (or if the session email no longer exists in the database), THE SYSTEM SHALL purge `cliente_email` from `request.session`, register a warning flash message ("Por favor, faça login para acessar esta página."), and redirect the request to `/login/`.

**Objetivo:**  
Garantir que apenas usuários com sessão ativa válida e registro existente no banco de dados possam acessar a página de perfil.

**Ator:**  
Visitante ou usuário com sessão expirada/inválida.

**Pré-condições:**
- Requisição HTTP GET para `/alterar_dados/`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Cookie `sessionid` | String | Não | Pode estar ausente ou conter sessão sem `cliente_email`. |

**Regras de negócio:**
1. A função auxiliar `get_cliente_from_session(request)` deve inspecionar `request.session.get('cliente_email')`.
2. Se o e-mail não estiver na sessão:
   - A função retorna `None, None`;
   - A view registra mensagem de aviso: `"Por favor, faça login para acessar esta página."`;
   - O sistema responde com redirecionamento HTTP 302 para a rota `login` (`/login/`).
3. Se o e-mail estiver na sessão, mas a consulta `Cliente.objects.filter(email=cliente_email).first()` retornar nula:
   - A chave `cliente_email` deve ser purgada da sessão via `del request.session['cliente_email']`;
   - A view registra mensagem de aviso: `"Por favor, faça login para acessar esta página."`;
   - O sistema responde com redirecionamento HTTP 302 para `/login/`.
4. Se ocorrer qualquer falha inesperada na recuperação do cliente:
   - A view registra mensagem de erro: `"Erro ao carregar seus dados. Por favor, tente novamente."`;
   - O sistema redireciona com HTTP 302 para `/login/`.

**Fluxo principal:**
1. Um usuário não autenticado tenta acessar `/alterar_dados/`.
2. A view `alterar_dados` executa `get_cliente_from_session`.
3. A ausência de credencial válida na sessão é detectada.
4. A mensagem de aviso `"Por favor, faça login para acessar esta página."` é enfileirada.
5. O sistema emite resposta HTTP 302 direcionando o navegador para `/login/`.

**Fluxos alternativos e de erro:**
- **Cliente excluído do banco com sessão ainda aberta no navegador:**
  1. A view localiza o e-mail na sessão, porém a busca no banco retorna vazio.
  2. A view remove o e-mail da sessão (`del request.session['cliente_email']`).
  3. Adiciona a mensagem de aviso e redireciona para `/login/`.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/login/`.
- Notificação de aviso enfileirada no framework de mensagens.

**Persistência:**
- Remoção da chave de sessão em caso de e-mail órfão. Nenhuma alteração no modelo `Cliente`.

**Critérios de aceitação:**
- GIVEN que não há sessão ativa
  WHEN enviar requisição GET para `/alterar_dados/`
  THEN o código HTTP retornado deve ser 302 com destino para `/login/`
  AND deve ser registrada a mensagem `"Por favor, faça login para acessar esta página."`.
- GIVEN que a sessão contém `cliente_email="removido@exemplo.com"` e o registro correspondente não existe no banco
  WHEN enviar requisição GET para `/alterar_dados/`
  THEN a chave `cliente_email` deve ser excluída de `request.session`
  AND o sistema deve redirecionar com HTTP 302 para `/login/`.

**Casos-limite:**
- Sessão corrompida: capturada pelo bloco `except Exception` da view, redirecionando para `/login/` com a mensagem `"Erro ao carregar seus dados. Por favor, tente novamente."`.

**Fora de escopo:**
- Armazenamento de rota de retorno (*next parameter*) para retorno automático pós-login.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`get_cliente_from_session`, `alterar_dados`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/alterar_dados_cliente.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-PERFIL-02 — Renderização da Interface do Perfil

**Descrição EARS:**  
WHEN an authenticated client accesses `/alterar_dados/` via HTTP GET, THE SYSTEM SHALL load the `Cliente` object corresponding to the active session and render the `alterar_dados_cliente.html` template with HTTP 200, presenting the user's information organized into Dados Pessoais, Localização, and Conta e Segurança (with password masked as `********`).

**Objetivo:**  
Apresentar ao cliente autenticado seus dados cadastrais vigentes de forma clara, estruturada e protegida.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente possui sessão ativa válida associada a seu e-mail cadastrado.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. A rota `/alterar_dados/` deve responder a requisições GET com status HTTP 200 para clientes autenticados.
2. A tela deve apresentar os dados agrupados em três seções estruturadas:
   - **Dados Pessoais:** `nome_completo`, `idade`, `profissao`;
   - **Localização:** `cidade`, `estado`;
   - **Conta e Segurança:** `email`, `password` (exibida estritamente mascarada como `********`).
3. A senha armazenada no banco de dados nunca deve ser transmitida para o template em texto plano nem em formato hash. O valor renderizado para o campo senha deve ser estaticamente `"********"`.
4. Os campos `nome_completo`, `idade`, `profissao`, `email` e `senha` devem conter o elemento de gatilho de edição (`.edit-icon`).
5. DECISÃO PENDENTE: No template `alterar_dados_cliente.html`, os campos `Cidade` e `Estado` contêm a classe CSS `editable`, porém não possuem o elemento visual `<svg class="edit-icon">`. Como o script `edit_profile.js` requer o `.edit-icon` para associar o ouvinte de clique, Cidade e Estado não podem ser editados na interface atual. Definir se o ícone de edição deve ser adicionado a esses campos no template ou se a classe `editable` deve ser removida deles.

**Fluxo principal:**
1. O cliente autenticado requisita `/alterar_dados/` via HTTP GET.
2. A view recupera o objeto `Cliente` do banco de dados pelo e-mail na sessão.
3. A view renderiza `alterar_dados_cliente.html` passando `{'cliente': cliente}` no contexto.
4. O navegador exibe os cartões com os dados do cliente e a senha mascarada com asteriscos.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Página HTML carregada com status HTTP 200 contendo as três seções informativas.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um cliente autenticado com `nome_completo="Carlos Pereira"`, `idade=40` e `email="carlos@gmail.com"`
  WHEN enviar requisição GET para `/alterar_dados/`
  THEN o código de status HTTP retornado deve ser 200
  AND a resposta deve conter `"Carlos Pereira"`, `"40"`, `"carlos@gmail.com"`
  AND o valor visual exibido para a senha deve ser estritamente `"********"`.

**Casos-limite:**
- Campos opcionais nulos ou em branco no banco (ex.: profissão nula): renderizados como vazio sem interrupção do carregamento da página.

**Fora de escopo:**
- Upload de foto de perfil ou avatar.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`alterar_dados`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/alterar_dados_cliente.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-PERFIL-03 — Edição em Linha no Frontend (*Inline Editing*)

**Descrição EARS:**  
WHEN the user clicks the edit icon next to an editable field on the profile page, THE SYSTEM SHALL replace the static text with an inline input element matching the data type (`text`, `number` for idade, `email` for email, or `password` with an eye toggle for senha), allowing the user to submit on `blur` or `Enter`, or cancel changes on `Escape`.

**Objetivo:**  
Prover uma experiência interativa e ágil de modificação de dados cadastrais diretamente na interface do perfil, sem necessidade de redirecionamento para telas intermediárias.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Página de perfil carregada com o script `edit_profile.js` ativo.

**Entradas:**
| Campo | Tipo do Input Gerado | Comportamento ao Abrir |
|---|---|---|
| Nome Completo | `type="text"` | Recebe o texto atual em exibição. |
| Idade | `type="number"` | Recebe o número atual em exibição. |
| Profissão | `type="text"` | Recebe o texto atual em exibição. |
| Email | `type="email"` | Recebe o e-mail atual em exibição. |
| Senha | `type="password"` | Inicia com valor vazio `""` e placeholder `"Digite a nova senha"`. Acompanhado de botão com ícone de olho para alternância de visibilidade. |

**Regras de negócio:**
1. Ao clicar no elemento `.edit-icon`, se o campo já estiver em modo de edição, deve acionar o salvamento; caso contrário, deve ativar o modo de edição.
2. O elemento estático `.field-value` deve ser substituído dinamicamente pelo container com o input correspondente (`.input-container`).
3. O input gerado deve receber foco automático imediato (`focus()`).
4. Ao pressionar a tecla `Enter`, o sistema deve acionar o salvamento do campo (`saveField`).
5. Ao pressionar a tecla `Escape`, a edição deve ser cancelada (`cancelEdit`), restaurando o valor original exibido antes da abertura do campo.
6. Ao disparar o evento `blur` (perda de foco), o salvamento deve ser acionado após um atraso (*delay*) de 150 milissegundos.
7. Para o campo de senha:
   - Se o valor digitado for vazio `""`, a edição deve ser cancelada e o texto restaurado para `"********"`, sem emitir requisição de rede para a API.
   - O ícone de olho permite alternar o atributo `type` entre `"password"` e `"text"`. O evento `mousedown` do olho deve executar `e.preventDefault()` para evitar perda de foco prematura do input.
8. Ao concluir o salvamento:
   - O input deve ser substituído por um elemento `span.field-value` com o novo texto;
   - Para o campo de senha, o novo texto exibido deve ser sempre formatado como `"********"`.

**Fluxo principal:**
1. O usuário clica no ícone de lápis ao lado do seu nome.
2. O texto estático é substituído por um `<input type="text">` focado com o nome atual.
3. O usuário altera o texto e pressiona `Enter`.
4. O script restaura o elemento `span.field-value` com o novo valor e dispara a requisição assíncrona para `/api/cliente/update/`.

**Fluxos alternativos e de erro:**
- **Cancelamento via teclado:** O usuário pressiona `Escape`. O input é removido e o valor prévio é restaurado sem qualquer requisição à API.
- **Senha em branco:** O usuário abre a edição da senha, não digita nada e clica fora. O script detecta string vazia, cancela a operação e restaura `"********"`.

**Resultado esperado:**
- Campo atualizado na interface visual com transição de cor indicativa: verde (`#27AE60`) em caso de resposta positiva da API ou vermelho (`#E74C3C`) em caso de falha.

**Persistência:**
- Nenhuma alteração direta no banco até a conclusão da chamada à API (REQ-PERFIL-04).

**Critérios de aceitação:**
- GIVEN que o usuário está na tela de perfil
  WHEN clicar no ícone de edição da idade
  THEN um input de tipo `number` deve ser exibido com o valor atual
  AND ao pressionar `Escape`, o input deve ser substituído pelo valor anterior original.
- GIVEN que o usuário abre a edição de senha
  WHEN deixar o campo vazio e retirar o foco
  THEN o campo deve retornar ao valor `"********"` sem realizar chamada HTTP.

**Casos-limite:**
- Clique rápido fora do campo enquanto o script de salvamento processa: o delay de 150ms assegura que o evento não duplique requisições.

**Fora de escopo:**
- Reversão com botão de desfazer (*undo*) global na tela.

**Rastreabilidade:**
- Implementação: `static/login_cadastro_app/js/edit_profile.js`
- Template/JS: `apps/pagina_interna/templates/pagina_interna/alterar_dados_cliente.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-PERFIL-04 — Atualização de Dados via API Assíncrona

**Descrição EARS:**  
WHEN the frontend submits an asynchronous HTTP POST request to `/api/cliente/update/` containing a valid CSRF token, authenticated session, and JSON payload with `field` and `value`, IF the specified `field` belongs to the allowed whitelist (`nome_completo`, `idade`, `email`, `password`, `cidade`, `pais`, `profissao`), THEN THE SYSTEM SHALL assign the value to the `Cliente` model, execute `cliente.save()`, and respond with HTTP 200 JSON `{"success": true, "message": "Dados atualizados com sucesso"}`.

**Objetivo:**  
Processar a gravação no banco de dados de alterações cadastrais unitárias enviadas pela interface de perfil de forma assíncrona.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Sessão ativa com chave `cliente_email` válida.
- Token CSRF presente no cabeçalho `X-CSRFToken`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `field` | String | Sim | Deve pertencer à lista branca: `'nome_completo'`, `'idade'`, `'email'`, `'password'`, `'cidade'`, `'pais'`, `'profissao'`. |
| `value` | Qualquer (string/número) | Sim | Não pode ser nulo (`None`). Pode ser string vazia para campos que permitem vazio, exceto senha. |

**Regras de negócio:**
1. A rota `/api/cliente/update/` aceita estritamente o método HTTP POST (decorada com `@require_POST`). Requisições com outros métodos devem ser rejeitadas pelo Django com HTTP 405 Method Not Allowed.
2. O corpo da requisição deve ser interpretado como JSON via `json.loads(request.body)`. Se o corpo não for um JSON bem-formado, o sistema responde com HTTP 400 e `{"success": false, "error": "JSON inválido"}`.
3. Se `field` for vazio ou `value` for nulo (`value is None`), o sistema responde com HTTP 400 e `{"success": false, "error": "Campo ou valor inválido"}`.
4. Se o usuário não estiver autenticado na sessão (`get_cliente_from_session` retornar nulo), o sistema responde com HTTP 401 e `{"success": false, "error": "Usuário não autenticado. Faça login novamente."}`.
5. O mapeamento de campos permitidos (`field_map`) é estritamente:
   - `'nome_completo'` -> `'nome_completo'`
   - `'idade'` -> `'idade'`
   - `'email'` -> `'email'`
   - `'password'` -> `'password'`
   - `'cidade'` -> `'cidade'`
   - `'pais'` -> `'pais'`
   - `'profissao'` -> `'profissao'`
6. Caso o campo não conste no `field_map`, a requisição é rejeitada conforme REQ-PERFIL-06.
7. Caso o campo seja diferente de `'password'`, o sistema executa `setattr(cliente, model_field, value)`.
8. O método `cliente.save()` deve ser invocado, garantindo que o método `save()` do modelo execute a normalização de e-mail e o hash de senha necessários.
9. Em caso de sucesso, o sistema deve retornar status HTTP 200 com JSON:
   ```json
   {"success": true, "message": "Dados atualizados com sucesso"}
   ```
10. Em caso de erro interno não tratado, o sistema captura a exceção e retorna HTTP 500 com `{"success": false, "error": "<mensagem do erro>"}`.
11. NOTA TÉCNICA / DECISÃO PENDENTE:
    - O campo `'pais'` consta na lista branca da view, mas o modelo `Cliente` não possui coluna `pais` no banco de dados. Ao receber esse campo, `setattr` cria um atributo transitório em memória e `cliente.save()` não persiste a informação em tabela. Definir se a coluna `pais` deve ser criada no modelo `Cliente` ou se `'pais'` deve ser substituído por `'estado'` no `field_map`.
    - O campo `'estado'` existe no modelo `Cliente`, porém não está no `field_map`, impossibilitando sua atualização pela API.

**Fluxo principal:**
1. O frontend envia requisição POST para `/api/cliente/update/` com headers `Content-Type: application/json` e `X-CSRFToken: <token>` e payload `{"field": "nome_completo", "value": "Gabriel Silva"}`.
2. A view valida a sessão ativa e localiza o cliente.
3. O campo `"nome_completo"` é validado na lista branca.
4. `setattr(cliente, 'nome_completo', 'Gabriel Silva')` atualiza o objeto.
5. `cliente.save()` persiste a alteração no banco de dados.
6. A view retorna status HTTP 200 com JSON de confirmação.

**Fluxos alternativos e de erro:**
- **Sessão inexistente ou expirada:** A view retorna HTTP 401 com `{"success": false, "error": "Usuário não autenticado. Faça login novamente."}`.
- **JSON malformado no corpo:** A view captura `json.JSONDecodeError` e retorna HTTP 400 com `{"success": false, "error": "JSON inválido"}`.
- **Exceção de banco de dados (ex.: duplicidade ao alterar e-mail para um já existente):** Dispara `IntegrityError`, capturado pelo bloco genérico, retornando HTTP 500 com a mensagem de erro.

**Resultado esperado:**
- Resposta JSON HTTP 200 com confirmação de sucesso.
- Banco de dados atualizado com o novo valor do campo.

**Persistência:**
- Registro do cliente atualizado na tabela `login_cadastro_app_cliente`.

**Critérios de aceitação:**
- GIVEN um cliente autenticado na sessão
  WHEN enviar POST para `/api/cliente/update/` com payload `{"field": "profissao", "value": "Engenheiro de Software"}`
  THEN o código HTTP de retorno deve ser 200
  AND o corpo JSON deve conter `{"success": true, "message": "Dados atualizados com sucesso"}`
  AND a consulta ao banco deve confirmar que `cliente.profissao` é igual a `"Engenheiro de Software"`.
- GIVEN uma requisição sem sessão de autenticação ativa
  WHEN enviar POST para `/api/cliente/update/`
  THEN o status retornado deve ser HTTP 401
  AND o JSON deve conter `{"success": false, "error": "Usuário não autenticado. Faça login novamente."}`.

**Casos-limite:**
- Alteração do e-mail: `cliente.save()` executa normalização automática para minúsculas e remoção de espaços em branco antes de persistir.

**Fora de escopo:**
- Histórico ou auditoria de alterações cadastrais anteriores (versionamento de perfil).

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`update_cliente`)
- Template/JS: `static/login_cadastro_app/js/edit_profile.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-PERFIL-05 — Validação e Criptografia na Alteração de Senha

**Descrição EARS:**  
WHEN the user attempts to update the `password` field via `/api/cliente/update/`, IF the submitted `value` is empty, THEN THE SYSTEM SHALL reject the request with HTTP 400 and error message "A senha não pode ser vazia"; OTHERWISE, THE SYSTEM SHALL assign the new password to the client and invoke `cliente.save()` to hash and store the updated credential.

**Objetivo:**  
Garantir que a senha nunca seja redefinida para valor vazio e que novas senhas válidas sejam criptografadas com hash PBKDF2 SHA-256 no momento da persistência.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Requisição autenticada enviada para `/api/cliente/update/` com `field="password"`.

**Entradas:**
| Campo | Tipo | Valor |
|---|---|---|
| `field` | String | `"password"` |
| `value` | String | Nova senha desejada em texto plano. |

**Regras de negócio:**
1. Se o valor submetido para a senha for vazio, nulo ou string vazia (`not value`):
   - O sistema deve rejeitar a operação com código HTTP 400;
   - O corpo JSON deve ser exatamente: `{"success": false, "error": "A senha não pode ser vazia"}`.
2. Se a senha contiver caracteres:
   - A string é atribuída a `cliente.password = value`;
   - O método `cliente.save()` é disparado;
   - O método `save()` do modelo `Cliente` verifica que o valor não inicia com `pbkdf2_sha256$` e aplica `make_password(self.password)`;
   - O hash seguro PBKDF2 SHA-256 é persistido no banco de dados;
   - A resposta deve ter código HTTP 200 com `{"success": true, "message": "Dados atualizados com sucesso"}`.
3. DECISÃO PENDENTE: Não há validação de comprimento mínimo de senha ou complexidade de caracteres na view `update_cliente`. Qualquer string não vazia (ex.: `"1"`) é aceita e criptografada. Definir se as regras do `AUTH_PASSWORD_VALIDATORS` do Django devem ser aplicadas na alteração de senha pela API.

**Fluxo principal:**
1. O cliente digita `"novaSenhaSegura@2026"` no input de senha da tela de perfil e confirma.
2. O frontend envia POST com `{"field": "password", "value": "novaSenhaSegura@2026"}`.
3. A view valida que `value` não é vazio.
4. A view atribui a senha e chama `cliente.save()`.
5. O modelo gera o hash `pbkdf2_sha256$...`.
6. A view responde com HTTP 200 e confirmação de sucesso.
7. O cliente passa a se autenticar exclusivamente com a nova senha.

**Fluxos alternativos e de erro:**
- **Submissão com senha vazia:**
  1. A view detecta `not value`.
  2. Retorna imediatamente HTTP 400 com `{"success": false, "error": "A senha não pode ser vazia"}`.
  3. A senha anterior do cliente permanece inalterada no banco de dados.

**Resultado esperado:**
- Senha criptografada e salva no banco de dados com resposta HTTP 200; ou rejeição com HTTP 400 se vazia.

**Persistência:**
- Coluna `password` do registro do cliente atualizada com o novo hash PBKDF2 SHA-256.

**Critérios de aceitação:**
- GIVEN um cliente autenticado
  WHEN enviar POST para `/api/cliente/update/` com `{"field": "password", "value": ""}`
  THEN o código de resposta deve ser 400
  AND o corpo JSON deve conter `{"success": false, "error": "A senha não pode ser vazia"}`.
- GIVEN um cliente autenticado com senha antiga
  WHEN enviar POST para `/api/cliente/update/` com `{"field": "password", "value": "novaSenha@123"}`
  THEN o código de resposta deve ser 200
  AND `cliente.check_password("novaSenha@123")` deve retornar `True`
  AND `cliente.check_password("senhaAntiga")` deve retornar `False`.

**Casos-limite:**
- Senha com espaços nas extremidades: preservada como digitada e hasheada (senhas não são trimadas).

**Fora de escopo:**
- Exigência da digitação da senha atual como confirmação prévia para autorizar a troca.

**Rastreabilidade:**
- Implementação: `apps/login_cadastro_app/models.py` (`Cliente.save`, `Cliente.check_password`), `apps/pagina_interna/views.py` (`update_cliente`)
- Template/JS: `static/login_cadastro_app/js/edit_profile.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-PERFIL-06 — Rejeição de Campos Fora da Lista Branca (*Whitelist*)

**Descrição EARS:**  
IF an HTTP POST request to `/api/cliente/update/` sends a `field` not present in the allowed whitelist, THEN THE SYSTEM SHALL reject the operation with HTTP 400 and JSON error `{"success": false, "error": "Campo <field> não permitido"}`.

**Objetivo:**  
Proteger a integridade e segurança do modelo contra ataques de atribuição em massa (*mass assignment*) ou manipulação de campos protegidos (como identificador primário, metadados de criação ou consentimento LGPD).

**Ator:**  
Cliente autenticado ou agente externo.

**Pré-condições:**
- Requisição POST enviada para `/api/cliente/update/`.

**Entradas:**
| Campo | Tipo | Valor |
|---|---|---|
| `field` | String | Qualquer identificador não contido em `['nome_completo', 'idade', 'email', 'password', 'cidade', 'pais', 'profissao']` (ex.: `'id'`, `'data_criacao'`, `'lgpd'`, `'is_superuser'`, `'estado'`). |
| `value` | Qualquer | Qualquer valor enviado. |

**Regras de negócio:**
1. Apenas os campos explicitamente mapeados no dicionário `field_map` da view `update_cliente` são permitidos:
   - `nome_completo`, `idade`, `email`, `password`, `cidade`, `pais`, `profissao`.
2. Se o valor recebido na chave `field` não for uma chave do `field_map`:
   - A operação de gravação deve ser bloqueada;
   - O sistema deve retornar status HTTP 400;
   - A resposta JSON deve ser: `{"success": false, "error": f"Campo {field} não permitido"}`.

**Fluxo principal:**
1. Um cliente envia POST com `{"field": "lgpd", "value": false}` para `/api/cliente/update/`.
2. A view verifica que `'lgpd'` não está presente em `field_map`.
3. A view interrompe o fluxo imediatamente.
4. O sistema retorna HTTP 400 com `{"success": false, "error": "Campo lgpd não permitido"}`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Resposta HTTP 400 com mensagem de erro informando o campo não permitido.
- Nenhum atributo do modelo alterado no banco de dados.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um cliente autenticado
  WHEN enviar POST para `/api/cliente/update/` com `{"field": "data_criacao", "value": "2020-01-01"}`
  THEN o código HTTP de resposta deve ser 400
  AND o JSON deve ser exatamente `{"success": false, "error": "Campo data_criacao não permitido"}`.
- GIVEN um cliente autenticado
  WHEN enviar POST para `/api/cliente/update/` com `{"field": "estado", "value": "RJ"}`
  THEN o código HTTP de resposta deve ser 400
  AND o JSON deve ser `{"success": false, "error": "Campo estado não permitido"}`.

**Casos-limite:**
- Nomes de campos com caracteres especiais ou strings longas: rejeitados de forma idêntica com HTTP 400.

**Fora de escopo:**
- Tentativa de exploração automatizada com bloqueio de IP.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/views.py` (`update_cliente`)
- Template/JS: `static/login_cadastro_app/js/edit_profile.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-PERFIL-07 — Rotas de Garantia (*Stubs* / Funcionalidade Incompleta)

**Descrição EARS:**  
WHEN an authenticated user requests `/cadastro_garantia/` or `/consultar_garantia/` via HTTP GET, THE SYSTEM SHALL issue an informational flash message indicating that warranty registration or consultation is currently unavailable ("A funcionalidade de cadastro/consulta de garantia não está disponível no momento.") and redirect the user back to `/alterar_dados/`.

**Objetivo:**  
Documentar formalmente o comportamento das rotas legadas ou em espera (*stubs*) de garantia, garantindo que o usuário seja avisado sobre a indisponibilidade e reconduzido com segurança à página de perfil.

**Ator:**  
Cliente autenticado ou visitante.

**Pré-condições:**
- Acesso às rotas `/cadastro_garantia/` ou `/consultar_garantia/` via HTTP GET.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. Se a requisição for feita por usuário não autenticado:
   - O sistema enfileira a mensagem de aviso `"Por favor, faça login para acessar esta página."`;
   - O sistema redireciona com HTTP 302 para `/login/`.
2. Se a requisição for feita por cliente autenticado para `/cadastro_garantia/`:
   - O sistema enfileira a mensagem informativa via `messages.info`: `"A funcionalidade de cadastro de garantia não está disponível no momento."`;
   - O sistema responde com redirecionamento HTTP 302 para `/alterar_dados/`.
3. Se a requisição for feita por cliente autenticado para `/consultar_garantia/`:
   - O sistema enfileira a mensagem informativa via `messages.info`: `"A funcionalidade de consulta de garantia não está disponível no momento."`;
   - O sistema responde com redirecionamento HTTP 302 para `/alterar_dados/`.
4. Não existem modelos, formulários ou tabelas de banco de dados para a funcionalidade de garantia no sistema.

**Fluxo principal:**
1. O cliente autenticado clica em um link de garantia ou digita a URL `/cadastro_garantia/`.
2. A view `cadastro_garantia` valida a autenticação na sessão com sucesso.
3. A view registra a mensagem informativa no framework de mensagens.
4. O sistema retorna HTTP 302 redirecionando para `/alterar_dados/`.
5. A página de perfil é renderizada exibindo a notificação informativa.

**Fluxos alternativos e de erro:**
- **Usuário deslogado requisita a rota:**
  1. A validação de sessão em `get_cliente_from_session` falha.
  2. Mensagem de aviso enfileirada.
  3. Redirecionamento HTTP 302 para `/login/`.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/alterar_dados/` acompanhado de mensagem informativa; ou para `/login/` se não logado.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um cliente com sessão ativa
  WHEN enviar requisição GET para `/cadastro_garantia/`
  THEN o código HTTP retornado deve ser 302 com destino para `/alterar_dados/`
  AND deve ser registrada a mensagem informativa `"A funcionalidade de cadastro de garantia não está disponível no momento."`.
- GIVEN um cliente com sessão ativa
  WHEN enviar requisição GET para `/consultar_garantia/`
  THEN o código HTTP retornado deve ser 302 com destino para `/alterar_dados/`
  AND deve ser registrada a mensagem informativa `"A funcionalidade de consulta de garantia não está disponível no momento."`.

**Casos-limite:**
- Requisição por métodos POST/PUT/DELETE: a view executa a mesma lógica e redireciona para `/alterar_dados/`.

**Fora de escopo:**
- Implementação de módulo de gerenciamento de termos de garantia, produtos ou notas fiscais.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`cadastro_garantia`, `consultar_garantia`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/alterar_dados_cliente.html`
- Testes existentes: Não coberto por teste automatizado
