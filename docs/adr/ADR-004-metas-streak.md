# ADR-004 — Metas, estados e streak

**Status:** Aceito

## Contexto

O Habbit Control precisa oferecer funcionalidades que vão além do cadastro e gerenciamento básico de hábitos.

Para que o sistema acompanhe a evolução do usuário de forma objetiva, é necessário permitir a definição de metas e o acompanhamento do cumprimento dessas metas ao longo do tempo.

Também é necessário registrar sequências de períodos cumpridos para representar a constância do usuário.

## Decisão

Será implementado um sistema de **metas** vinculado aos hábitos.

Cada meta deverá possuir:

- hábito associado;
- quantidade mínima;
- período de avaliação;
- estado;
- streak;
- data de início;
- data de término.

Os períodos permitidos serão:

- dia;
- semana;
- mês;
- ano.

Os estados possíveis serão:

- `ativa`;
- `cumprida`;
- `não cumprida`.

Uma meta será criada inicialmente com:

- estado `ativa`;
- streak igual a `0`.

Quando a quantidade de atividades registrada no período atingir ou ultrapassar a quantidade mínima, a meta deverá passar para o estado `cumprida`.

Quando o período terminar sem atingir a quantidade mínima, a meta deverá ser encerrada como `não cumprida`.

O streak representará a quantidade de períodos consecutivos em que a meta foi cumprida.

As regras principais serão:

- período cumprido: `streak = streak + 1`;
- período não cumprido: `streak = 0`.

As regras de metas e streak deverão possuir testes automatizados e serão desenvolvidas preferencialmente utilizando TDD.

## Consequências

### Positivas

- adiciona regras de negócio claras ao sistema;
- permite acompanhar a evolução do usuário;
- cria estados e transições no domínio;
- permite medir constância através do streak;
- aumenta a complexidade funcional do sistema além de um CRUD simples;
- facilita a criação de testes de regras de negócio.

### Negativas

- aumenta a complexidade da lógica do sistema;
- exige controle correto de datas e períodos;
- exige tratamento das transições de estado;
- exige testes para diferentes cenários e casos-limite;
- será necessário garantir que o streak seja atualizado corretamente no encerramento de cada período.