# Cadastro de Cliente

## Requisitos

### REQ-CAD-01
WHEN the user requests the URL `/cadastro/cliente/` via HTTP GET, THE SYSTEM SHALL render the client registration page displaying the form with fields for Nome Completo, Idade, Email, Senha, Estado, Cidade, Profissão, and LGPD acceptance checkbox.

#### Rastreabilidade:
- `apps/login_cadastro_app/urls.py`
- `apps/login_cadastro_app/views.py`
- `apps/login_cadastro_app/forms.py`
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `apps/login_cadastro_app/tests.py` (`test_get_cadastro_retorna_200`, `test_formulario_sem_campo_cpf`)

---

### REQ-CAD-02
WHEN the user submits valid registration data via HTTP POST with Nome Completo, Idade, Email, Senha, and accepted LGPD terms, THE SYSTEM SHALL persist a new `Cliente` record, hash the password using PBKDF2 SHA256, normalize the email (lowercase and trimmed), and redirect the user to the login route (`/login/`).

#### Rastreabilidade:
- `apps/login_cadastro_app/models.py`
- `apps/login_cadastro_app/forms.py`
- `apps/login_cadastro_app/views.py`
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `apps/login_cadastro_app/tests.py` (`test_criar_cliente_sem_cpf`, `test_post_cadastro_sucesso`)

---

### REQ-CAD-03
IF the user submits a registration request with an email address that already belongs to an existing `Cliente` (evaluated case-insensitively), THEN THE SYSTEM SHALL reject the registration, prevent creation of duplicate records, and display the error message: "Este email já está cadastrado. Por favor, use outro email ou faça login."

#### Rastreabilidade:
- `apps/login_cadastro_app/models.py`
- `apps/login_cadastro_app/forms.py`
- `apps/login_cadastro_app/views.py`
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `apps/login_cadastro_app/tests.py` (`test_email_unico_no_modelo`, `test_formulario_rejeita_email_duplicado`, `test_post_cadastro_email_duplicado`)

---

### REQ-CAD-04
WHILE the user is interacting with form inputs, THE SYSTEM SHALL validate in real-time on blur that the email follows a valid email regex format (`/^[^\s@]+@[^\s@]+\.[^\s@]+$/`) and that the age is a numeric integer between 0 and 150, toggling visual validation classes (`valid` or `invalid`) accordingly.

#### Rastreabilidade:
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `static/login_cadastro_app/js/masks.js`
- `apps/login_cadastro_app/tests.py` (`test_formulario_valido`)

---

### REQ-CAD-05
WHEN the user selects a Brazilian state from the Estado dropdown, THE SYSTEM SHALL dynamically populate the Cidade dropdown with the cities associated with that state and enable the Cidade select element.

#### Rastreabilidade:
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `static/login_cadastro_app/js/estados_cidades.js`

---

### REQ-CAD-06
WHEN the user clicks the toggle password button in the password input group, THE SYSTEM SHALL alternate the input type between `password` and `text` and update the eye icon visibility state.

#### Rastreabilidade:
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `static/login_cadastro_app/js/masks.js`

---

### REQ-CAD-07
IF the user submits the registration form without agreeing to the LGPD terms (`lgpd` checkbox unmarked), THEN THE SYSTEM SHALL reject form submission and display a validation error.

#### Rastreabilidade:
- `apps/login_cadastro_app/models.py`
- `apps/login_cadastro_app/forms.py`
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `apps/login_cadastro_app/tests.py` (`test_formulario_valido`)
