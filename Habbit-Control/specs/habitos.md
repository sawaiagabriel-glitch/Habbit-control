# Especificação: Gestão de Hábitos

## Visão Geral do Módulo
O módulo de hábitos gerencia o ciclo completo de vida dos hábitos de um cliente: definição de hábitos positivos e negativos, parametrização de frequências atuais e desejadas, acompanhamento visual de progresso, registro de atividades diárias associadas a datas específicas e compilação de relatórios analíticos comparativos com gráficos temporais.

---

## Requisitos do Sistema

### REQ-HAB-01 — Cadastro de Hábito

**Descrição EARS:**  
WHEN an authenticated client submits valid habit data via HTTP POST to `/cadastro_habito/` containing `tipo_habito` ('positivo' or 'negativo'), `nome_habito`, `frequencia_valor` (integer >= 0), `periodo` ('dia', 'semana', 'mes', 'ano'), `frequencia_desejada_valor` (integer >= 0), and `periodo_desejado`, THE SYSTEM SHALL create and save a new `Habito` record associated with the authenticated `Cliente`, issue a success flash message (`Hábito "[nome]" cadastrado com sucesso!`), and redirect to `/cadastro_habito/`.

**Objetivo:**  
Permitir a criação de um novo hábito vinculado exclusivamente à conta do cliente autenticado, registrando metas operacionais e frequências de acompanhamento.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente possui sessão ativa válida associada ao seu e-mail.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `tipo_habito` | String | Sim | Deve ser estritamente `'positivo'` ou `'negativo'`. |
| `nome_habito` | String | Sim | Texto descritivo com até 255 caracteres. Não pode ser vazio. |
| `frequencia_valor` | Inteiro | Sim | Inteiro maior ou igual a 0. |
| `periodo` | String | Sim | Deve ser estritamente `'dia'`, `'semana'`, `'mes'` ou `'ano'`. |
| `frequencia_desejada_valor` | Inteiro | Sim | Inteiro maior ou igual a 0. |
| `periodo_desejado` | String | Sim | Deve ser estritamente `'dia'`, `'semana'`, `'mes'` ou `'ano'`. |

**Regras de negócio:**
1. A rota `/cadastro_habito/` exige autenticação. Se o cliente não estiver autenticado, deve ser redirecionado para `/login/` com mensagem de aviso.
2. Em requisições HTTP GET, o sistema deve renderizar o template `pagina_interna/cadastro_habito.html` com código de status HTTP 200, passando `cliente` no contexto.
3. Em requisições HTTP POST:
   - Se algum dos campos obrigatórios estiver ausente ou vazio, o sistema deve registrar a mensagem de erro `"Por favor, preencha todos os campos."`, re-renderizar a página com HTTP 200 e interromper a criação;
   - Os campos `frequencia_valor` e `frequencia_desejada_valor` devem ser convertidos para inteiros e validados conforme REQ-HAB-02;
   - O objeto `Habito` deve ser instanciado e salvo com a chave estrangeira `cliente` apontando para o cliente da sessão;
   - Os metadados `data_criacao` e `data_atualizacao` são preenchidos automaticamente;
   - Deve ser enfileirada uma mensagem de sucesso no padrão: `Hábito "{nome_habito}" cadastrado com sucesso!`;
   - O sistema deve responder com redirecionamento HTTP 302 para `/cadastro_habito/`.

**Fluxo principal:**
1. O cliente preenche o formulário em `/cadastro_habito/` e clica em "Cadastrar Hábito".
2. O formulário é enviado via POST com os 6 campos obrigatórios.
3. A view `cadastro_habito` valida a autenticação e a integridade de todos os campos.
4. A view executa `Habito.objects.create(...)`.
5. Uma mensagem de sucesso é registrada.
6. O sistema emite HTTP 302 redirecionando para `/cadastro_habito/`.
7. A página é recarregada limpa e a notificação de confirmação é exibida.

**Fluxos alternativos e de erro:**
- **Campos em branco:** A view detecta ausência de dados, adiciona a mensagem `"Por favor, preencha todos os campos."` e renderiza a página com status HTTP 200.
- **Falha de persistência no banco:** Capturada pelo bloco `except Exception as e`, enfileirando `"Erro ao cadastrar hábito: <erro>"` e renderizando com HTTP 200.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/cadastro_habito/`.
- Notificação de sucesso exibida no topo da tela.
- Registro gravado na tabela `pagina_interna_habito`.

**Persistência:**
- Tabela `pagina_interna_habito`: inserção de 1 novo registro associado ao `cliente_id`.

**Critérios de aceitação:**
- GIVEN um cliente autenticado
  WHEN enviar POST para `/cadastro_habito/` com `tipo_habito="positivo"`, `nome_habito="Leitura Diária"`, `frequencia_valor=1`, `periodo="dia"`, `frequencia_desejada_valor=2` e `periodo_desejado="dia"`
  THEN o sistema deve redirecionar com HTTP 302 para `/cadastro_habito/`
  AND o banco de dados deve conter o registro correspondente associado a este cliente
  AND a mensagem `"Hábito \"Leitura Diária\" cadastrado com sucesso!"` deve ser enfileirada.

**Casos-limite:**
- Frequência igual a 0: permitida e persistida com sucesso.
- Nome com 255 caracteres: aceito sem truncamento.

**Fora de escopo:**
- Lembretes por notificação push ou e-mail.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/models.py` (`Habito`), `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`cadastro_habito`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/cadastro_habito.html`, `static/pagina_interna/js/habitos.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-02 — Validação Numérica de Frequências

**Descrição EARS:**  
IF the user submits non-numeric frequency values or negative integers on `/cadastro_habito/` or `/editar_habito/<id>/`, THEN THE SYSTEM SHALL reject habit persistence, emit an error notification ("As frequências não podem ser negativas." or "Os valores de frequência devem ser números válidos."), and re-render the form with HTTP 200.

**Objetivo:**  
Assegurar que apenas valores inteiros válidos e não negativos sejam aceitos nos campos de frequência atual e desejada de hábitos.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Requisição POST submetida para `/cadastro_habito/` ou `/editar_habito/<int:habito_id>/`.

**Entradas:**
| Campo | Tipo | Condição |
|---|---|---|
| `frequencia_valor` | String | Não conversível para inteiro, OU inteiro menor que 0. |
| `frequencia_desejada_valor` | String | Não conversível para inteiro, OU inteiro menor que 0. |

**Regras de negócio:**
1. A conversão de `frequencia_valor` e `frequencia_desejada_valor` deve ser realizada via `int()`.
2. Se a conversão disparar `ValueError`:
   - A operação de gravação ou atualização deve ser abortada;
   - Deve ser enfileirada a mensagem de erro: `"Os valores de frequência devem ser números válidos."`;
   - O formulário correspondente deve ser re-renderizado com código HTTP 200.
3. Se os valores forem números válidos, porém qualquer um deles for menor que 0 (`freq_atual < 0 or freq_desejada < 0`):
   - A operação de gravação ou atualização deve ser abortada;
   - Deve ser enfileirada a mensagem de erro: `"As frequências não podem ser negativas."`;
   - O formulário correspondente deve ser re-renderizado com código HTTP 200.

**Fluxo principal:**
1. O usuário submete o formulário com `frequencia_valor="-3"`.
2. A view tenta a conversão e identifica valor negativo.
3. A view registra a mensagem `"As frequências não podem ser negativas."`.
4. O sistema re-renderiza o template com código HTTP 200 sem persistir alterações.

**Fluxos alternativos e de erro:**
- **Submissão com caracteres alfanuméricos:** O usuário envia `frequencia_valor="cinco"`. A view dispara `ValueError`, enfileira `"Os valores de frequência devem ser números válidos."` e re-renderiza com HTTP 200.

**Resultado esperado:**
- Formulário re-renderizado com código HTTP 200 e mensagem de erro visualizada em toast.
- Nenhuma alteração persistida no banco de dados.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um cliente preenchendo o cadastro de hábito
  WHEN enviar `frequencia_valor="-1"`
  THEN a resposta deve ter status HTTP 200
  AND deve conter a notificação `"As frequências não podem ser negativas."`
  AND nenhum registro de hábito deve ser salvo.
- GIVEN um cliente editando um hábito
  WHEN enviar `frequencia_desejada_valor="abc"`
  THEN a resposta deve ter status HTTP 200
  AND deve conter a notificação `"Os valores de frequência devem ser números válidos."`.

**Casos-limite:**
- Valor 0: aceito com sucesso (inteiro não negativo).
- Números decimais (ex.: `"2.5"`): disparam `ValueError` na conversão `int()`, exibindo `"Os valores de frequência devem ser números válidos."`.

**Fora de escopo:**
- Aceite de frequências fracionadas.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/views.py` (`cadastro_habito`, `editar_habito`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/cadastro_habito.html`, `apps/pagina_interna/templates/pagina_interna/editar_habito.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-03 — Edição de Hábito

**Descrição EARS:**  
WHEN an authenticated client submits modified habit data via HTTP POST to `/editar_habito/<int:habito_id>/` without the `excluir` parameter, IF the habit belongs to the authenticated client and all fields are valid, THEN THE SYSTEM SHALL update the `Habito` fields, update `data_atualizacao`, save the instance, emit a success flash message, and redirect the user to `/progressos/`.

**Objetivo:**  
Permitir que o cliente titular modifique o nome, tipo e parâmetros de frequência de um hábito previamente cadastrado.

**Ator:**  
Cliente autenticado (titular do hábito).

**Pré-condições:**
- O hábito existe e pertence ao cliente logado.
- Requisição POST para `/editar_habito/<int:habito_id>/` sem o campo `'excluir'`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `tipo_habito` | String | Sim | `'positivo'` ou `'negativo'`. |
| `nome_habito` | String | Sim | Texto não vazio com até 255 caracteres. |
| `frequencia_valor` | Inteiro | Sim | Inteiro maior ou igual a 0. |
| `periodo` | String | Sim | `'dia'`, `'semana'`, `'mes'` ou `'ano'`. |
| `frequencia_desejada_valor` | Inteiro | Sim | Inteiro maior ou igual a 0. |
| `periodo_desejado` | String | Sim | `'dia'`, `'semana'`, `'mes'` ou `'ano'`. |

**Regras de negócio:**
1. A rota `/editar_habito/<int:habito_id>/` exige autenticação.
2. Em requisições HTTP GET:
   - O sistema valida a titularidade do hábito. Se válido, renderiza `pagina_interna/editar_habito.html` com código HTTP 200, pré-populando os campos com os valores atuais.
3. Em requisições HTTP POST sem `'excluir'`:
   - Todos os 6 campos devem ser validados quanto ao preenchimento;
   - Se faltar algum campo, re-renderiza `editar_habito.html` com mensagem `"Por favor, preencha todos os campos."`;
   - As frequências devem ser números inteiros maiores ou iguais a 0;
   - Os atributos do hábito são atualizados: `tipo_habito`, `nome_habito`, `frequencia_atual_valor`, `frequencia_atual_periodo`, `frequencia_desejada_valor`, `frequencia_desejada_periodo`;
   - O campo `data_atualizacao` é atualizado automaticamente pelo Django (`auto_now=True`);
   - O sistema invoca `habito.save()`;
   - Deve ser enfileirada mensagem de sucesso: `Hábito "{nome_habito}" atualizado com sucesso!`;
   - O sistema responde com redirecionamento HTTP 302 para a rota `progressos` (`/progressos/`).

**Fluxo principal:**
1. O cliente acessa `/editar_habito/5/` via GET e visualiza os dados atuais.
2. O cliente altera a frequência desejada de 1 para 3 vezes ao dia.
3. O cliente submete o formulário via POST.
4. A view valida titularidade, campos e valores numéricos.
5. A instância de `Habito` é salva com os novos valores.
6. A view adiciona a mensagem de sucesso.
7. O sistema redireciona com HTTP 302 para `/progressos/`.

**Fluxos alternativos e de erro:**
- **Campos faltantes:** A view re-renderiza o formulário de edição com HTTP 200 e mensagem `"Por favor, preencha todos os campos."`.
- **Frequência inválida:** Rejeita conforme REQ-HAB-02.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/progressos/` com mensagem de sucesso.
- Dados do hábito atualizados no banco de dados.

**Persistência:**
- Atualização das colunas na tabela `pagina_interna_habito` para a linha correspondente ao `habito_id`.

**Critérios de aceitação:**
- GIVEN um cliente titular do hábito com ID 1
  WHEN enviar POST para `/editar_habito/1/` com `nome_habito="Caminhada Matinal"` e novos dados válidos
  THEN o sistema deve redirecionar com HTTP 302 para `/progressos/`
  AND o registro no banco deve ter `nome_habito="Caminhada Matinal"`
  AND a mensagem `"Hábito \"Caminhada Matinal\" atualizado com sucesso!"` deve ser enfileirada.

**Casos-limite:**
- Troca de tipo de hábito (de `'positivo'` para `'negativo'` ou vice-versa): aceita e atualizada no banco.

**Fora de escopo:**
- Histórico de versões anteriores das configurações do hábito.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/models.py` (`Habito`), `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`editar_habito`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/editar_habito.html`, `static/pagina_interna/js/habitos.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-04 — Exclusão de Hábito com Exclusão em Cascata

**Descrição EARS:**  
WHEN an authenticated client submits an HTTP POST request to `/editar_habito/<int:habito_id>/` with the `excluir` parameter, IF the habit belongs to the authenticated client, THEN THE SYSTEM SHALL delete the `Habito` object and cascade-delete all associated `RegistroAtividade` rows, emit a notification (`Hábito "[nome]" foi apagado com sucesso!`), and redirect to `/progressos/`.

**Objetivo:**  
Permitir a remoção definitiva de um hábito indesejado e expurgar de forma consistente todos os registros de atividade vinculados a ele.

**Ator:**  
Cliente autenticado (titular do hábito).

**Pré-condições:**
- O hábito existe e pertence ao cliente logado.
- Modal de confirmação acionado no frontend ou envio direto de POST com parâmetro `excluir`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `excluir` | String | Sim | Deve estar presente no payload POST (ex.: `name="excluir"` com `value="1"`). |

**Regras de negócio:**
1. A detecção da intenção de exclusão ocorre pela verificação: `request.method == 'POST' and 'excluir' in request.POST`.
2. O sistema deve validar que o hábito pertence ao cliente antes de qualquer operação destrutiva.
3. Ao executar `habito.delete()`, todas as linhas da tabela `RegistroAtividade` que possuem chave estrangeira para o hábito em questão devem ser excluídas automaticamente por efeito de `on_delete=models.CASCADE`.
4. Uma mensagem de notificação deve ser enfileirada no formato: `Hábito "{nome_habito}" foi apagado com sucesso!`. (No código atual da view, é inserida com `messages.error(request, ...)` para renderização estilizada em tom de alerta/remoção).
5. O sistema deve redirecionar com HTTP 302 para `/progressos/`.

**Fluxo principal:**
1. O cliente clica no botão "Excluir Hábito" na tela de edição.
2. O modal de confirmação `#modalExclusao` é aberto via JavaScript (`ModalExclusao.abrir()`).
3. O cliente clica em "Sim, Excluir".
4. O formulário oculto `#deleteForm` com `excluir=1` é submetido via POST.
5. A view identifica o parâmetro `excluir` e chama `habito.delete()`.
6. O hábito e todos os seus registros de atividade são removidos do banco.
7. A mensagem de confirmação de exclusão é adicionada.
8. O sistema redireciona com HTTP 302 para `/progressos/`.

**Fluxos alternativos e de erro:**
- **Falha durante a exclusão:** Capturada por `except Exception as e`, adicionando a mensagem `"Erro ao excluir hábito: <erro>"` e redirecionando para `/progressos/`.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/progressos/`.
- Hábito e registros de atividade removidos permanentemente do banco de dados.

**Persistência:**
- Deleção física da linha correspondente em `pagina_interna_habito` e de todas as linhas relacionadas em `pagina_interna_registroatividade`.

**Critérios de aceitação:**
- GIVEN um hábito de ID 3 com 5 registros de atividade vinculados
  WHEN o titular enviar POST para `/editar_habito/3/` com `excluir=1`
  THEN o sistema deve redirecionar com HTTP 302 para `/progressos/`
  AND o hábito 3 não deve mais existir no banco
  AND os 5 registros de atividade correspondentes devem ter sido excluídos em cascata.

**Casos-limite:**
- Exclusão de hábito sem registros de atividade associados: a deleção ocorre de forma atômica e idêntica.

**Fora de escopo:**
- Lixeira lógica (*soft delete*) ou restauração de hábitos excluídos.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/models.py` (`Habito`, `RegistroAtividade`), `apps/pagina_interna/views.py` (`editar_habito`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/editar_habito.html`, `static/pagina_interna/js/habitos.js` (`ModalExclusao`)
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-05 — Autorização e Isolamento de Hábitos por Cliente

**Descrição EARS:**  
IF an authenticated client attempts to access, edit, or delete a `Habito` that does not exist or belongs to another client, THEN THE SYSTEM SHALL deny access, emit an error flash message ("Hábito não encontrado ou você não tem permissão para editá-lo."), and redirect to `/progressos/`.

**Objetivo:**  
Garantir o isolamento completo dos dados (*multi-tenancy* lógico por cliente), impedindo que um cliente visualize, edite ou exclua hábitos de terceiros via alteração arbitrária de identificadores na URL (*IDOR - Insecure Direct Object References*).

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Requisição GET ou POST para `/editar_habito/<int:habito_id>/`.

**Entradas:**
| Campo | Tipo | Condição |
|---|---|---|
| `habito_id` | Inteiro | Identificador não existente no banco OU pertencente a outro cliente. |

**Regras de negócio:**
1. A consulta ao banco de dados deve utilizar obrigatoriamente o filtro composto: `Habito.objects.get(id=habito_id, cliente=cliente)`.
2. Se a consulta resultar em `Habito.DoesNotExist`:
   - O sistema não deve exibir nem alterar qualquer dado do hábito;
   - Uma mensagem de erro deve ser enfileirada: `"Hábito não encontrado ou você não tem permissão para editá-lo."`;
   - O sistema deve responder com redirecionamento HTTP 302 para a rota `progressos` (`/progressos/`).
3. Para endpoints de API (`/api/registrar_atividade/` e `/api/dados_relatorio/`), a violação de propriedade deve responder com status HTTP 404 e JSON `{"success": false, "error": "Hábito não encontrado"}`.

**Fluxo principal:**
1. O cliente A (id=1) tenta acessar a URL `/editar_habito/99/` (pertencente ao cliente B).
2. A view executa a busca combinando `id=99` e `cliente=clienteA`.
3. O ORM dispara `Habito.DoesNotExist`.
4. A view captura a exceção.
5. A mensagem de erro é enfileirada no framework de mensagens.
6. O sistema emite HTTP 302 redirecionando para `/progressos/`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Redirecionamento HTTP 302 para `/progressos/` com mensagem de erro.
- Nenhum dado de outros clientes exposto.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um hábito pertencente ao cliente B
  WHEN o cliente A tentar enviar requisição GET ou POST para `/editar_habito/<id_do_cliente_B>/`
  THEN o sistema deve redirecionar com HTTP 302 para `/progressos/`
  AND a mensagem `"Hábito não encontrado ou você não tem permissão para editá-lo."` deve ser apresentada.

**Casos-limite:**
- ID inexistente no banco (ex.: `habito_id=999999`): comportamento idêntico, redirecionando com a mesma mensagem de segurança.

**Fora de escopo:**
- Compartilhamento de hábitos entre múltiplos clientes ou perfis em equipe.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/views.py` (`editar_habito`, `registrar_atividade`, `api_dados_relatorio`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/editar_habito.html`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-06 — Listagem e Estatísticas de Progressos

**Descrição EARS:**  
WHEN an authenticated client accesses `/progressos/` via HTTP GET, THE SYSTEM SHALL retrieve all `Habito` records linked to the client ordered by `-data_criacao`, calculate the total number of habits, the count of positive habits (`tipo_habito='positivo'`), and the count of negative habits (`tipo_habito='negativo'`), and render `progressos.html` displaying these statistics and cards with HTTP 200.

**Objetivo:**  
Apresentar uma visão panorâmica e consolidada dos hábitos do cliente, fornecendo contadores estatísticos e cartões individuais de acompanhamento.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Sessão autenticada ativa.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| Nenhuma (requisição GET) | N/A | Não | N/A |

**Regras de negócio:**
1. A rota `/progressos/` exige autenticação via `get_cliente_from_session`.
2. A consulta de hábitos deve ser filtrada exclusivamente pelo cliente da sessão: `Habito.objects.filter(cliente=cliente).order_by('-data_criacao')`.
3. O sistema deve computar três métricas estatísticas:
   - `total_habitos = habitos.count()`
   - `habitos_positivos = habitos.filter(tipo_habito='positivo').count()`
   - `habitos_negativos = habitos.filter(tipo_habito='negativo').count()`
4. Se o cliente possuir 1 ou mais hábitos:
   - A página exibe o painel com os 3 contadores numéricos;
   - Uma grade de cartões é renderizada, onde cada cartão exibe o tipo do hábito (com badge colorida), nome, frequência atual, frequência desejada, data de criação e link para edição.
5. Se o cliente não possuir hábitos cadastrados:
   - A página exibe o estado vazio (*empty state*) com ícone, mensagem explicativa e botão "Cadastrar Primeiro Hábito" apontando para `/cadastro_habito/`.
6. O status HTTP retornado deve ser 200 OK.

**Fluxo principal:**
1. O cliente clica no menu "Progressos" ou requisita `/progressos/`.
2. A view recupera a lista ordenada de hábitos e calcula os totais.
3. O template `pagina_interna/progressos.html` é renderizado com status HTTP 200.
4. O cliente visualiza as estatísticas e seus cartões de hábitos.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Página HTML carregada com status HTTP 200 contendo as métricas e a listagem de cartões.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um cliente com 2 hábitos positivos e 1 negativo cadastrados
  WHEN enviar requisição GET para `/progressos/`
  THEN o código HTTP de retorno deve ser 200
  AND a página deve exibir `total_habitos=3`, `habitos_positivos=2` e `habitos_negativos=1`.
- GIVEN um cliente sem hábitos
  WHEN enviar requisição GET para `/progressos/`
  THEN o código HTTP de retorno deve ser 200
  AND deve exibir a seção de estado vazio com link para `/cadastro_habito/`.

**Casos-limite:**
- Cliente com dezenas de hábitos: exibidos em ordem cronológica reversa (mais recentes primeiro).

**Fora de escopo:**
- Paginação de cartões na tela de progressos.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`progressos`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/progressos.html`, `static/pagina_interna/js/progressos.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-07 — Visualização de Atividades Diárias por Data

**Descrição EARS:**  
WHEN an authenticated client accesses `/atividade_diaria/` via HTTP GET, THE SYSTEM SHALL determine the target date from the `data` query parameter (defaulting to the current date if omitted or malformed, bounded to between today and 365 days prior), query all habits of the client, pair each habit with its corresponding `RegistroAtividade` for that date, and render `atividade_diaria.html` with HTTP 200.

**Objetivo:**  
Permitir que o cliente consulte e registre execuções diárias de seus hábitos em uma data selecionada dentro da janela retroativa permitida de até 365 dias.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Sessão autenticada ativa.

**Entradas:**
| Parâmetro | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `data` (query param) | String (ISO date `YYYY-MM-DD`) | Não | Se omitido ou em formato inválido, adota a data atual (`date.today()`). Limite inferior: `hoje - 365 dias`. Limite superior: `hoje`. |

**Regras de negócio:**
1. A rota `/atividade_diaria/` exige autenticação.
2. Tratamento da data:
   - Se o parâmetro `data` for fornecido na URL, o sistema tenta converter via `datetime.strptime(data_selecionada, '%Y-%m-%d').date()`;
   - Se a conversão falhar (`ValueError`, `TypeError`) ou o parâmetro não for enviado, adota `date.today()`.
3. O seletor de data da interface define `min = date.today() - timedelta(days=365)` e `max = date.today()`.
4. A view busca todos os hábitos do cliente ordenados por `-data_criacao`.
5. Para cada hábito, busca o registro correspondente para a data selecionada: `RegistroAtividade.objects.filter(habito=habito, data=data_selecionada).first()`.
6. A view monta a lista `habitos_com_registros` contendo os pares `{'habito': habito, 'registro': registro}`.
7. Se não houver registro existente para o hábito na data selecionada, o campo de quantidade deve exibir o valor padrão `0`.
8. O template `pagina_interna/atividade_diaria.html` deve ser renderizado com status HTTP 200.

**Fluxo principal:**
1. O cliente acessa `/atividade_diaria/?data=2026-10-15`.
2. A view analisa o parâmetro de data e identifica o dia 15/10/2026.
3. A view recupera os hábitos do cliente e os registros vinculados a essa data.
4. A página é renderizada com código HTTP 200, exibindo os cartões com controles de incremento/decremento de quantidade.

**Fluxos alternativos e de erro:**
- **Parâmetro de data malformado:** O cliente envia `?data=invalida`. A view captura o erro e utiliza `date.today()`.

**Resultado esperado:**
- Página HTML carregada com status HTTP 200 exibindo o seletor de data e os hábitos com suas quantidades registradas na data.

**Persistência:**
- Nenhuma alteração no banco de dados durante a requisição GET.

**Critérios de aceitação:**
- GIVEN um cliente com hábitos e um registro com quantidade 3 na data de hoje
  WHEN acessar `/atividade_diaria/` sem parâmetros
  THEN o código HTTP deve ser 200
  AND o cartão do hábito deve exibir o valor 3 no campo de quantidade
  AND o seletor de data deve estar com a data de hoje.
- GIVEN que o usuário fornece uma data inválida `?data=99-99-9999`
  WHEN enviar requisição GET para `/atividade_diaria/`
  THEN a página deve carregar com HTTP 200 adotando a data de hoje.

**Casos-limite:**
- Troca de data no input pelo usuário: o script `atividade_diaria.js` dispara `alterarData()`, recarregando a página com `?data=YYYY-MM-DD`.

**Fora de escopo:**
- Registro de atividades em datas futuras além de `date.today()`.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`atividade_diaria`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/atividade_diaria.html`, `static/pagina_interna/js/atividade_diaria.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-08 — Registro e Atualização de Atividade Diária via API

**Descrição EARS:**  
WHEN an authenticated client submits an asynchronous HTTP POST request to `/api/registrar_atividade/` with a JSON body containing `habito_id`, `quantidade` (integer >= 0), and `data` (ISO date format), IF the specified habit belongs to the client, THEN THE SYSTEM SHALL create or update the unique `RegistroAtividade` for that habit and date, enforce the `unique_together = ['habito', 'data']` constraint, and respond with HTTP 200 JSON `{"success": true, "quantidade": <quantidade>, "data": "<data>"}`.

**Objetivo:**  
Permitir a gravação atômica da quantidade de vezes em que um hábito foi executado em um determinado dia, sem necessidade de recarregar a página.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Sessão autenticada ativa.
- Token CSRF presente no cabeçalho `X-CSRFToken`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `habito_id` | Inteiro | Sim | Deve pertencer a um hábito ativo do cliente autenticado. |
| `quantidade` | Inteiro | Não (default 1) | Inteiro maior ou igual a 0. |
| `data` | String (ISO date `YYYY-MM-DD`) | Não (default hoje) | Data no formato ISO. |

**Regras de negócio:**
1. A rota `/api/registrar_atividade/` exige requisição HTTP POST. Requisições por outros métodos respondem com HTTP 405 e `{"success": false, "error": "Método não permitido"}`.
2. Se o usuário não estiver autenticado na sessão, responde com HTTP 401 e `{"success": false, "error": "Usuário não autenticado"}`.
3. Se o valor de `quantidade` for menor que 0, responde com HTTP 400 e `{"success": false, "error": "A quantidade não pode ser negativa"}`.
4. Se `quantidade` não puder ser convertida para inteiro, responde com HTTP 400 e `{"success": false, "error": "Quantidade inválida"}`.
5. O sistema deve validar que o hábito especificado por `habito_id` pertence ao cliente autenticado (`Habito.objects.get(id=habito_id, cliente=cliente)`). Se não pertencer ou não existir, responde com HTTP 404 e `{"success": false, "error": "Hábito não encontrado"}`.
6. A persistência do registro deve respeitar a restrição de unicidade `unique_together = ['habito', 'data']`:
   - O sistema invoca `RegistroAtividade.objects.get_or_create(habito=habito, data=data_registro, defaults={'quantidade': quantidade})`;
   - Se o registro já existir (`created == False`), a quantidade deve ser atualizada para o novo valor (`registro.quantidade = quantidade`) e gravada via `registro.save()`.
7. Em caso de sucesso, o sistema responde com HTTP 200 e JSON:
   ```json
   {
     "success": true,
     "quantidade": 3,
     "data": "2026-10-15"
   }
   ```
8. Em caso de erro interno não tratado, o sistema responde com HTTP 400 e `{"success": false, "error": "<mensagem_erro>"}`.

**Fluxo principal:**
1. O usuário clica no botão "+" de um hábito na tela de atividade diária.
2. O script incrementa o input visual e envia POST para `/api/registrar_atividade/` com `{"habito_id": 2, "quantidade": 4, "data": "2026-10-15"}`.
3. A view autentica o cliente e localiza o hábito.
4. O sistema busca ou cria o `RegistroAtividade` para o hábito e data.
5. O valor `quantidade = 4` é salvo no banco de dados.
6. A view retorna status HTTP 200 com o JSON de confirmação.
7. O frontend exibe a confirmação visual "Registrado: 4x".

**Fluxos alternativos e de erro:**
- **Quantidade negativa submetida:** Retorna HTTP 400 com `{"success": false, "error": "A quantidade não pode ser negativa"}`.
- **Hábito pertencente a outro cliente:** Retorna HTTP 404 com `{"success": false, "error": "Hábito não encontrado"}`.
- **Cliente não autenticado:** Retorna HTTP 401 com `{"success": false, "error": "Usuário não autenticado"}`.

**Resultado esperado:**
- Resposta JSON HTTP 200 confirmando a quantidade e a data persistidas.
- Tabela `RegistroAtividade` atualizada.

**Persistência:**
- Criação de novo registro ou atualização da coluna `quantidade` na tabela `pagina_interna_registroatividade`.

**Critérios de aceitação:**
- GIVEN um hábito existente do cliente
  WHEN enviar POST para `/api/registrar_atividade/` com `quantidade=5` e `data="2026-10-15"`
  THEN o código HTTP de retorno deve ser 200
  AND o JSON deve conter `"quantidade": 5`
  AND o banco de dados deve registrar exatamente 1 linha para esse hábito nesta data com quantidade 5.
- GIVEN um envio com `quantidade=-2`
  WHEN submeter requisição à API
  THEN o código HTTP deve ser 400
  AND o JSON deve conter `"error": "A quantidade não pode ser negativa"`.

**Casos-limite:**
- Quantidade zero (`quantidade=0`): aceita com sucesso, permitindo zerar o registro de atividade daquele dia.

**Fora de escopo:**
- Registro em lote de múltiplos hábitos em uma única chamada de API.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/models.py` (`RegistroAtividade`), `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`registrar_atividade`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/atividade_diaria.html`, `static/pagina_interna/js/atividade_diaria.js`
- Testes existentes: Não coberto por teste automatizado

---

### REQ-HAB-09 — Compilação e Geração de Dados para Relatórios

**Descrição EARS:**  
WHEN an authenticated client requests `/api/dados_relatorio/` via HTTP GET with query parameters `habito_id` and `periodo` ('dia', 'semana', 'mes', or 'ano'), IF the habit belongs to the client, THEN THE SYSTEM SHALL extract activities within the range, calculate accumulated registered volume, compute expected cumulative volume according to the desired frequency, determine the percentage of progress differentiating positive and negative habit formulas, and return the dataset in JSON format with HTTP 200 for Chart.js rendering.

**Objetivo:**  
Fornecer os dados analíticos temporais consolidados e calculados para renderização de gráficos de linha comparativos de progresso contra metas estabelecidas.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- Sessão autenticada ativa.

**Entradas:**
| Parâmetro | Tipo | Obrigatório | Valores Permitidos |
|---|---|---|---|
| `habito_id` | Inteiro | Sim | ID de um hábito pertencente ao cliente. |
| `periodo` | String | Não (default `'mes'`) | `'dia'`, `'semana'`, `'mes'`, `'ano'`. |

**Regras de negócio:**
1. A rota `/api/dados_relatorio/` exige autenticação. Caso desautenticado, responde com HTTP 401 e `{"success": false, "error": "Usuário não autenticado"}`.
2. A requisição deve ser via método HTTP GET. Outros métodos respondem com HTTP 405 e `{"success": false, "error": "Método não permitido"}`.
3. Se `habito_id` for omitido, responde com HTTP 400 e `{"success": false, "error": "Hábito não especificado"}`.
4. Se o hábito não pertencer ao cliente ou não existir, responde com HTTP 404 e `{"success": false, "error": "Hábito não encontrado"}`.
5. Se `periodo` não pertencer a `['dia', 'semana', 'mes', 'ano']`, responde com HTTP 400 e `{"success": false, "error": "Período inválido"}`.
6. **Definição de intervalos temporais (`data_fim = date.today()`):**
   - `'dia'`: `data_inicio = data_fim` (1 dia; intervalo diário);
   - `'semana'`: `data_inicio = data_fim - timedelta(days=6)` (7 dias; intervalo diário);
   - `'mes'`: `data_inicio = data_fim - timedelta(days=29)` (30 dias; intervalo diário);
   - `'ano'`: `data_inicio = data_fim - timedelta(days=364)` (365 dias; agrupamento semanal em blocos de 7 dias).
7. **Normalização da frequência desejada para base diária (`freq_desejada_por_dia`):**
   - Se `frequencia_desejada_periodo == 'dia'`: `freq_desejada_por_dia = valor`;
   - Se `frequencia_desejada_periodo == 'semana'`: `freq_desejada_por_dia = valor / 7`;
   - Se `frequencia_desejada_periodo == 'mes'`: `freq_desejada_por_dia = valor / 30`;
   - Se `frequencia_desejada_periodo == 'ano'`: `freq_desejada_por_dia = valor / 365`.
8. **Cálculo acumulativo e percentual de progresso por ponto:**
   - Em cada ponto de medição (dia a dia, ou semana a semana no ano):
     - `total_registrado_acumulado`: soma cumulativa das quantidades de atividades registradas até aquele ponto;
     - `esperado_acumulado = freq_desejada_por_dia * dias_contados`.
   - **Fórmula para Hábito Positivo (quanto mais execuções, melhor):**
     - Se `esperado_acumulado > 0`:  
       `progresso = min(100, (total_registrado_acumulado / esperado_acumulado) * 100)`
     - Se `esperado_acumulado == 0`:  
       `progresso = 0`
   - **Fórmula para Hábito Negativo (quanto menos execuções, melhor):**
     - Se `esperado_acumulado > 0`:  
       `progresso = min(100, max(0, (1 - (total_registrado_acumulado / esperado_acumulado)) * 100))`
     - Se `esperado_acumulado == 0`:  
       `progresso = 100` se `total_registrado_acumulado == 0` senão `0`.
9. **Totais consolidados do período:**
   - `total_registrado`: somatório de todas as quantidades de atividades registradas no intervalo;
   - `total_esperado`:
     - Para `'dia'`: `freq_desejada_por_dia`
     - Para `'semana'`: `freq_desejada_por_dia * 7`
     - Para `'mes'`: `freq_desejada_por_dia * 30`
     - Para `'ano'`: `freq_desejada_por_dia * 365`
10. **Estrutura do JSON retornado com status HTTP 200:**
    ```json
    {
      "success": true,
      "habito": {
        "id": 1,
        "nome": "Exercício Físico",
        "tipo": "positivo",
        "frequencia_desejada_valor": 1,
        "frequencia_desejada_periodo": "Dia"
      },
      "periodo": "semana",
      "total_registrado": 5,
      "total_esperado": 7.0,
      "labels": ["09/10", "10/10", "11/10", "12/10", "13/10", "14/10", "15/10"],
      "dados_registrados": [1, 2, 2, 3, 4, 4, 5],
      "dados_esperados": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
      "progresso_percent": [100.0, 100.0, 66.67, 75.0, 80.0, 66.67, 71.43]
    }
    ```

**Fluxo principal:**
1. O usuário seleciona um hábito e o período `'semana'` na tela `/relatorios/` e clica em "Gerar Relatório".
2. O script `relatorios.js` efetua requisição GET para `/api/dados_relatorio/?habito_id=1&periodo=semana`.
3. A view executa os cálculos de acumulação e percentuais diferenciados para o tipo de hábito.
4. O sistema retorna o JSON com código HTTP 200.
5. O script atualiza os contadores na tela e renderiza o gráfico via Chart.js com curvas de acumulado registrado, acumulado esperado e percentual de progresso.

**Fluxos alternativos e de erro:**
- **Período inexistente:** Requisição com `?periodo=trimestre` retorna HTTP 400 com `{"success": false, "error": "Período inválido"}`.
- **Hábito não informado:** Requisição sem `habito_id` retorna HTTP 400 com `{"success": false, "error": "Hábito não especificado"}`.

**Resultado esperado:**
- Resposta JSON HTTP 200 contendo listas alinhadas de labels, dados registrados acumulados, dados esperados acumulados e progresso percentual.

**Persistência:**
- Nenhuma alteração no banco de dados.

**Critérios de aceitação:**
- GIVEN um hábito positivo com meta de 1 por dia
  WHEN solicitar relatório do período `'semana'` tendo 7 atividades registradas
  THEN o status retornado deve ser HTTP 200
  AND `total_registrado` deve ser 7
  AND `total_esperado` deve ser 7.0
  AND o último valor de `progresso_percent` deve ser 100.0.
- GIVEN um hábito negativo com meta desejada de 0 e total registrado de 2 no período
  WHEN solicitar relatório
  THEN o cálculo de progresso deve aplicar a fórmula de hábito negativo.

**Casos-limite:**
- Nenhuma atividade registrada no período: `dados_registrados` contém lista de zeros, progresso para hábito positivo resulta em 0%, e para hábito negativo resulta em 100%.

**Fora de escopo:**
- Exportação de relatórios para arquivo PDF ou CSV.

**Rastreabilidade:**
- Implementação: `apps/pagina_interna/models.py` (`Habito`, `RegistroAtividade`), `apps/pagina_interna/urls.py`, `apps/pagina_interna/views.py` (`relatorios`, `api_dados_relatorio`)
- Template/JS: `apps/pagina_interna/templates/pagina_interna/relatorios.html`, `static/pagina_interna/js/relatorios.js`
- Testes existentes: Não coberto por teste automatizado
