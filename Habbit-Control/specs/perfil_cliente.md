# Perfil de Cliente

## Requisitos

### REQ-PERFIL-01
WHEN an unauthenticated user requests `/alterar_dados/` without a valid `cliente_email` session key (or if the session email no longer exists in the database), THE SYSTEM SHALL purge `cliente_email` from `request.session`, register a warning message ("Por favor, faça login para acessar esta página."), and redirect the request to `/login/`.

#### Rastreabilidade:
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`get_cliente_from_session`, `alterar_dados`)

---

### REQ-PERFIL-02
WHEN an authenticated client accesses `/alterar_dados/` via HTTP GET, THE SYSTEM SHALL load the `Cliente` object corresponding to the active session and render the `alterar_dados_cliente.html` template, presenting the user's information organized into Dados Pessoais (Nome Completo, Idade, Profissão), Localização (Cidade, Estado), and Conta e Segurança (Email, Senha mascarada com `********`).

#### Rastreabilidade:
- `apps/pagina_interna/views.py` (`alterar_dados`)
- `apps/pagina_interna/templates/pagina_interna/alterar_dados_cliente.html`

---

### REQ-PERFIL-03
WHEN the user clicks the edit icon next to an editable field on the profile page, THE SYSTEM SHALL replace the static text with an inline input element matching the data type (`text`, `number` for idade, `email` for email, or `password` with an eye toggle for senha), allowing the user to submit on blur or Enter, or cancel changes on Escape.

#### Rastreabilidade:
- `apps/pagina_interna/templates/pagina_interna/alterar_dados_cliente.html`
- `static/login_cadastro_app/js/edit_profile.js`

---

### REQ-PERFIL-04
WHEN the frontend submits an asynchronous HTTP POST request to `/api/cliente/update/` containing a valid CSRF token, authenticated session, and JSON payload with `field` and `value`, IF the specified `field` belongs to the allowed whitelist (`nome_completo`, `idade`, `email`, `password`, `cidade`, `pais`, `profissao`), THEN THE SYSTEM SHALL assign the value to the `Cliente` model, execute `cliente.save()`, and respond with HTTP 200 JSON `{"success": true, "message": "Dados atualizados com sucesso"}`.

#### Rastreabilidade:
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`update_cliente`)
- `static/login_cadastro_app/js/edit_profile.js`

---

### REQ-PERFIL-05
WHEN the user attempts to update the `password` field via `/api/cliente/update/`, IF the submitted `value` is empty, THEN THE SYSTEM SHALL reject the request with HTTP 400 and error message "A senha não pode ser vazia"; OTHERWISE, THE SYSTEM SHALL assign the new password to the client and invoke `cliente.save()` to hash and store the updated credential.

#### Rastreabilidade:
- `apps/login_cadastro_app/models.py` (`save`)
- `apps/pagina_interna/views.py` (`update_cliente`)
- `static/login_cadastro_app/js/edit_profile.js`

---

### REQ-PERFIL-06
IF an HTTP POST request to `/api/cliente/update/` sends a `field` not present in the allowed whitelist, THEN THE SYSTEM SHALL reject the operation with HTTP 400 and JSON error `{"success": false, "error": "Campo <field> não permitido"}`.

#### Rastreabilidade:
- `apps/pagina_interna/views.py` (`update_cliente`)

---

### REQ-PERFIL-07 (Funcionalidade Incompleta / Placeholder)
WHEN an authenticated user requests `/cadastro_garantia/` or `/consultar_garantia/` via HTTP GET, THE SYSTEM SHALL issue an informational flash message indicating that warranty registration or consultation is currently unavailable ("A funcionalidade de cadastro/consulta de garantia não está disponível no momento.") and redirect the user back to `/alterar_dados/`.

> [!NOTE]
> As rotas de garantia (`cadastro_garantia` e `consultar_garantia`) estão implementadas apenas como stubs/redirecionamentos com mensagem informativa no código atual, sem models ou formulários dedicados.

#### Rastreabilidade:
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`cadastro_garantia`, `consultar_garantia`)
