# Habbit Control

Sistema de acompanhamento e controle de hábitos desenvolvido para o trabalho final da disciplina de Modelagem de Software.

## Integrantes

- Miqueias
- Gabriel
- Heitor

## Objetivo

O Habbit Control permite que usuários cadastrem hábitos, registrem atividades e acompanhem sua evolução ao longo do tempo.

O sistema também possui regras de negócio relacionadas a metas, estados de metas e streak.

## Tecnologias

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite
- Git
- GitHub

## Funcionalidades

- cadastro de usuários;
- login e autenticação;
- gerenciamento de perfil;
- criação e gerenciamento de hábitos;
- registro de atividades;
- acompanhamento de progresso;
- privacidade e LGPD;
- metas;
- estados de metas;
- streak;
- Parceiro de Acompanhamento;
- compartilhamento de metas.

## Como executar

Instale as dependências:

```bash id="xh79zb"
python -m pip install -r requirements.txt
```

Execute as migrations:

```bash id="btfq45"
python manage.py migrate
```

Inicie o servidor:

```bash id="p5m40k"
python manage.py runserver
```

Acesse:

```text id="rlpnqq"
http://127.0.0.1:8000/
```

## Testes

Para executar os testes:

```bash id="3zqpij"
python manage.py test
```

## Documentação

A documentação do projeto está organizada em:

- `spec.md` — especificação principal do sistema;
- `plan.md` — plano técnico;
- `tasks.md` — tarefas do projeto;
- `specs/` — requisitos detalhados;
- `docs/adr/` — decisões arquiteturais;
- `docs/review/` — revisão técnica.