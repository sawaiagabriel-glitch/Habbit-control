# Especificação: Metas e Sequências (Streak)

## Status do Módulo
**NÃO IMPLEMENTADO** — Funcionalidade planejada para implementação futura orientada por desenvolvimento orientado a testes (TDD).

## Visão Geral do Módulo
O módulo de metas e sequências permite que os clientes estabeleçam alvos objetivos de frequência para seus hábitos dentro de intervalos padronizados (`dia`, `semana`, `mes`, `ano`). O sistema avalia deterministicamente o cumprimento da meta através do somatório de atividades registradas no intervalo temporal, gerenciando transições de estado da meta (`ativa`, `cumprida`, `não cumprida`) e mantendo o histórico de períodos consecutivos bem-sucedidos através de um contador de sequência (`streak`).

---

## Requisitos do Sistema

### REQ-META-01 — Definição de Meta Vinculada ao Hábito

**Descrição EARS:**  
WHEN an authenticated client defines a target for a habit, THE SYSTEM SHALL allow setting a minimum activity threshold (`quantidade_minima`, integer >= 1) for an evaluation period restricted to 'dia', 'semana', 'mes', or 'ano', associating the goal with exactly one positive `Habito`.

**Objetivo:**  
Permitir a parametrização de um limiar mínimo quantitativo de execuções exigidas dentro de um ciclo temporal regular para um hábito positivo específico.

**Ator:**  
Cliente autenticado (titular do hábito).

**Pré-condições:**
- O cliente possui sessão ativa válida.
- O hábito vinculado existe, pertence ao cliente autenticado e é do tipo `positivo`.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `habito_id` | Inteiro | Sim | Deve pertencer a um registro ativo de `Habito` do tipo `positivo` pertencente ao cliente autenticado. Cada hábito positivo possui no máximo 1 meta ativa. |
| `quantidade_minima` | Inteiro | Sim | Inteiro estritamente maior ou igual a 1 (`quantidade_minima >= 1`). Valores menores que 1 são inválidos. |
| `periodo` | String | Sim | Deve ser estritamente um dos 4 valores permitidos: `'dia'`, `'semana'`, `'mes'` ou `'ano'`. |

**Regras de negócio:**
1. A meta deve estar associada a exatamente um hábito (`Habito`) por meio de chave estrangeira.
2. Cada hábito positivo deve possuir no máximo uma meta ativa por período de avaliação.
3. A `quantidade_minima` é um número inteiro positivo (`PositiveIntegerField`) com valor mínimo permitido igual a 1.
4. O campo `periodo` aceita exclusivamente os quatro intervalos temporais homologados na plataforma:
   - `'dia'`
   - `'semana'`
   - `'mes'`
   - `'ano'`
5. **Limites temporais determinísticos do período (fuso horário `America/Sao_Paulo`):**
   - **`'dia'`**: Inicia às 00:00:00 da data e encerra às 23:59:59 da mesma data;
   - **`'semana'`**: Inicia na segunda-feira às 00:00:00 e encerra no domingo subsequente às 23:59:59;
   - **`'mes'`**: Inicia no primeiro dia do mês civil (dia 01) às 00:00:00 e encerra no último dia do mesmo mês (dia 28, 29, 30 ou 31) às 23:59:59;
   - **`'ano'`**: Inicia em 01 de janeiro às 00:00:00 e encerra em 31 de dezembro às 23:59:59 do mesmo ano civil.
6. Ao ser criada, a meta deve receber o estado inicial `'ativa'`.
7. O contador de sequência (`streak`) associado à meta deve receber o valor inicial igual a 0.
8. Nesta versão, metas só podem ser criadas para hábitos classificados como `positivo`. Tentativas de criar ou associar metas a hábitos negativos devem ser rejeitadas no backend (conforme REQ-META-09).

**Fluxo principal:**
1. O cliente escolhe um hábito positivo e define uma meta com `quantidade_minima = 5` e `periodo = "semana"`.
2. O sistema valida que `quantidade_minima >= 1`, que o hábito é do tipo positivo e que `periodo` pertence à lista permitida.
3. O sistema cria o registro da meta com estado `'ativa'` e `streak = 0`.
4. O sistema vincula a meta ao hábito especificado e associa o ciclo temporal vigente.

**Fluxos alternativos e de erro:**
- **Quantidade mínima menor que 1:** Se o usuário submeter `quantidade_minima <= 0`, o sistema deve rejeitar a criação com erro de validação.
- **Período inválido:** Se o usuário submeter período fora da lista permitida (ex.: `"quinzena"`), o sistema deve rejeitar com erro de validação.
- **Hábito negativo:** Se o cliente tentar cadastrar meta para um hábito classificado como negativo, o sistema rejeita a operação com erro de validação (REQ-META-09).

**Resultado esperado:**
- Registro de meta persistido com estado inicial `'ativa'` e `streak = 0`.

**Persistência:**
- Tabela de metas: inserção de registro contendo `habito_id`, `quantidade_minima`, `periodo`, `estado="ativa"`, `streak=0`, `data_inicio` e `data_criacao`.

**Critérios de aceitação:**
- GIVEN um hábito positivo válido pertencente ao cliente autenticado
  WHEN o cliente cadastrar meta com `quantidade_minima=3` e `periodo="semana"`
  THEN o sistema deve persistir a meta com estado `'ativa'`
  AND o valor do `streak` deve ser 0.
- GIVEN uma tentativa de criação de meta com `quantidade_minima=0`
  WHEN a requisição for processada
  THEN o sistema deve rejeitar a persistência e retornar erro de validação.
- GIVEN um hábito classificado como negativo
  WHEN o cliente tentar criar uma meta para ele
  THEN a criação deve ser rejeitada.

**Casos-limite:**
- Criação de meta no último dia do mês ou ano: o ciclo temporal vigente encerra-se às 23:59:59 daquele mesmo dia, disparando a avaliação do período logo em seguida.

**Fora de escopo:**
- Metas com intervalos customizados (ex.: a cada 3 dias ou a cada 15 dias).

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-02 — Estado Ativa Durante a Vigência do Período

**Descrição EARS:**  
WHILE the current evaluation period is ongoing and the cumulative volume of registered activities has not reached the defined minimum threshold, THE SYSTEM SHALL maintain the goal in the `ativa` state.

**Objetivo:**  
Manter a meta em andamento enquanto o ciclo temporal estiver vigente e o montante de execuções ainda não tiver alcançado o limiar fixado.

**Ator:**  
Sistema (motor de avaliação de metas).

**Pré-condições:**
- O carimbo de data/hora atual está contido dentro do intervalo do período vigente (`data_inicio <= agora <= data_fim`).
- A soma das atividades registradas no intervalo é menor que a `quantidade_minima`.

**Entradas:**
| Dado de Entrada | Origem | Descrição |
|---|---|---|
| `RegistroAtividade` do período | Tabela `RegistroAtividade` | Coleção de registros cuja coluna `data` satisfaz `data_inicio <= data <= data_fim` para o hábito. |
| `quantidade_minima` | Registro da Meta | Limiar numérico estipulado no REQ-META-01. |

**Regras de negócio:**
1. O volume de atividades realizadas no período é calculado estritamente pela soma das quantidades registradas:  
   `total_atividades = Sum(quantidade)` para todos os `RegistroAtividade` do hábito com `data` entre `data_inicio` e `data_fim` do período.
2. Se nenhum registro for encontrado para o hábito no período, o valor de `total_atividades` deve ser considerado igual a 0.
3. Enquanto o carimbo de data/hora atual for menor ou igual ao término do período (`agora <= data_fim`) e `total_atividades < quantidade_minima`, o estado da meta deve permanecer obrigatoriamente como `'ativa'`.
4. Durante o estado `'ativa'`, a interface deve exibir o progresso percentual padronizado entre 0% e 100% (conforme REQ-META-07). Quando o volume de atividades atinge ou ultrapassa a quantidade mínima (`total_atividades >= quantidade_minima`), a meta alcança 100% e transiciona para o estado `'cumprida'` (conforme REQ-META-03).

**Fluxo principal:**
1. O sistema calcula o progresso de uma meta semanal cuja `quantidade_minima` é 5.
2. O usuário possui 2 atividades registradas na semana corrente.
3. O sistema calcula `total_atividades = 2`.
4. Como `2 < 5` e o domingo 23:59:59 ainda não foi ultrapassado, a meta permanece no estado `'ativa'` com progresso proporcional de 40%.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Meta apresentada com status `'ativa'` e indicador visual de progresso proporcional entre 0% e 100%.

**Persistência:**
- O estado da meta permanece gravado como `'ativa'`.

**Critérios de aceitação:**
- GIVEN uma meta com `quantidade_minima=4` no período semanal corrente
  WHEN o usuário acumular 3 atividades e o período ainda não tiver encerrado
  THEN o estado da meta deve ser `'ativa'`
  AND o progresso percentual exibido deve ser `75%`.

**Casos-limite:**
- Meta recém-criada sem nenhum registro no período corrente: `total_atividades` é 0, o estado permanece `'ativa'` e o progresso percentual é 0%.

**Fora de escopo:**
- Congelamento ou pausa temporária voluntária de metas ativas.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-03 — Transição Imediata para o Estado Cumprida

**Descrição EARS:**  
WHEN the cumulative volume of registered activities reaches or exceeds the minimum threshold within the active evaluation period, THE SYSTEM SHALL transition the goal state to `cumprida` and record the completion timestamp.

**Objetivo:**  
Reconhecer imediatamente o atingimento do alvo estipulado pelo cliente logo que o volume cumulativo necessário for alcançado dentro do ciclo, registrando a data e hora do cumprimento.

**Ator:**  
Sistema (gatilho de inclusão ou edição de `RegistroAtividade`).

**Pré-condições:**
- A meta encontra-se no estado `'ativa'`.
- O período de avaliação ainda está vigente (`agora <= data_fim`).

**Entradas:**
| Evento disparador | Carga |
|---|---|
| Inclusão ou atualização de `RegistroAtividade` | Novo somatório de quantidades no período. |

**Regras de negócio:**
1. Sempre que um `RegistroAtividade` for criado ou alterado para uma data compreendida no período vigente, o sistema deve recalcular o somatório de atividades do período:  
   `total_atividades = Sum(quantidade)`.
2. Se `total_atividades >= quantidade_minima`:
   - O estado da meta deve transicionar imediatamente de `'ativa'` para `'cumprida'`;
   - O carimbo temporal de conclusão (`data_cumprimento`) deve ser registrado com a data/hora atual da ocorrência;
   - O progresso percentual exibido atinge 100% (conforme REQ-META-07).
3. Se a quantidade registrada ultrapassar a meta (`total_atividades > quantidade_minima`):
   - A meta permanece no estado `'cumprida'`;
   - O progresso percentual exibido permanece padronizado em 100%;
   - O volume excedente é apresentado na contagem numérica (conforme REQ-META-06), mas não gera saldo acumulável para ciclos temporais futuros.
4. **Reversibilidade intra-período:** Se um cliente editar ou excluir um registro de atividade do período corrente e o novo somatório recair para `total_atividades < quantidade_minima`, o estado da meta deve retornar imediatamente de `'cumprida'` para `'ativa'`, e o progresso percentual volta a ser inferior a 100%.

**Fluxo principal:**
1. Uma meta possui `quantidade_minima = 3` na semana.
2. O usuário registra a 3ª atividade na quarta-feira.
3. O sistema recalcula o total acumulado da semana para 3.
4. Como `3 >= 3`, o estado da meta muda imediatamente de `'ativa'` para `'cumprida'`, o progresso passa para 100% e `data_cumprimento` é registrada.
5. A interface exibe badge visual de meta cumprida.

**Fluxos alternativos e de erro:**
- **Reversão por redução de quantidade:** Na quinta-feira, o usuário reduz a quantidade da atividade de quarta-feira de 1 para 0. O novo total torna-se 2. Como `2 < 3`, o sistema reverte o estado da meta de `'cumprida'` para `'ativa'` e o progresso percentual retorna para cerca de 66.7%.

**Resultado esperado:**
- Estado da meta atualizado para `'cumprida'` no banco de dados e `data_cumprimento` preenchida.

**Persistência:**
- Coluna `estado` atualizada para `'cumprida'` e coluna `data_cumprimento` preenchida.

**Critérios de aceitação:**
- GIVEN uma meta ativa com `quantidade_minima=5`
  WHEN a soma de atividades do período atingir ou ultrapassar 5
  THEN o estado da meta deve mudar para `'cumprida'`
  AND o progresso percentual exibido deve ser `100%`
  AND a `data_cumprimento` deve ser registrada.
- GIVEN uma meta cumprida com soma de atividades igual a 5
  WHEN uma atividade de valor 1 do período for excluída reduzindo a soma para 4
  THEN o estado da meta deve retornar para `'ativa'`
  AND o progresso percentual deve retornar para `80%`.

**Casos-limite:**
- Adição em lote de atividades que ultrapasse a meta (ex.: meta de 2, adiciona 5): a meta transiciona diretamente para `'cumprida'` com progresso em 100%.

**Fora de escopo:**
- Bonificações financeiras ou premiações por alcance antecipado da meta.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-04 — Fechamento de Período e Transição para Não Cumprida

**Descrição EARS:**  
WHEN an evaluation period concludes and the cumulative volume of registered activities has not reached the minimum threshold, THE SYSTEM SHALL transition the goal state for that period to `não cumprida`, reset the streak counter to 0, and open a new evaluation period with state `ativa`.

**Objetivo:**  
Consolidar formalmente o resultado de encerramento do ciclo temporal, zerando o contador de sequência quando a meta não for alcançada e inicializando o novo ciclo de avaliação.

**Ator:**  
Sistema (rotina de fechamento de ciclo temporal).

**Pré-condições:**
- O carimbo temporal atingiu ou ultrapassou o término do período vigente (`agora > data_fim`).
- O estado da meta no encerramento permanece como `'ativa'`.

**Entradas:**
| Evento disparador | Condição |
|---|---|
| Virada do período temporal | `agora > data_fim` e `total_atividades < quantidade_minima`. |

**Regras de negócio:**
1. A rotina de fechamento de ciclo deve ser avaliada deterministicamente na virada do período:
   - Para `'dia'`: diariamente na virada do dia;
   - Para `'semana'`: às segundas-feiras às 00:00:00;
   - Para `'mes'`: no primeiro dia de cada mês civil às 00:00:00;
   - Para `'ano'`: no dia 01 de janeiro às 00:00:00.
2. Se ao término do período a meta ainda estiver com `total_atividades < quantidade_minima`:
   - O estado do ciclo encerrado é definido como `'não cumprida'`;
   - O valor do `streak` da meta é definido como 0 (`streak = 0`, conforme REQ-STREAK-02).
3. Se não houver nenhum registro de atividade associado ao hábito durante o período encerrado (`total_atividades == 0`), a meta encerra-se como `'não cumprida'` e o `streak` vai a 0.
4. Imediatamente após o encerramento, o sistema inicializa o próximo ciclo de avaliação para a mesma meta:
   - Novo intervalo temporal com `data_inicio` e `data_fim` atualizados para o período subsequente;
   - Estado do novo ciclo definido como `'ativa'`;
   - Contagem acumulada de atividades reiniciada a partir de 0.
5. Registros de atividades inseridos retroativamente com datas de períodos passados não alteram o streak de ciclos já encerrados (sem reprocessamento retroativo).

**Fluxo principal:**
1. Uma meta semanal possui `quantidade_minima = 4`.
2. Durante a semana, o cliente registra apenas 2 atividades.
3. No domingo às 23:59:59, o período se encerra.
4. Na virada do período, o sistema constata que `total_atividades = 2` e `2 < 4`.
5. A meta transiciona para `'não cumprida'` e o `streak` é definido como 0.
6. Um novo ciclo semanal é aberto com estado `'ativa'`, contagem zerada e `streak = 0`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Meta avaliada como `'não cumprida'` para o período findo.
- Valor de streak definido como 0.
- Novo ciclo aberto com estado `'ativa'`.

**Persistência:**
- Registro de meta atualizado com `estado="não cumprida"` e `streak=0`, seguido da abertura do novo ciclo com `estado="ativa"`.

**Critérios de aceitação:**
- GIVEN uma meta com `quantidade_minima=5` na semana encerrada com apenas 3 atividades registradas
  WHEN ocorrer a virada de período
  THEN o estado do ciclo encerrado deve ser `'não cumprida'`
  AND o contador de streak deve ser definido como 0
  AND o novo ciclo semanal deve ser inicializado com estado `'ativa'`.

**Casos-limite:**
- Ausência total de login ou registros: o ciclo encerra como `'não cumprida'` e o `streak` é mantido em 0.

**Fora de escopo:**
- Tolerância de carência (*grace period*) ou reprocessamento retroativo de ciclos anteriores.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-STREAK-01 — Incremento da Sequência de Cumprimento (*Streak*)

**Descrição EARS:**  
WHEN an evaluation period concludes with the goal in the `cumprida` state, THE SYSTEM SHALL increment the consecutive fulfilled periods counter (`streak`) by exactly 1.

**Objetivo:**  
Contabilizar com exatidão matemática o número ininterrupto de ciclos temporais em que o cliente atingiu com êxito a meta proposta.

**Ator:**  
Sistema (rotina de virada de ciclo temporal).

**Pré-condições:**
- O período de avaliação foi encerrado (`agora > data_fim`).
- O estado final da meta no ciclo que está se encerrando é estritamente `'cumprida'`.

**Entradas:**
| Dado de Entrada | Tipo | Restrições |
|---|---|---|
| `streak` atual | Inteiro | Maior ou igual a 0 (`PositiveIntegerField`). |
| Estado do ciclo encerrado | String | Deve ser `'cumprida'`. |

**Regras de negócio:**
1. O campo `streak` é um número inteiro não negativo (`models.PositiveIntegerField(default=0)`).
2. O incremento do streak ocorre estritamente no momento do fechamento formal do período de avaliação (na virada do ciclo).
3. Se o cliente atingir a `quantidade_minima` de forma antecipada durante a vigência do período, a meta transiciona imediatamente para `'cumprida'` (conforme REQ-META-03), porém o valor numérico do `streak` não é incrementado antecipadamente; ele só é acrescido no encerramento formal do período.
4. Na virada do ciclo temporal, se a meta do período encerrado estiver como `'cumprida'`:
   - O valor do streak deve ser incrementado em exatamente 1 (`streak = streak + 1`);
   - O novo valor é atribuído à meta para vigorar no ciclo que se inicia.
5. Se o cliente cumprir a meta em períodos consecutivos (ex.: 3 semanas seguidas cumpridas), o streak acumula sucessivamente (0 -> 1 -> 2 -> 3).

**Fluxo principal:**
1. O cliente possui uma meta semanal com `streak = 2`.
2. Durante a semana, atinge a meta na sexta-feira. O estado passa para `'cumprida'`, mas o streak permanece 2 até a virada.
3. No encerramento da semana, o sistema verifica que o ciclo terminou com estado `'cumprida'`.
4. O sistema calcula `novo_streak = 2 + 1 = 3`.
5. O valor `streak = 3` é persistido para a meta no novo ciclo que se inicia.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Campo `streak` incrementado em 1 e persistido no banco de dados.

**Persistência:**
- Coluna `streak` da meta atualizada com o valor acrescido de 1.

**Critérios de aceitação:**
- GIVEN uma meta com `streak=0` e estado `'cumprida'` na semana que encerra
  WHEN o período for encerrado na virada semanal
  THEN o valor do `streak` para o novo período deve ser 1.
- GIVEN uma meta mensal com `streak=4` que terminou o mês com estado `'cumprida'`
  WHEN o mês civil virar às 00:00:00 do dia 01
  THEN o valor do `streak` deve ser atualizado para 5.

**Casos-limite:**
- Cumprimento antecipado no primeiro dia do ciclo: o streak só incrementa ao final do ciclo, impedindo acúmulo duplo.

**Fora de escopo:**
- Multiplicadores de pontuação ou bônus com base na magnitude do streak.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-STREAK-02 — Zeramento da Sequência em Ciclos Não Cumpridos

**Descrição EARS:**  
WHEN an evaluation period concludes with the goal in the `não cumprida` state, THE SYSTEM SHALL set the consecutive fulfilled periods counter (`streak`) to 0.

**Objetivo:**  
Definir deterministicamente a perda da sequência consecutiva quando um ciclo temporal é finalizado sem que o alvo de atividades tenha sido alcançado.

**Ator:**  
Sistema (rotina de virada de ciclo temporal).

**Pré-condições:**
- O período de avaliação foi encerrado (`agora > data_fim`).
- O estado final da meta no ciclo encerrado é `'não cumprida'`.

**Entradas:**
| Dado de Entrada | Tipo | Condição |
|---|---|---|
| `streak` anterior | Inteiro | Qualquer valor maior ou igual a 1. |
| Estado do ciclo encerrado | String | `'não cumprida'`. |

**Regras de negócio:**
1. Quando um período de avaliação encerrar sem que a meta tenha sido cumprida (estado final `'não cumprida'`), o valor do streak deve ser definido como 0 (`streak = 0`).
2. Não são permitidas deduções parciais: o streak nunca é decrementado gradualmente, sendo redefinido estritamente para 0.
3. Se não houver nenhum registro de atividade no período encerrado, o streak deve ser definido como 0.
4. Na criação de uma nova meta para qualquer hábito positivo, o valor inicial do streak deve ser definido como 0.
5. Não existem mecanismos de congelamento ou recuperação de streak nesta especificação.

**Fluxo principal:**
1. O cliente possui uma meta diária com `streak = 14`.
2. No dia anterior, o cliente não registrou atividades suficientes para atingir a `quantidade_minima`.
3. O dia encerrou e o ciclo foi fechado como `'não cumprida'`.
4. Na virada do ciclo, o sistema define deterministicamente `streak = 0`.
5. A meta do novo dia inicia com estado `'ativa'` e `streak = 0`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Valor do campo `streak` gravado como 0 no banco de dados.

**Persistência:**
- Coluna `streak` da meta atualizada para o valor numérico 0.

**Critérios de aceitação:**
- GIVEN uma meta com `streak=10` cujo período encerrou no estado `'não cumprida'`
  WHEN a rotina de virada de período for processada
  THEN o valor do `streak` deve ser definido como 0.
- GIVEN um usuário que cria uma nova meta para um hábito
  WHEN o registro for criado no banco
  THEN o valor inicial do `streak` deve ser estritamente 0.

**Casos-limite:**
- Meta que já possuía `streak = 0` e não foi cumprida novamente: o streak permanece em 0.

**Fora de escopo:**
- Proteção paga de streak ou recuperação manual de sequência.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-05 — Exclusão de Meta sem Exclusão do Hábito

**Descrição EARS:**  
WHEN an authenticated client deletes a goal, THE SYSTEM SHALL remove the goal record without deleting the associated habit or its activity records.

**Objetivo:**  
Permitir que o cliente exclua uma meta existente mantendo intactos o hábito vinculado e todo o seu histórico de registros de atividades.

**Ator:**  
Cliente autenticado (titular da meta/hábito).

**Pré-condições:**
- O cliente possui sessão ativa válida.
- A meta a ser excluída pertence a um hábito positivo do cliente autenticado.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `meta_id` | Inteiro | Sim | Identificador de meta válida pertencente ao cliente autenticado. |

**Regras de negócio:**
1. O cliente autenticado pode excluir sua meta a qualquer momento, independentemente do estado em que ela se encontre (`ativa`, `cumprida` ou `não cumprida`).
2. A exclusão da meta deve remover exclusivamente o registro da meta (`Meta`).
3. A exclusão da meta **não deve excluir nem modificar** a entidade `Habito` associada.
4. A exclusão da meta **não deve excluir nem modificar** os registros de atividade (`RegistroAtividade`) vinculados ao hábito.
5. Após a exclusão da meta, o hábito permanece ativo no sistema e fica liberado para a criação de uma nova meta futura, se o usuário desejar.

**Fluxo principal:**
1. O cliente solicita a exclusão de uma meta associada a um de seus hábitos.
2. O sistema valida que a meta pertence ao cliente autenticado.
3. O sistema remove o registro da meta.
4. O hábito e seus registros de atividades permanecem inalterados no banco de dados.
5. O sistema apresenta confirmação visual de exclusão bem-sucedida.

**Fluxos alternativos e de erro:**
- **Tentativa de exclusão por usuário não titular:** A operação é bloqueada com status de erro de autorização (conforme REQ-META-10).

**Resultado esperado:**
- Registro da meta removido do banco de dados, com hábito e atividades intactos.

**Persistência:**
- Remoção do registro correspondente na tabela de metas. Nenhuma alteração nas tabelas de hábitos ou registros de atividades.

**Critérios de aceitação:**
- GIVEN um cliente autenticado com uma meta e 5 registros de atividades associados ao seu hábito
  WHEN o cliente solicitar a exclusão da meta
  THEN o registro da meta deve ser excluído
  AND o hábito deve continuar existindo no banco de dados
  AND os 5 registros de atividade devem permanecer inalterados.

**Casos-limite:**
- Exclusão de meta com streak positivo: a meta é removida e o streak anterior é descartado junto à meta.

**Fora de escopo:**
- Lixeira ou recuperação de metas excluídas.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-06 — Exibição Numérica do Progresso

**Descrição EARS:**  
WHEN an authenticated client views a goal, THE SYSTEM SHALL display the numerical progress formatted as completed activities over target threshold (`realizado/meta`, e.g., '3/5').

**Objetivo:**  
Apresentar de forma direta, transparente e de fácil leitura a contagem numérica de atividades concluídas em relação à quantidade mínima estabelecida na meta.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente possui meta associada ao hábito em visualização.

**Entradas:**
| Campo | Origem | Descrição |
|---|---|---|
| `total_atividades` | Sum(`RegistroAtividade.quantidade`) | Quantidade acumulada de atividades registradas no período vigente. |
| `quantidade_minima` | Registro da Meta | Limiar mínimo estipulado para a meta. |

**Regras de negócio:**
1. A interface deve apresentar o progresso no formato textual `realizado/meta` (por exemplo: `3/5`, `0/4`, `5/5`).
2. O componente `realizado` corresponde ao somatório `total_atividades` das atividades do hábito registradas dentro do ciclo temporal vigente. Caso não haja atividades registradas, o valor exibido deve ser `0`.
3. O componente `meta` corresponde ao valor de `quantidade_minima` da meta.
4. Caso o número de atividades realizadas ultrapasse a meta (ex.: 7 atividades para uma meta de 5), a exibição numérica deve refletir o valor real atingido (ex.: `7/5`), complementando a barra de progresso percentual que é limitada a 100%.
5. A exibição numérica do progresso deve acompanhar tanto metas no estado `'ativa'` quanto no estado `'cumprida'`.

**Fluxo principal:**
1. O cliente acessa a tela de hábitos ou painel de progresso.
2. O sistema recupera as atividades do período vigente (ex.: 3) e o valor de `quantidade_minima` da meta (ex.: 5).
3. A interface renderiza o indicador numérico no formato `3/5`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Indicador numérico renderizado no formato `realizado/meta` na interface.

**Persistência:**
- Nenhuma alteração no banco de dados (exibição computada em tempo de renderização).

**Critérios de aceitação:**
- GIVEN uma meta com `quantidade_minima = 5`
  WHEN o cliente tiver 3 atividades registradas no período vigente
  THEN a interface deve exibir o progresso numérico como `"3/5"`.
- GIVEN uma meta com `quantidade_minima = 4` sem nenhum registro no período
  WHEN o cliente visualizar a meta
  THEN a interface deve exibir `"0/4"`.
- GIVEN uma meta com `quantidade_minima = 2` e 3 atividades registradas
  WHEN o cliente visualizar a meta
  THEN a interface deve exibir `"3/2"`.

**Casos-limite:**
- Atividade com valor decimal ou fracionário (se suportado): exibição formatada de forma legível.

**Fora de escopo:**
- Conversão de unidades de medida (ex.: minutos para horas).

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-07 — Cálculo do Progresso Percentual

**Descrição EARS:**  
WHEN the progress of a goal is requested, THE SYSTEM SHALL calculate the percentage based on the accumulated activity quantity and the defined minimum quantity, standardized between 0% and 100%.

**Objetivo:**  
Permitir que o cliente acompanhe visualmente a proporção cumprida de sua meta através de uma escala percentual padronizada de 0% a 100%.

**Ator:**  
Sistema (motor de cálculo de métricas).

**Pré-condições:**
- A meta existe e está associada a um hábito positivo.

**Entradas:**
| Dado de Entrada | Origem | Descrição |
|---|---|---|
| `total_atividades` | Sum(`RegistroAtividade.quantidade`) | Atividades do período vigente. |
| `quantidade_minima` | Registro da Meta | Limiar mínimo da meta. |

**Regras de negócio:**
1. O progresso percentual deve ser calculado deterministicamente por:
   $$\text{progresso} = \min\left(100, \frac{\text{total\_atividades}}{\text{quantidade\_minima}} \times 100\right)$$
2. Se não houver atividades registradas no período, o progresso deve ser estritamente `0%`.
3. O progresso percentual exibido deve ser sempre mantido no intervalo entre `0%` e `100%`.
4. Quando o progresso atinge ou ultrapassa 100% (`total_atividades >= quantidade_minima`), a meta deve estar no estado `'cumprida'` (conforme REQ-META-03).
5. Apenas registros de atividades cuja data pertença ao intervalo do período vigente da meta devem ser computados.

**Fluxo principal:**
1. Uma meta possui `quantidade_minima = 5`.
2. O cliente acumula 3 atividades no período.
3. O sistema calcula `(3 / 5) * 100 = 60%`.
4. A interface exibe a barra e o rótulo de progresso com `60%`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Valor percentual calculado entre 0 e 100 retornado para a interface.

**Persistência:**
- Nenhuma alteração persistida diretamente pelo cálculo (valor computado dinamicamente).

**Critérios de aceitação:**
- GIVEN uma meta com `quantidade_minima = 5`
  WHEN o cliente possuir 3 atividades registradas no período
  THEN o progresso percentual deve ser `60%`.
- GIVEN uma meta sem atividades registradas no período
  WHEN o progresso for calculado
  THEN o resultado deve ser estritamente `0%`.
- GIVEN uma meta com `quantidade_minima = 4` e 6 atividades registradas
  WHEN o progresso for calculado
  THEN o progresso percentual exibido deve ser `100%`
  AND o estado da meta deve ser `'cumprida'`.

**Casos-limite:**
- Quantidade mínima igual a 1 e 1 atividade registrada: resulta em exatamente 100% de progresso e transição para cumprida.

**Fora de escopo:**
- Projeção probabilística de alcance de meta futura.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-08 — Confirmação de Criação da Meta

**Descrição EARS:**  
WHEN a goal is successfully created by an authenticated client, THE SYSTEM SHALL display a clear confirmation message to the user acknowledging the goal creation.

**Objetivo:**  
Fornecer feedback visual e explícito ao usuário confirmando que a meta foi devidamente cadastrada e vinculada ao hábito.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O formulário ou requisição de criação de meta foi submetido com parâmetros válidos e persistido no banco de dados.

**Entradas:**
| Dado de Entrada | Origem | Descrição |
|---|---|---|
| Objeto da Meta persistida | Backend | Confirmação de persistência da meta vinculada ao hábito. |

**Regras de negócio:**
1. Após a persistência bem-sucedida de uma nova meta, o sistema deve emitir uma mensagem explícita de sucesso (por exemplo, via framework de mensagens ou payload JSON de sucesso).
2. O conteúdo da confirmação deve indicar com clareza a conclusão da ação (ex.: `"Meta criada com sucesso!"`).
3. A interface deve atualizar a visualização ou redirecionar o usuário para a listagem/detalhes da meta, apresentando seu estado inicial `'ativa'`, streak `0` e indicador numérico `0/meta`.
4. Em caso de falha de validação ou de banco de dados, a mensagem de sucesso não deve ser emitida e deve ser apresentada notificação de erro específica.

**Fluxo principal:**
1. O cliente preenche os campos de meta (ex.: 4 vezes por semana) para um hábito positivo e confirma.
2. O backend valida os dados, persiste a meta e enfileira a notificação de confirmação.
3. A interface recarrega exibindo a notificação `"Meta criada com sucesso!"`.
4. O cliente visualiza o cartão da meta criada em estado ativa.

**Fluxos alternativos e de erro:**
- **Falha de validação:** O sistema não emite a confirmação de criação e re-renderiza o formulário com a indicação dos campos incorretos.

**Resultado esperado:**
- Notificação de confirmação apresentada de forma clara na interface do usuário.

**Persistência:**
- Registro de notificação temporária na sessão/mensagens do usuário.

**Critérios de aceitação:**
- GIVEN um cliente autenticado submetendo dados válidos para criação de meta
  WHEN a operação for concluída com sucesso
  THEN o sistema deve apresentar uma mensagem clara de confirmação ao usuário
  AND a meta deve ser exibida no estado `'ativa'`.

**Casos-limite:**
- Criação via requisição assíncrona (AJAX): resposta JSON com `{"success": true, "message": "Meta criada com sucesso!"}`.

**Fora de escopo:**
- Envio de notificações push ou e-mails transacionais de confirmação.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-STREAK-03 — Streak Nunca Pode Ser Negativo

**Descrição EARS:**  
THE SYSTEM SHALL guarantee that the streak counter is always a non-negative integer (integer >= 0) under all operations and state transitions.

**Objetivo:**  
Assegurar a integridade matemática do contador de sequência, impedindo que o streak assuma valores negativos em qualquer hipótese ou transição de estado.

**Ator:**  
Sistema (modelo e operações de banco de dados).

**Pré-condições:**
- Qualquer operação de persistência, incremento, zeramento ou consulta sobre o streak.

**Entradas:**
| Campo | Tipo | Restrições |
|---|---|---|
| `streak` | Inteiro | Deve ser estritamente maior ou igual a zero (`streak >= 0`). |

**Regras de negócio:**
1. O campo `streak` deve ser implementado no modelo como um inteiro não negativo (`models.PositiveIntegerField(default=0)`).
2. O valor do streak nunca pode ser inferior a zero (`streak >= 0`).
3. Operações de encerramento de ciclos não cumpridos redefinem o streak para `0`, nunca para valores negativos.
4. Tentativas de atribuir valores negativos ao streak devem ser rejeitadas por validação do modelo e do banco de dados.

**Fluxo principal:**
1. O sistema processa transições de ciclo e atualizações da meta.
2. O campo `streak` é persistido respeitando a restrição de valor não negativo.
3. Consultas e relatórios leem valores de streak sempre maiores ou iguais a 0.

**Fluxos alternativos e de erro:**
- **Atribuição inválida:** Qualquer instrução que tente gravar valor menor que zero dispara erro de validação de modelo, impedindo a persistência.

**Resultado esperado:**
- Integridade do campo `streak` preservada com valores estritamente maiores ou iguais a zero.

**Persistência:**
- Coluna `streak` protegida por restrição de verificação (`CheckConstraint(check=Q(streak__gte=0))`) ou `PositiveIntegerField`.

**Critérios de aceitação:**
- GIVEN uma meta existente no sistema
  WHEN o valor do `streak` for consultado após qualquer operação
  THEN o valor retornado deve ser um inteiro maior ou igual a 0.
- GIVEN uma tentativa de persistência com `streak = -1`
  WHEN a validação for executada
  THEN o sistema deve rejeitar a operação com erro de validação.

**Casos-limite:**
- Redefinição de streak que já era 0: permanece em 0 sem sofrer decremento.

**Fora de escopo:**
- Pontuações de penalidade negativa fora do modelo de streak.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-STREAK-04 — Streak Inicial Visível

**Descrição EARS:**  
WHEN a new goal is created, THE SYSTEM SHALL initialize and display its streak counter with the value of 0.

**Objetivo:**  
Garantir que toda meta recém-criada inicie explicitamente com sequência zerada visível na interface antes do encerramento de qualquer ciclo.

**Ator:**  
Cliente autenticado / Sistema.

**Pré-condições:**
- Uma nova meta foi cadastrada e associada a um hábito positivo.

**Entradas:**
| Campo | Origem | Valor Inicial |
|---|---|---|
| `streak` | Criação da meta | `0` |

**Regras de negócio:**
1. Toda meta recém-criada recebe `streak = 0` por padrão no momento da persistência.
2. A interface do usuário deve apresentar de forma clara e visível o contador de streak com o valor `0` (ex.: `"Sequência: 0"` ou `"Streak: 0"`).
3. O valor `0` do streak deve permanecer visível durante todo o primeiro período de vigência da meta até que ocorra o encerramento formal do período com cumprimento.
4. O contador de streak inicial não deve ser ocultado, omitido ou exibido como nulo/vazio.

**Fluxo principal:**
1. O cliente cria uma nova meta para seu hábito positivo.
2. O sistema inicializa a meta com `streak = 0`.
3. Ao visualizar a meta no painel, o cliente vê o streak exibido como `0`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Streak da meta inicializado em 0 e visível no painel do usuário.

**Persistência:**
- Campo `streak` gravado com valor 0 na criação da meta.

**Critérios de aceitação:**
- GIVEN uma meta recém-criada
  WHEN o cliente visualizar os dados da meta
  THEN o contador de streak deve ser exibido com o valor 0.
- GIVEN uma nova instância de meta persistida no banco
  WHEN o campo `streak` for consultado
  THEN o valor persistido deve ser estritamente 0.

**Casos-limite:**
- Visualização imediata logo após a criação da meta: exibe `0` sem necessidade de recarregar páginas externas.

**Fora de escopo:**
- Inicialização de streak com valores herdados ou customizados pelo usuário.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-09 — Metas Apenas para Hábitos Positivos

**Descrição EARS:**  
WHEN an authenticated client attempts to create a goal, THE SYSTEM SHALL allow the operation only when the associated habit is classified as positive.

**Objetivo:**  
Simplificar a primeira versão do sistema de metas e evitar ambiguidade na interpretação de metas para hábitos negativos.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente possui sessão ativa válida.
- O hábito vinculado pertence ao cliente autenticado.

**Entradas:**
| Campo | Origem | Restrições |
|---|---|---|
| `tipo_habito` | `Habito.tipo_habito` | Deve ser estritamente `'positivo'`. |

**Regras de negócio:**
1. Apenas hábitos do tipo `positivo` podem possuir metas vinculadas.
2. Hábitos classificados como `negativo` não podem receber metas nesta versão.
3. A validação deve ocorrer obrigatoriamente no backend, rejeitando a operação caso o hábito associado seja do tipo negativo.
4. Na interface de criação de meta, apenas hábitos classificados como positivos devem ser disponibilizados para seleção.

**Fluxo principal:**
1. O cliente seleciona um hábito classificado como positivo para definir uma meta.
2. O sistema verifica que `habito.tipo_habito == 'positivo'`.
3. A criação da meta prossegue normalmente.

**Fluxos alternativos e de erro:**
- **Tentativa de vincular a hábito negativo:**
  1. O cliente tenta enviar formulário ou chamada de API vinculando uma meta a um hábito negativo.
  2. O backend identifica que `habito.tipo_habito == 'negativo'`.
  3. A criação é rejeitada com erro de validação informando que metas só são permitidas para hábitos positivos.

**Resultado esperado:**
- Metas permitidas exclusivamente para hábitos positivos; bloqueio para hábitos negativos.

**Persistência:**
- Nenhuma alteração persistida em caso de rejeição.

**Critérios de aceitação:**
- GIVEN um hábito positivo
  WHEN o cliente criar uma meta válida
  THEN a criação deve ser permitida.
- GIVEN um hábito negativo
  WHEN o cliente tentar criar uma meta
  THEN a criação deve ser rejeitada pelo sistema.

**Casos-limite:**
- Alteração do tipo do hábito de positivo para negativo: a plataforma deve impedir a conversão enquanto houver meta vinculada ou exigir a exclusão prévia da meta.

**Fora de escopo:**
- Metas de redução de danos ou limites máximos de tolerância para hábitos negativos.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-10 — Controle de Acesso às Metas

**Descrição EARS:**  
WHEN a client attempts to create, edit or delete a goal, THE SYSTEM SHALL allow the operation only if the associated habit belongs to the authenticated client.

**Objetivo:**  
Garantir que clientes não possam modificar metas vinculadas a hábitos de outros usuários, assegurando o isolamento de dados.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente está autenticado na sessão.

**Entradas:**
| Campo | Origem | Validação |
|---|---|---|
| `habito.cliente` | Banco de dados | Deve ser idêntico ao cliente autenticado na sessão. |

**Regras de negócio:**
1. O cliente deve estar devidamente autenticado.
2. O hábito associado à meta deve pertencer ao cliente autenticado (`habito.cliente == cliente_autenticado`).
3. Tentativas de acesso, alteração ou exclusão de metas pertencentes a hábitos de outros usuários devem ser bloqueadas com status de erro de autorização (HTTP 403 ou 404).

**Fluxo principal:**
1. O cliente autenticado solicita a alteração ou exclusão de uma meta.
2. O sistema verifica se o hábito correspondente pertence ao cliente autenticado.
3. Confirmada a titularidade, a operação é executada com sucesso.

**Fluxos alternativos e de erro:**
- **Usuário não proprietário:** O sistema bloqueia a requisição e não efetua nenhuma modificação.

**Resultado esperado:**
- Operação realizada com sucesso para o proprietário; bloqueio imediato para terceiros.

**Persistência:**
- Modificações autorizadas gravadas no banco de dados.

**Critérios de aceitação:**
- GIVEN uma meta pertencente ao cliente autenticado
  WHEN ele editar ou excluir a meta
  THEN a operação deve ser permitida.
- GIVEN uma meta pertencente a outro cliente
  WHEN houver tentativa de edição ou exclusão
  THEN a operação deve ser bloqueada.

**Casos-limite:**
- Sessão expirada durante a submissão: redireciona para login e bloqueia a ação.

**Fora de escopo:**
- Delegação formal de administração de conta para terceiros.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-11 — Exibição do Estado da Meta

**Descrição EARS:**  
WHEN an authenticated client views a goal, THE SYSTEM SHALL display its current state as `ativa`, `cumprida` or `não cumprida`.

**Objetivo:**  
Permitir que o cliente identifique com facilidade e rapidez a situação atual de cada meta acompanhada.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente possui meta cadastrada para seu hábito.

**Entradas:**
| Campo | Origem | Descrição |
|---|---|---|
| `estado` | Registro da Meta | Estado atual da meta (`ativa`, `cumprida` ou `não cumprida`). |

**Regras de negócio:**
1. O estado exibido na interface deve corresponder fielmente ao estado persistido da meta no banco de dados.
2. Somente os três estados previstos são permitidos:
   - `'ativa'`
   - `'cumprida'`
   - `'não cumprida'`
3. A interface deve apresentar o estado com destaque visual (badges, cores ou textos descritivos distintos).

**Fluxo principal:**
1. O cliente acessa a tela de visualização de hábitos/metas.
2. O sistema recupera a meta e seu estado atual.
3. A interface renderiza o indicador de estado correspondente.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Estado renderizado com clareza na interface.

**Persistência:**
- Leitura do banco de dados sem alteração de estado.

**Critérios de aceitação:**
- GIVEN uma meta no estado `'cumprida'`
  WHEN o cliente visualizar a meta
  THEN a interface deve apresentar o indicador `'cumprida'`.
- GIVEN uma meta no estado `'ativa'`
  WHEN o cliente visualizar a meta
  THEN a interface deve apresentar o indicador `'ativa'`.
- GIVEN uma meta no estado `'não cumprida'`
  WHEN o cliente visualizar a meta
  THEN a interface deve apresentar o indicador `'não cumprida'`.

**Casos-limite:**
- Transição visual em tempo real após salvar atividade: o estado atualiza sem recarregamento se implementado com frontend assíncrono.

**Fora de escopo:**
- Estados intermediários ou personalizados (ex.: "em risco", "quase lá").

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-STREAK-05 — Exibição do Streak Atual

**Descrição EARS:**  
WHEN an authenticated client views a goal, THE SYSTEM SHALL display the current streak associated with that goal.

**Objetivo:**  
Permitir que o cliente acompanhe visualmente sua sequência acumulada de períodos consecutivos de cumprimento da meta.

**Ator:**  
Cliente autenticado.

**Pré-condições:**
- O cliente possui meta cadastrada.

**Entradas:**
| Campo | Origem | Descrição |
|---|---|---|
| `streak` | Registro da Meta | Contador numérico de períodos consecutivos cumpridos. |

**Regras de negócio:**
1. O valor de streak exibido na interface deve corresponder exatamente ao valor persistido na meta.
2. O valor mínimo exibido é `0`.
3. Uma meta recém-criada deve apresentar streak igual a `0` (conforme REQ-STREAK-04).
4. O valor deve ser apresentado acompanhado de identificação compreensível (ex.: ícone de fogo/chama ou texto explicativo `"Sequência de X períodos"`).

**Fluxo principal:**
1. O cliente acessa a interface de metas.
2. O sistema busca o valor de `streak` da meta no banco de dados.
3. A interface exibe o contador com o valor correspondente.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Valor do streak apresentado de forma clara e motivadora na tela.

**Persistência:**
- Nenhuma alteração no banco de dados (operação de leitura).

**Critérios de aceitação:**
- GIVEN uma meta com `streak = 4`
  WHEN o cliente visualizar a meta
  THEN o sistema deve exibir o valor 4.
- GIVEN uma meta recém-criada
  WHEN ela for exibida pela primeira vez
  THEN o streak deve aparecer visivelmente como 0.

**Casos-limite:**
- Streak elevado (ex.: 52 semanas): valor renderizado adequadamente sem quebras de layout.

**Fora de escopo:**
- Gráficos históricos de evolução do streak ao longo dos anos.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

## Síntese de Regras de Negócio e Estados

### Matriz de Transição de Estados da Meta

| Estado Inicial | Evento Gatilho | Condição | Estado Final | Impacto no Streak |
|---|---|---|---|---|
| Inexistente | Criação da meta | `quantidade_minima >= 1` (hábito positivo) | `ativa` | `streak = 0` |
| `ativa` | Registro/edição de atividade | `total_atividades >= quantidade_minima` e período vigente | `cumprida` | Mantém streak atual (incrementa apenas na virada) |
| `cumprida` | Edição/exclusão de atividade | `total_atividades < quantidade_minima` e período vigente | `ativa` | Mantém streak atual |
| `ativa` | Virada de período (`agora > data_fim`) | `total_atividades < quantidade_minima` | `não cumprida` (reinicia ciclo como `ativa`) | `streak = 0` |
| `cumprida` | Virada de período (`agora > data_fim`) | `total_atividades >= quantidade_minima` | Reinicia ciclo como `ativa` | `streak = streak + 1` |
| `não cumprida` | Virada de período (`agora > data_fim`) | Início de novo ciclo temporal | `ativa` (novo ciclo) | Inicia com `streak = 0` |
