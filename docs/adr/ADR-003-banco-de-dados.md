# ADR-003 — Estratégia de banco de dados

**Status:** Aceito

## Contexto

O Habbit Control precisa armazenar de forma persistente informações como:

- clientes;
- hábitos;
- registros de atividades;
- metas;
- streaks;
- relacionamentos de acompanhamento.

Também é necessário que o projeto seja fácil de executar durante o desenvolvimento local, sem exigir uma configuração complexa de banco de dados.

Ao mesmo tempo, o sistema deve permitir o uso de outro banco em ambientes externos.

## Decisão

O ambiente local utilizará **SQLite**, por ser simples de configurar e possuir integração direta com o Django.

Em ambientes externos, a configuração do banco poderá ser feita utilizando a variável de ambiente:

`DATABASE_URL`

As alterações na estrutura do banco serão controladas através do sistema de **migrations do Django**.

## Consequências

### Positivas

- configuração local simples;
- não exige instalação de um servidor de banco de dados para desenvolvimento;
- integração direta com o Django;
- migrations permitem acompanhar alterações na estrutura dos dados;
- possibilidade de utilizar outro banco em ambiente externo;
- facilita a execução do projeto por outros integrantes da equipe.

### Negativas

- SQLite possui limitações para aplicações com muitos acessos simultâneos;
- podem existir diferenças de comportamento entre SQLite e outros bancos;
- alterações nos models exigem criação e aplicação correta das migrations.