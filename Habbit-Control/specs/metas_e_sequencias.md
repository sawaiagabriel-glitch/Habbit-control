# Especificação: Metas e Sequências (Streak)

## Status do Módulo
**NÃO IMPLEMENTADO** — Funcionalidade planejada para implementação futura orientada por desenvolvimento orientado a testes (TDD).

## Visão Geral do Módulo
O módulo de metas e sequências permite que os clientes estabeleçam alvos objetivos de frequência para seus hábitos dentro de intervalos padronizados (`dia`, `semana`, `mes`, `ano`). O sistema avalia deterministicamente o cumprimento da meta através do somatório de atividades registradas no intervalo temporal, gerenciando transições de estado da meta (`ativa`, `cumprida`, `não cumprida`) e mantendo o histórico de períodos consecutivos bem-sucedidos através de um contador de sequência (`streak`).

---

## Requisitos do Sistema

### REQ-META-01 — Definição de Meta Vinculada ao Hábito

**Descrição EARS:**  
WHEN an authenticated client defines a target for a habit, THE SYSTEM SHALL allow setting a minimum activity threshold (`quantidade_minima`, integer >= 1) for an evaluation period restricted to 'dia', 'semana', 'mes', or 'ano', associating the goal with exactly one `Habito`.

**Objetivo:**  
Permitir a parametrização de um limiar mínimo quantitativo de execuções exigidas dentro de um ciclo temporal regular para um hábito específico.

**Ator:**  
Cliente autenticado (titular do hábito).

**Pré-condições:**
- O cliente possui sessão ativa válida.
- O hábito vinculado existe e pertence ao cliente autenticado.

**Entradas:**
| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `habito_id` | Inteiro | Sim | Deve pertencer a um registro ativo de `Habito` do cliente autenticado. Relação de 1 meta ativa por hábito. |
| `quantidade_minima` | Inteiro | Sim | Inteiro estritamente maior ou igual a 1 (`quantidade_minima >= 1`). Valores menores que 1 são inválidos. |
| `periodo` | String | Sim | Deve ser estritamente um dos 4 valores permitidos: `'dia'`, `'semana'`, `'mes'` ou `'ano'`. |

**Regras de negócio:**
1. A meta deve estar associada a exatamente um hábito (`Habito`) por meio de chave estrangeira.
2. Cada hábito deve possuir no máximo uma meta ativa por período de avaliação.
3. A `quantidade_minima` é um número inteiro positivo (`PositiveIntegerField`) com valor mínimo permitido igual a 1.
4. O campo `periodo` aceita exclusivamente os quatro intervalos temporais já homologados na plataforma:
   - `'dia'`
   - `'semana'`
   - `'mes'`
   - `'ano'`
5. **Limites temporais determinísticos do período (fuso horário `America/Sao_Paulo`):**
   - **`'dia'`**: Inicia às 00:00:00 da data e encerra às 23:59:59 da mesma data;
   - **`'semana'`**: Inicia na segunda-feira às 00:00:00 e encerra no domingo subsequente às 23:59:59;
   - **`'mes'`**: Inicia no primeiro dia do mês civil (dia 01) às 00:00:00 e encerra no último dia do mesmo mês (dia 28, 29, 30 ou 31, conforme calendário gregoriano) às 23:59:59;
   - **`'ano'`**: Inicia em 01 de janeiro às 00:00:00 e encerra em 31 de dezembro às 23:59:59 do mesmo ano civil.
6. Ao ser criada, a meta deve receber o estado inicial `'ativa'`.
7. O contador de sequência (`streak`) associado à meta deve receber o valor inicial igual a 0.
8. DECISÃO PENDENTE: Definir se a criação de meta para hábitos do tipo `'negativo'` deve utilizar a mesma lógica de `quantidade_minima` (limiar de abstinência) ou se para hábitos negativos a meta deve ser interpretada como um teto máximo tolerado (`quantidade_maxima`), onde ultrapassar o valor desqualifica a meta.

**Fluxo principal:**
1. O cliente escolhe um hábito e define uma meta com `quantidade_minima = 5` e `periodo = "semana"`.
2. O sistema valida que `quantidade_minima >= 1` e que `periodo` pertence à lista permitida.
3. O sistema cria o registro da meta com estado `'ativa'` e `streak = 0`.
4. O sistema vincula a meta ao hábito especificado e associa o ciclo temporal vigente.

**Fluxos alternativos e de erro:**
- **Quantidade mínima menor que 1:** Se o usuário submeter `quantidade_minima <= 0`, o sistema deve rejeitar a criação com erro de validação.
- **Período inválido:** Se o usuário submeter período fora da lista permitida (ex.: `"quinzena"`), o sistema deve rejeitar com erro de validação.

**Resultado esperado:**
- Registro de meta persistido com estado inicial `'ativa'` e `streak = 0`.

**Persistência:**
- Tabela de metas: inserção de registro contendo `habito_id`, `quantidade_minima`, `periodo`, `estado="ativa"`, `streak=0`, `data_inicio` e `data_criacao`.

**Critérios de aceitação:**
- GIVEN um hábito válido pertencente ao cliente autenticado
  WHEN o cliente cadastrar meta com `quantidade_minima=3` e `periodo="semana"`
  THEN o sistema deve persistir a meta com estado `'ativa'`
  AND o valor do `streak` deve ser 0.
- GIVEN uma tentativa de criação de meta com `quantidade_minima=0`
  WHEN a requisição for processada
  THEN o sistema deve rejeitar a persistência e retornar erro de validação.

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
4. Durante o estado `'ativa'`, a interface deve exibir o progresso percentual computado como `(total_atividades / quantidade_minima) * 100`, limitado entre 0% e 99.9%.

**Fluxo principal:**
1. O sistema calcula o progresso de uma meta semanal cuja `quantidade_minima` é 5.
2. O usuário possui 2 atividades registradas na semana corrente.
3. O sistema calcula `total_atividades = 2`.
4. Como `2 < 5` e o domingo 23:59:59 ainda não foi ultrapassado, a meta permanece no estado `'ativa'`.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Meta apresentada com status `'ativa'` e indicador visual de progresso proporcional.

**Persistência:**
- O estado da meta permanece gravado como `'ativa'`.

**Critérios de aceitação:**
- GIVEN uma meta com `quantidade_minima=4` no período semanal corrente
  WHEN o usuário acumular 3 atividades e o período ainda não tiver encerrado
  THEN o estado da meta deve ser `'ativa'`.

**Casos-limite:**
- Meta recém-criada sem nenhum registro no período corrente: `total_atividades` é 0 e o estado permanece `'ativa'`.

**Fora de escopo:**
- Congelamento ou pausa temporária voluntária de metas ativas.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-03 — Transição Imediata para o Estado Cumprida

**Descrição EARS:**  
WHEN the cumulative volume of registered activities reaches or exceeds the minimum threshold within the active evaluation period, THE SYSTEM SHALL transition the goal state to `cumprida`.

**Objetivo:**  
Reconhecer imediatamente o atingimento do alvo estipulado pelo cliente logo que o volume cumulativo necessário for alcançado dentro do ciclo.

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
   - O carimbo temporal de conclusão (`data_cumprimento`) deve ser registrado com a data/hora atual da ocorrência.
3. Se a quantidade registrada ultrapassar a meta (`total_atividades > quantidade_minima`):
   - A meta permanece no estado `'cumprida'`;
   - O volume excedente é registrado e exibido nas métricas, mas não gera saldo acumulável para ciclos temporais futuros.
4. **Reversibilidade intra-período:** Se um cliente editar ou excluir um registro de atividade do período corrente e o novo somatório recair para `total_atividades < quantidade_minima`, o estado da meta deve retornar imediatamente de `'cumprida'` para `'ativa'`.

**Fluxo principal:**
1. Uma meta possui `quantidade_minima = 3` na semana.
2. O usuário registra a 3ª atividade na quarta-feira.
3. O sistema recalcula o total acumulado da semana para 3.
4. Como `3 >= 3`, o estado da meta muda imediatamente de `'ativa'` para `'cumprida'`.
5. A interface exibe badge visual de meta cumprida.

**Fluxos alternativos e de erro:**
- **Reversão por redução de quantidade:** Na quinta-feira, o usuário reduz a quantidade da atividade de quarta-feira de 1 para 0. O novo total torna-se 2. Como `2 < 3`, o sistema reverte o estado da meta de `'cumprida'` para `'ativa'`.

**Resultado esperado:**
- Estado da meta atualizado para `'cumprida'` no banco de dados.

**Persistência:**
- Coluna `estado` da tabela de metas atualizada para `'cumprida'`.

**Critérios de aceitação:**
- GIVEN uma meta ativa com `quantidade_minima=5`
  WHEN a soma de atividades do período atingir 5
  THEN o estado da meta deve mudar para `'cumprida'`.
- GIVEN uma meta cumprida com soma de atividades igual a 5
  WHEN uma atividade de valor 1 do período for excluída reduzindo a soma para 4
  THEN o estado da meta deve retornar para `'ativa'`.

**Casos-limite:**
- Adição em lote de atividades que ultrapasse a meta (ex.: meta de 2, adiciona 5): a meta transiciona diretamente para `'cumprida'`.

**Fora de escopo:**
- Bonificações financeiras ou premiações por alcance antecipado da meta.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

### REQ-META-04 — Fechamento de Período e Transição para Não Cumprida

**Descrição EARS:**  
WHEN an evaluation period concludes and the cumulative volume of registered activities has not reached the minimum threshold, THE SYSTEM SHALL transition the goal state for that period to `não cumprida` and open a new evaluation period with state `ativa`.

**Objetivo:**  
Consolidar formalmente o resultado de encerramento do ciclo temporal, penalizando o não cumprimento da meta no fechamento do período e inicializando o novo ciclo.

**Ator:**  
Sistema (rotina programada de fechamento de ciclo temporal / *cron*).

**Pré-condições:**
- O carimbo temporal atingiu ou ultrapassou o término do período vigente (`agora > data_fim`).
- O estado da meta no encerramento permanece como `'ativa'`.

**Entradas:**
| Evento disparador | Condição |
|---|---|
| Virada do período temporal | `agora > data_fim` e `total_atividades < quantidade_minima`. |

**Regras de negócio:**
1. A rotina de fechamento de ciclo deve ser executada deterministicamente à meia-noite (00:00:00) seguinte ao encerramento do período:
   - Para `'dia'`: diariamente às 00:00:00;
   - Para `'semana'`: às segundas-feiras às 00:00:00;
   - Para `'mes'`: no primeiro dia de cada mês civil às 00:00:00;
   - Para `'ano'`: no dia 01 de janeiro às 00:00:00.
2. Se ao término do período a meta ainda estiver no estado `'ativa'`:
   - O estado do ciclo encerrado deve transicionar definitivamente para `'não cumprida'`;
   - O valor do `streak` da meta deve ser definido como 0 (`streak = 0`), conforme REQ-STREAK-02.
3. Se não houver nenhum registro de atividade associado ao hábito durante todo o período encerrado (`total_atividades == 0`), a meta do período encerrado deve transicionar obrigatoriamente para `'não cumprida'`.
4. Uma vez que o ciclo foi encerrado como `'não cumprida'`, esse registro histórico torna-se imutável.
5. Imediatamente após o fechamento, o sistema deve inicializar o próximo ciclo de avaliação para a mesma meta:
   - Novo intervalo temporal com `data_inicio` e `data_fim` atualizados para o período subsequente;
   - Estado inicial do novo ciclo definido como `'ativa'`;
   - Contagem acumulada de atividades reiniciada a partir de 0.
6. DECISÃO PENDENTE: Definir a política exata para registros retroativos efetuados após a virada do período (ex.: usuário insere na terça-feira uma atividade retroativa referente ao domingo do período já encerrado). Definir se o sistema mantém o período anterior estritamente imutável como `'não cumprida'` ou se recalcula o histórico e restaura o `streak`.

**Fluxo principal:**
1. Uma meta semanal possui `quantidade_minima = 4`.
2. Durante a semana, o cliente registra apenas 2 atividades.
3. No domingo às 23:59:59, o período se encerra.
4. Às 00:00:00 da segunda-feira, a rotina de virada de período é executada.
5. O sistema constata que `total_atividades = 2` e `2 < 4`.
6. A meta da semana concluída transiciona para `'não cumprida'`.
7. O sistema define o valor do `streak` como 0.
8. Um novo ciclo semanal é aberto com estado `'ativa'` e meta de 4 para a nova semana.

**Fluxos alternativos e de erro:**
- Não aplicável.

**Resultado esperado:**
- Histórico do período anterior gravado como `'não cumprida'`.
- Valor de streak definido como 0.
- Novo ciclo aberto com estado `'ativa'`.

**Persistência:**
- Registro do período anterior consolidado com `estado="não cumprida"`.
- Novo ciclo instanciado na tabela de controle de metas com `estado="ativa"`.

**Critérios de aceitação:**
- GIVEN uma meta com `quantidade_minima=5` na semana encerrada com apenas 3 atividades registradas
  WHEN ocorrer a virada de período na segunda-feira às 00:00:00
  THEN o estado do ciclo encerrado deve ser `'não cumprida'`
  AND o contador de streak deve ser definido como 0
  AND um novo ciclo semanal deve ser criado com estado `'ativa'`.

**Casos-limite:**
- Ausência total de login ou interação do usuário por semanas consecutivas: cada período transcorrido sem atividades deve ser registrado como ciclo `'não cumprida'` e o `streak` mantido em 0.

**Fora de escopo:**
- Tolerância de carência (*grace period*) de horas adicionais após o fechamento.

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
2. O incremento do streak ocorre estritamente no momento do fechamento formal do período de avaliação (às 00:00:00 da virada do ciclo).
3. Se o cliente atingir a `quantidade_minima` de forma antecipada durante a vigência do período, a meta transiciona imediatamente para `'cumprida'` (conforme REQ-META-03), porém o valor numérico do `streak` não é incrementado antecipadamente; ele só é acrescido no encerramento formal do período.
4. Na virada do ciclo temporal, se a meta do período encerrado estiver como `'cumprida'`:
   - O valor do streak deve ser incrementado em exatamente 1 (`streak = streak + 1`);
   - O novo valor é atribuído à meta para vigorar no ciclo que se inicia.
5. Se o cliente cumprir a meta em períodos consecutivos consecutivos (ex.: 3 semanas seguidas cumpridas), o streak acumula sucessivamente (0 -> 1 -> 2 -> 3).

**Fluxo principal:**
1. O cliente possui uma meta semanal com `streak = 2`.
2. Durante a semana, atinge a meta na sexta-feira. O estado passa para `'cumprida'`, mas o streak permanece 2 até a virada.
3. No encerramento da semana (segunda-feira 00:00:00), o sistema verifica que o ciclo terminou com estado `'cumprida'`.
4. O sistema calcula `novo_streak = 2 + 1 = 3`.
5. O valor `streak = 3` é persistido para a meta no novo ciclo.

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
2. Não são permitidas frases ou regras ambíguas: o streak nunca é decrementado parcialmente nem mantido em tolerância. O valor do streak é definido estritamente como 0.
3. Se não houver nenhum registro de atividade no período encerrado, o streak deve ser definido como 0.
4. Na criação de uma nova meta para qualquer hábito, o valor inicial do streak deve ser definido como 0.
5. Não existem mecanismos de "congelamento de streak", "dias de folga" ou "recuperação de sequência" nesta especificação.

**Fluxo principal:**
1. O cliente possui uma meta diária com `streak = 14`.
2. No dia de ontem, o cliente não registrou atividades suficientes para atingir a `quantidade_minima`.
3. O dia encerrou e o ciclo foi fechado como `'não cumprida'`.
4. Às 00:00:00 do novo dia, o sistema executa a rotina de virada.
5. O sistema define deterministicamente `streak = 0`.
6. A meta do novo dia inicia com estado `'ativa'` e `streak = 0`.

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
- Proteção paga de streak ou compras no app para restaurar sequências perdidas.

**Rastreabilidade:**
- Implementação: Não implementado (Funcionalidade planejada)
- Template/JS: Não implementado
- Testes existentes: Não coberto por teste automatizado

---

## Síntese de Regras de Negócio e Estados

### Matriz de Transição de Estados da Meta

| Estado Inicial | Evento Gatilho | Condição | Estado Final | Impacto no Streak |
|---|---|---|---|---|
| Inexistente | Criação da meta | `quantidade_minima >= 1` | `ativa` | `streak = 0` |
| `ativa` | Registro/edição de atividade | `total_atividades >= quantidade_minima` e período vigente | `cumprida` | Mantém streak atual (incrementa apenas na virada) |
| `cumprida` | Edição/exclusão de atividade | `total_atividades < quantidade_minima` e período vigente | `ativa` | Mantém streak atual |
| `ativa` | Virada de período (`agora > data_fim`) | `total_atividades < quantidade_minima` | `não cumprida` | `streak = 0` |
| `cumprida` | Virada de período (`agora > data_fim`) | `total_atividades >= quantidade_minima` | Encerrada (Cumprida) | `streak = streak + 1` |
| `não cumprida` | Virada de período (`agora > data_fim`) | Início de novo ciclo temporal | `ativa` (novo ciclo) | Inicia com `streak = 0` |
