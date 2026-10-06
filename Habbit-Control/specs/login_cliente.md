# Login de Cliente

## Requisitos

### REQ-LOGIN-01
WHEN the user accesses the URL `/login/` via HTTP GET, THE SYSTEM SHALL render the login interface displaying the `LoginForm` containing fields for Email and Senha, clearing any previously stored flash messages before rendering.

#### Rastreabilidade:
- `apps/login_cadastro_app/urls.py`
- `apps/login_cadastro_app/views.py` (`login`)
- `apps/login_cadastro_app/forms.py` (`LoginForm`)
- `apps/login_cadastro_app/templates/login_cadastro_app/login.html`

---

### REQ-LOGIN-02
WHEN the user submits valid email and password credentials via HTTP POST to `/login/`, THE SYSTEM SHALL verify the password against the stored PBKDF2 hash using `Cliente.check_password`, store the authenticated email in `request.session['cliente_email']`, create a welcome message ("Bem-vindo(a), [PrimeiroNome]!"), and redirect the user to `/alterar_dados/`.

#### Rastreabilidade:
- `apps/login_cadastro_app/models.py` (`check_password`)
- `apps/login_cadastro_app/views.py` (`login`)
- `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- `apps/login_cadastro_app/tests.py` (`test_login_sucesso_com_email_e_senha`)

---

### REQ-LOGIN-03
WHEN the user submits an email address with mixed uppercase or leading/trailing whitespace, THE SYSTEM SHALL normalize the email string to lowercase and trimmed characters prior to executing the database lookup.

#### Rastreabilidade:
- `apps/login_cadastro_app/forms.py` (`LoginForm.clean_email`)
- `apps/login_cadastro_app/views.py` (`login`)
- `apps/login_cadastro_app/tests.py` (`test_login_insensivel_a_maiusculas_email`)

---

### REQ-LOGIN-04
IF the submitted email does not exist in the `Cliente` database OR the password does not match the stored hash, THEN THE SYSTEM SHALL reject authentication, clear the message storage, keep the user unauthenticated without session cookies, and re-render the login page.

#### Rastreabilidade:
- `apps/login_cadastro_app/views.py` (`login`)
- `apps/login_cadastro_app/templates/login_cadastro_app/login.html`
- `apps/login_cadastro_app/tests.py` (`test_login_senha_incorreta`, `test_login_email_inexistente`)

---

### REQ-LOGIN-05
WHEN the user clicks the password toggle button on the login form, THE SYSTEM SHALL alternate the password input field type between `password` and `text`, toggling the open-eye and slash-eye icon display.

#### Rastreabilidade:
- `apps/login_cadastro_app/templates/login_cadastro_app/login.html`

---

### REQ-LOGIN-06
WHILE the user is editing the email field on the login form, THE SYSTEM SHALL validate on blur whether the content matches standard email regex format (`/^[^\s@]+@[^\s@]+\.[^\s@]+$/`) and apply `valid` or `invalid` CSS classes to the enclosing form group.

#### Rastreabilidade:
- `apps/login_cadastro_app/templates/login_cadastro_app/login.html`

---

### REQ-LOGIN-07
WHEN the user accesses the URL `/logout/` via HTTP GET, IF `cliente_email` exists in the session, THEN THE SYSTEM SHALL delete `cliente_email` from `request.session`, issue a success flash message ("Logout realizado com sucesso!"), and redirect the user to `/`; OTHERWISE, THEN THE SYSTEM SHALL emit an info message ("Você não estava logado.") and redirect to `/`.

#### Rastreabilidade:
- `apps/login_cadastro_app/urls.py`
- `apps/login_cadastro_app/views.py` (`logout_view`)
