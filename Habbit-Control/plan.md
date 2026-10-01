# Habbit Control — Plano Técnico

## 1. Tecnologias

O sistema utiliza:

- Python
- Django
- HTML
- CSS
- JavaScript
- Banco de dados 
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