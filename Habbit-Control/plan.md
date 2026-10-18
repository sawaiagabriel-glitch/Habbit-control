# Habbit Control — Plano Técnico

## 1. Tecnologias

O sistema utiliza:

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite para banco de dados local
- Git e GitHub para versionamento e trabalho colaborativo

## 2. Estrutura do Sistema

O projeto utiliza o framework Django.

A aplicação é organizada em:

- apps: aplicações e regras principais do sistema;
- habit_control: configurações gerais do projeto Django;
- templates: páginas HTML;
- static: arquivos estáticos, como CSS e JavaScript;
- docs: documentação técnica do projeto;
- tests: testes do sistema.

## 3. Entidades Principais

### Cliente

Representa o usuário principal do sistema.

Responsabilidades:
- possuir uma conta;
- cadastrar hábitos;
- definir metas;
- registrar atividades;
- acompanhar sua evolução.

### Hábito

Representa um hábito acompanhado pelo cliente.

Um hábito possui informações como:
- nome;
- tipo (positivo ou negativo);
- frequência atual;
- frequência desejada;
- usuário responsável.

### Registro de Atividade

Representa uma atividade registrada para determinado hábito em uma data.

Os registros são utilizados para calcular a evolução do usuário.

## 4. Metas

As metas permitem que o cliente defina objetivos relacionados aos seus hábitos.

Cada meta possui:
- hábito associado;
- quantidade mínima;
- período de avaliação;
- estado;
- streak;
- data de início;
- data de término.

Os períodos permitidos são:
- dia;
- semana;
- mês;
- ano.

Os estados possíveis são:
- ativa;
- cumprida;
- não cumprida.

## 5. Streak

O streak representa a quantidade de períodos consecutivos em que uma meta foi cumprida.

Regras principais:
- se o período for cumprido, o streak aumenta em 1;
- se o período não for cumprido, o streak volta para 0.

## 6. Segundo Perfil de Usuário

O sistema possuirá também o perfil Parceiro de Acompanhamento.

Esse perfil poderá visualizar metas que tenham sido compartilhadas com ele.

O Parceiro não poderá:
- editar hábitos do cliente;
- excluir hábitos;
- alterar dados pessoais;
- visualizar metas não compartilhadas.

## 7. Persistência

Os dados do sistema serão armazenados de forma persistente utilizando o banco configurado no projeto Django.

Entre os dados persistidos estão:
- clientes;
- hábitos;
- registros de atividade;
- metas;
- streaks;
- relacionamentos de acompanhamento.

## 8. Segurança

O sistema deverá utilizar:
- armazenamento seguro de senhas;
- autenticação por sessão;
- proteção CSRF;
- validação de dados no backend;
- controle de acesso aos dados;
- isolamento entre usuários;
- variáveis de ambiente para dados sensíveis.

## 9. Estratégia de Testes

O projeto utilizará testes automatizados para validar os principais comportamentos.

Serão utilizados:
- testes unitários;
- testes de integração;
- testes funcionais;
- testes de regras de negócio;
- testes de autorização.

As funcionalidades de metas e streak serão desenvolvidas preferencialmente utilizando TDD.

## 10. Ordem de Implementação

1. manter cadastro, login, perfil e hábitos funcionando;
2. implementar metas;
3. implementar estados das metas;
4. implementar streak;
5. implementar Parceiro de Acompanhamento;
6. implementar compartilhamento de metas;
7. ampliar testes;
8. revisar documentação.

## 11. Fluxo de Desenvolvimento

O desenvolvimento deverá seguir preferencialmente:

Issue  
→ Branch  
→ Implementação  
→ Testes  
→ Commit  
→ Pull Request  
→ Revisão  
→ Merge

## 12. Rastreabilidade

Sempre que possível, os artefatos deverão estar relacionados da seguinte forma:

REQ  
→ TASK  
→ CÓDIGO  
→ TESTE  
→ PR