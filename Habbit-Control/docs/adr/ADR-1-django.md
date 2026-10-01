# ADR-001 — Uso do Django

## Contexto

O Habbit Control necessita de uma estrutura para desenvolvimento de uma aplicação web com autenticação de usuários,

persistência de dados, regras de negócio e diferentes páginas para interação com o sistema.

## Decisão

Foi adotado o framework Django, utilizando Python, para o desenvolvimento da aplicação web.

O Django será utilizado para organizar a lógica da aplicação, o acesso aos dados, as rotas e a integração com os templates
do sistema.

## Consequências

### Positivas

- Organização do sistema utilizando a estrutura fornecida pelo Django.
- Integração com banco de dados através do ORM.
- Recursos para desenvolvimento de autenticação e controle de acesso.
- Possibilidade de criação de testes automatizados.
- Separação entre lógica da aplicação e interface.

### Limitações

- O projeto fica dependente do framework Django.