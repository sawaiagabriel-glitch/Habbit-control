# Privacidade e Conformidade LGPD

## Requisitos

### REQ-LGPD-01
WHEN any user accesses the route `/consentimento/` via HTTP GET, THE SYSTEM SHALL render the LGPD privacy policy page (`consentimento.html`) detailing the categories of personal data collected (Nome completo, Idade, Email, Cidade e país de residência, Profissão), the purposes of data collection (segurança da plataforma, estudos acadêmicos anonimizados, melhoria de serviços), technical data protection measures, and statutory user rights under Brazilian Federal Law 13.709/2018 (LGPD).

#### Rastreabilidade:
- `apps/login_cadastro_app/urls.py`
- `apps/login_cadastro_app/views.py` (`consentimento`)
- `apps/login_cadastro_app/templates/login_cadastro_app/consentimento.html`

---

### REQ-LGPD-02
THE SYSTEM SHALL display a mandatory consent checkbox on the client registration page (`cadastro_cliente.html`) containing an explicit hyperlink targeting `/consentimento/` with `target="_blank"`, accompanied by descriptive text outlining the processing of personal data in accordance with the LGPD.

#### Rastreabilidade:
- `apps/login_cadastro_app/forms.py` (`ClienteForm`)
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`

---

### REQ-LGPD-03
WHEN a client registration is successfully processed, THE SYSTEM SHALL persist the affirmative consent state as a boolean `True` value in the `lgpd` attribute of the `Cliente` database model (`default=False`).

#### Rastreabilidade:
- `apps/login_cadastro_app/models.py` (`Cliente.lgpd`)
- `apps/login_cadastro_app/forms.py` (`ClienteForm`)
- `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- `apps/login_cadastro_app/tests.py` (`test_criar_cliente_sem_cpf`, `test_post_cadastro_sucesso`)

---

### REQ-LGPD-04
IF a client registration request is submitted without the user checking the `lgpd` agreement checkbox, THEN THE SYSTEM SHALL invalidate the submission, prevent account persistence, and return the registration template displaying the appropriate field validation error.

#### Rastreabilidade:
- `apps/login_cadastro_app/forms.py` (`ClienteForm`)
- `apps/login_cadastro_app/views.py` (`cadastro_cliente`)
- `apps/login_cadastro_app/templates/login_cadastro_app/cadastro_cliente.html`
- `apps/login_cadastro_app/tests.py` (`test_formulario_valido`)
