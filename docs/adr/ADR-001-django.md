# ADR-001 — Uso do Django como framework

**Status:** Aceito

## Contexto

O Habbit Control é uma aplicação web que precisa oferecer cadastro de usuários, autenticação, persistência de dados, gerenciamento de hábitos, registros de atividades e regras de negócio.

Era necessário utilizar uma tecnologia que permitisse desenvolver essas funcionalidades de forma organizada e integrada.

## Decisão

Foi escolhido o framework Django, utilizando Python como linguagem principal do backend.

O projeto utiliza a estrutura do Django com models, views, forms, templates e sistema de migrations.

## Consequências

### Positivas

- integração com banco de dados através do ORM;
- suporte a migrations;
- estrutura organizada para aplicações web;
- recursos de segurança já disponíveis no framework;
- facilidade para criação de testes automatizados.

### Negativas

- exige conhecimento da estrutura e convenções do Django;
- algumas funcionalidades simples dependem da organização definida pelo framework.