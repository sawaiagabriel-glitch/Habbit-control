# Metas e Sequências

## Status

Funcionalidade planejada — ainda não implementada.

---

## Requisitos

### REQ-META-01
WHEN an authenticated client defines a target for a habit, THE SYSTEM SHALL allow setting a minimum activity threshold (`quantidade_minima`) for a defined period utilizing solely the currently supported intervals: `'dia'`, `'semana'`, `'mes'`, or `'ano'`.

#### Rastreabilidade:
- Implementação: ainda não implementada
- Teste automatizado: ainda não implementado

---

### REQ-META-02
WHILE the current evaluation period is ongoing and the cumulative volume of registered activities has not reached the defined minimum threshold, THE SYSTEM SHALL maintain the goal in the `ativa` state.

#### Rastreabilidade:
- Implementação: ainda não implementada
- Teste automatizado: ainda não implementado

---

### REQ-META-03
WHEN the cumulative volume of registered activities reaches or exceeds the minimum threshold within the active evaluation period, THE SYSTEM SHALL transition the goal state to `cumprida`.

#### Rastreabilidade:
- Implementação: ainda não implementada
- Teste automatizado: ainda não implementado

---

### REQ-META-04
WHEN an evaluation period concludes without the cumulative volume of registered activities reaching the minimum threshold, THE SYSTEM SHALL transition the goal state for that period to `não cumprida`.

#### Rastreabilidade:
- Implementação: ainda não implementada
- Teste automatizado: ainda não implementado

---

### REQ-STREAK-01
WHEN a goal reaches the `cumprida` state within an evaluation period, THE SYSTEM SHALL increment the consecutive fulfilled periods counter (`streak`) by 1.

#### Rastreabilidade:
- Implementação: ainda não implementada
- Teste automatizado: ainda não implementado

---

### REQ-STREAK-02
WHEN an evaluation period concludes with the goal in the `não cumprida` state, THE SYSTEM SHALL reset or interrupt the consecutive fulfilled periods sequence (`streak`) to 0.

#### Rastreabilidade:
- Implementação: ainda não implementada
- Teste automatizado: ainda não implementado

---

## Regras de Negócio

### 1. Quantidade Mínima
- A meta é mensurada através de um valor inteiro positivo (`quantidade_minima`) de atividades registradas.
- O progresso é cumulativo dentro do período correspondente (somatório dos registros de atividade daquele período).

### 2. Influência do Período
- Os períodos suportados são restritos aos já existentes no sistema: `dia`, `semana`, `mes` e `ano`.
- Cada período possui limites temporais bem definidos (início e término do ciclo correspondente).
- A contagem de atividades registradas é restrita ao intervalo temporal do período vigente.

### 3. Mudança de Estado
Uma meta pode assumir exatamente três estados:
- **`ativa`**: Estado inicial enquanto o período estiver em andamento e o valor cumulativo for menor que a quantidade mínima definida.
- **`cumprida`**: Ativado assim que o volume de atividades no período atingir ou ultrapassar a quantidade mínima exigida.
- **`não cumprida`**: Atribuído automaticamente no fechamento do período caso a quantidade mínima não tenha sido alcançada.

### 4. Sequência (`streak`)
- A sequência contabiliza o número de períodos consecutivos em que a meta foi considerada `cumprida`.
- **Incremento**: A cada período concluído com cumprimento da meta, o contador de sequência é incrementado em 1.
- **Interrupção / Reinício**: Ao término de um período sem cumprimento da meta (`não cumprida`), a sequência de períodos consecutivos é interrompida e reiniciada em 0.
- Não existem tolerâncias, congelamentos de streak ou regras de terceiros nesta especificação.

---

## Rastreabilidade

- **REQ-META-01**:
  - Implementação: ainda não implementada
  - Teste automatizado: ainda não implementado
- **REQ-META-02**:
  - Implementação: ainda não implementada
  - Teste automatizado: ainda não implementado
- **REQ-META-03**:
  - Implementação: ainda não implementada
  - Teste automatizado: ainda não implementado
- **REQ-META-04**:
  - Implementação: ainda não implementada
  - Teste automatizado: ainda não implementado
- **REQ-STREAK-01**:
  - Implementação: ainda não implementada
  - Teste automatizado: ainda não implementado
- **REQ-STREAK-02**:
  - Implementação: ainda não implementada
  - Teste automatizado: ainda não implementado

---

## Ordem futura de implementação

A implementação das novas regras de negócio deverá ser realizada futuramente em etapas rigorosas orientadas por TDD (*Test-Driven Development*):

1. **Etapa 1 — Regras Básicas de Metas**:
   - Definição de quantidade mínima de atividades por período (`dia`, `semana`, `mes`, `ano`);
   - Atribuição do estado inicial `ativa`;
   - Transição automática para `cumprida` ao atingir a quantidade mínima;
   - Transição automática para `não cumprida` quando o período encerrar sem que a quantidade mínima tenha sido alcançada.

2. **Etapa 2 — Funcionalidade de Sequência (`streak`)**:
   - Manutenção do contador de períodos consecutivos cumpridos;
   - Incremento da sequência a cada período cumprido;
   - Interrupção e reinício da sequência para 0 quando o período terminar sem cumprimento.

### Fluxo de Trabalho (TDD)
Cada etapa futura seguirá estritamente o ciclo:
1. **Spec**: Validação dos requisitos documentados.
2. **Teste automatizado**: Criação de testes unitários/integração cobrindo o requisito.
3. **Teste falhando (RED)**: Execução para confirmar falha controlada do teste antes do código.
4. **Implementação mínima**: Escrita do código estritamente necessário para atender à regra.
5. **Teste passando (GREEN)**: Execução para confirmar aprovação de todos os testes.
6. **Auditoria de aderência à spec**: Revisão de cobertura e rastreabilidade entre código, testes e especificação.
