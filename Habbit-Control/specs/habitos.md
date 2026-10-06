# Gestão de Hábitos

## Requisitos

### REQ-HAB-01
WHEN an authenticated client submits valid habit data via HTTP POST to `/cadastro_habito/` containing `tipo_habito` ('positivo' or 'negativo'), `nome_habito`, `frequencia_valor` (integer >= 0), `periodo` ('dia', 'semana', 'mes', 'ano'), `frequencia_desejada_valor` (integer >= 0), and `periodo_desejado`, THE SYSTEM SHALL create and save a new `Habito` record associated with the authenticated `Cliente`, issue a success message (`Hábito "[nome]" cadastrado com sucesso!`), and redirect to `/cadastro_habito/`.

#### Rastreabilidade:
- `apps/pagina_interna/models.py` (`Habito`)
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`cadastro_habito`)
- `apps/pagina_interna/templates/pagina_interna/cadastro_habito.html`
- `static/pagina_interna/js/habitos.js`

---

### REQ-HAB-02
IF the user submits non-numeric frequency values or negative integers on `/cadastro_habito/` or `/editar_habito/<id>/`, THEN THE SYSTEM SHALL reject habit persistence, emit an error notification ("As frequências não podem ser negativas." or "Os valores de frequência devem ser números válidos."), and re-render the form with the user context.

#### Rastreabilidade:
- `apps/pagina_interna/views.py` (`cadastro_habito`, `editar_habito`)
- `apps/pagina_interna/templates/pagina_interna/cadastro_habito.html`
- `apps/pagina_interna/templates/pagina_interna/editar_habito.html`

---

### REQ-HAB-03
WHEN an authenticated client submits modified habit data via HTTP POST to `/editar_habito/<int:habito_id>/` without the `excluir` parameter, IF the habit belongs to the authenticated client and all fields are valid, THEN THE SYSTEM SHALL update the `Habito` fields, update `data_atualizacao`, save the instance, emit a success message, and redirect the user to `/progressos/`.

#### Rastreabilidade:
- `apps/pagina_interna/models.py` (`Habito`)
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`editar_habito`)
- `apps/pagina_interna/templates/pagina_interna/editar_habito.html`
- `static/pagina_interna/js/habitos.js`

---

### REQ-HAB-04
WHEN an authenticated client submits an HTTP POST request to `/editar_habito/<int:habito_id>/` with the `excluir` parameter, IF the habit belongs to the authenticated client, THEN THE SYSTEM SHALL delete the `Habito` object and cascade-delete all associated `RegistroAtividade` rows, emit a notification (`Hábito "[nome]" foi apagado com sucesso!`), and redirect to `/progressos/`.

#### Rastreabilidade:
- `apps/pagina_interna/models.py` (`Habito`, `RegistroAtividade`)
- `apps/pagina_interna/views.py` (`editar_habito`)
- `apps/pagina_interna/templates/pagina_interna/editar_habito.html`
- `static/pagina_interna/js/habitos.js` (`ModalExclusao`)

---

### REQ-HAB-05
IF an authenticated client attempts to access, edit, or delete a `Habito` that does not exist or belongs to another client, THEN THE SYSTEM SHALL deny access, emit an error message ("Hábito não encontrado ou você não tem permissão para editá-lo."), and redirect to `/progressos/`.

#### Rastreabilidade:
- `apps/pagina_interna/views.py` (`editar_habito`)

---

### REQ-HAB-06
WHEN an authenticated client accesses `/progressos/` via HTTP GET, THE SYSTEM SHALL retrieve all `Habito` records linked to the client ordered by `-data_criacao`, calculate the total number of habits, the count of positive habits (`tipo_habito='positivo'`), and the count of negative habits (`tipo_habito='negativo'`), and render `progressos.html` displaying these statistics and cards.

#### Rastreabilidade:
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`progressos`)
- `apps/pagina_interna/templates/pagina_interna/progressos.html`
- `static/pagina_interna/js/progressos.js`

---

### REQ-HAB-07
WHEN an authenticated client accesses `/atividade_diaria/` via HTTP GET, THE SYSTEM SHALL determine the target date from the `data` query parameter (defaulting to the current date if omitted or malformed, bounded to between today and 365 days prior), query all habits of the client, pair each habit with its corresponding `RegistroAtividade` for that date, and render `atividade_diaria.html`.

#### Rastreabilidade:
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`atividade_diaria`)
- `apps/pagina_interna/templates/pagina_interna/atividade_diaria.html`
- `static/pagina_interna/js/atividade_diaria.js`

---

### REQ-HAB-08
WHEN an authenticated client submits an asynchronous HTTP POST request to `/api/registrar_atividade/` with a JSON body containing `habito_id`, `quantidade` (integer >= 0), and `data` (ISO date format), IF the specified habit belongs to the client, THEN THE SYSTEM SHALL create or update the unique `RegistroAtividade` for that habit and date, enforce the `unique_together = ['habito', 'data']` constraint, and respond with HTTP 200 JSON `{"success": true, "quantidade": <quantidade>, "data": "<data>"}`.

#### Rastreabilidade:
- `apps/pagina_interna/models.py` (`RegistroAtividade`)
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`registrar_atividade`)
- `apps/pagina_interna/templates/pagina_interna/atividade_diaria.html`
- `static/pagina_interna/js/atividade_diaria.js`

---

### REQ-HAB-09
WHEN an authenticated client requests `/api/dados_relatorio/` via HTTP GET with query parameters `habito_id` and `periodo` ('dia', 'semana', 'mes', or 'ano'), IF the habit belongs to the client, THEN THE SYSTEM SHALL extract activities within the range (`dia`: 1 day; `semana`: 7 days; `mes`: 30 days; `ano`: 365 days grouped weekly), calculate accumulated registered volume, compute expected cumulative volume according to the desired frequency, determine the percentage of progress (differentiating between positive and negative habit formulas), and return the dataset in JSON format for Chart.js rendering.

#### Rastreabilidade:
- `apps/pagina_interna/models.py` (`Habito`, `RegistroAtividade`)
- `apps/pagina_interna/urls.py`
- `apps/pagina_interna/views.py` (`relatorios`, `api_dados_relatorio`)
- `apps/pagina_interna/templates/pagina_interna/relatorios.html`
- `static/pagina_interna/js/relatorios.js`
