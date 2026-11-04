# ADR-001 — Uso do Django como framework

## Status

Aceito

## Contexto

O Habbit-Control é uma aplicação web que precisa oferecer cadastro de usuários, autenticação, persistência de dados, gerenciamento de hábitos, registros de atividades, metas, parceiro de acompanhamento e regras de negócio testáveis.

Era necessário escolher uma tecnologia que permitisse desenvolver essas funcionalidades de forma organizada, com segurança embutida e suporte a testes automatizados.

## Decisão

Foi adotado o framework Django, com Python como linguagem principal do backend.

O projeto utiliza a estrutura do Django com:

- models e ORM;
- views e URLs;
- forms;
- templates;
- migrations;
- framework de testes.

A organização funcional ficou em duas apps:

- `login_cadastro_app` — Cliente, Parceiro, cadastro e autenticação;
- `pagina_interna` — hábitos, atividades, metas, dashboard e APIs internas.

## Alternativas consideradas

- Flask / FastAPI com stack manual de ORM, autenticação e templates — maior flexibilidade, porém mais trabalho para CSRF, admin, migrations e convenções.
- Framework full-stack JavaScript — afastaria o time do ecossistema Python já adotado no projeto acadêmico.

## Consequências

### Positivas

- integração com banco de dados através do ORM;
- suporte a migrations versionadas;
- CSRF, sessões e hashing de senha disponíveis no framework;
- estrutura clara para apps, templates e testes;
- facilidade para TDD das regras de domínio.

### Negativas

- exige conhecimento das convenções do Django;
- algumas funcionalidades simples dependem da organização do framework;
- o projeto fica acoplado ao ciclo de vida e padrões do Django.
