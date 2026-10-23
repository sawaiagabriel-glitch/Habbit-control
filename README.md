# Habit Control

Aplicação web desenvolvida em Django para registar hábitos, acompanhar atividades e consultar a evolução de metas. O Cliente administra os próprios dados e pode partilhar metas específicas com um Parceiro de Acompanhamento, que tem acesso apenas de leitura.

## Perfis

### Cliente

- Cria conta e inicia sessão.
- Mantém os dados do perfil, incluindo profissão, cidade e estado.
- Cria, altera e exclui hábitos.
- Regista atividades por data.
- Define metas associadas aos próprios hábitos e escolhe quais partilhar.

### Parceiro de Acompanhamento

- Cria uma conta e inicia sessão em rotas próprias.
- Consulta as metas que um Cliente partilhou com essa conta.
- Não altera hábitos, metas, atividades ou dados do Cliente.

## Funcionalidades

- Cadastro e acesso de Cliente e Parceiro.
- Perfil de Cliente e atualização dos dados permitidos.
- Hábitos positivos e negativos com frequências atual e desejada.
- Registo diário de atividades, com um registo por hábito e data.
- Visão de progressos e relatórios.
- Metas com quantidade mínima, período, progresso numérico e estados por ciclo.
- Ciclos alinhados ao calendário civil e sequência incrementada ao fechar cada período cumprido.
- Fechamento idempotente de ciclos por comando de gestão, adequado a uma tarefa diária agendada.
- Partilha explícita de metas com Parceiros.

## Arquitetura

O projeto está organizado em duas aplicações Django e no projeto de configuração:

- `apps/login_cadastro_app/`: modelos de Cliente e Parceiro, formulários e fluxos de conta.
- `apps/login_cadastro_app/partner_views.py`: cadastro e login do Parceiro.
- `apps/pagina_interna/models.py`: hábitos, atividades, metas e ciclos de meta.
- `apps/pagina_interna/services.py`: cálculo e atualização dos ciclos, estados, progresso e streak.
- `apps/pagina_interna/access.py`: resolução do Cliente autenticado pela sessão.
- `apps/pagina_interna/meta_views.py`: gestão de metas pelo Cliente e consulta pelo Parceiro.
- `apps/pagina_interna/views.py`: páginas e APIs internas existentes.
- `apps/*/templates/` e `static/`: interface HTML, estilos e JavaScript.
- `specs/`: requisitos funcionais.
- `docs/adr/`: decisões de arquitetura.

As URLs mantêm nomes Django estáveis e são direcionadas às vistas responsáveis pelo fluxo. A autorização do Parceiro é baseada na relação explícita entre a meta partilhada e a sua conta.

## Acesso às páginas

| Fluxo | Endereço |
|---|---|
| Página inicial | `/` |
| Login de Cliente | `/login/` |
| Cadastro de Cliente | `/cadastro/cliente/` |
| Cadastro de Parceiro | `/parceiro/cadastro/` |
| Login de Parceiro | `/parceiro/login/` |
| Gestão de metas do Cliente | `/metas/` |
| Metas partilhadas com o Parceiro | `/parceiro/metas/` |

Metas só podem ser associadas a hábitos positivos e cada hábito pode ter uma meta. A conclusão do ciclo é persistida com data e hora; reduções de atividade antes do fechamento revertem o ciclo para ativo.

## Requisitos

- Python 3.10 ou superior.
- Dependências listadas em `requirements.txt`.
- SQLite para desenvolvimento local. A aplicação também aceita uma URL de base de dados através de `DATABASE_URL`.

## Sessão e proteção CSRF

O cadastro e as demais operações de formulário usam proteção CSRF do Django. Em desenvolvimento (`DEBUG=True`), os cookies de sessão e CSRF aceitam HTTP local e usam `SameSite=Lax`. Em produção (`DEBUG=False`), os cookies são `Secure` e usam `SameSite=None`, portanto a aplicação deve ser servida por HTTPS. A variável `SECURE_COOKIES` permite definir explicitamente essa política (`true` ou `false`).

No navegador, mantenha os cookies habilitados e aceda sempre pela mesma origem, por exemplo `http://127.0.0.1:8000`. Não abra os templates diretamente como ficheiros nem alterne entre `localhost` e `127.0.0.1` durante uma sessão.

## Executar no macOS

No Terminal, a partir da pasta do repositório:

```zsh
cd ~/Downloads/Habbit-control/Habbit-Control
python3 -m venv ../venv
source ../venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

A aplicação fica disponível em `http://127.0.0.1:8000/`. Para parar o servidor, use `Control+C` no terminal.

Se o ambiente virtual `../venv` já estiver criado, basta ativá-lo e iniciar o servidor:

```zsh
cd ~/Downloads/Habbit-control/Habbit-Control
source ../venv/bin/activate
python manage.py migrate
python manage.py runserver
```

## Testes e verificações

Executar todos os testes:

```zsh
python manage.py test
```

Executar apenas os testes de metas e parceiro:

```zsh
python manage.py test apps.pagina_interna.test_meta
```

Os testes incluem criação de metas, períodos civis, transições e streak, exclusão sem apagar histórico, partilha através dos formulários e bloqueio das operações de escrita do Parceiro. Os testes HTTP de autenticação e atividade usam verificação CSRF ativa.

Verificar configuração e migrações:

```zsh
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Migrações

As migrações adicionam o modelo `Parceiro`, o modelo `Meta`, os ciclos `MetaCiclo`, a relação de partilha, a unicidade de meta por hábito e a data de cumprimento do ciclo. Em cada ambiente, aplique-as antes de iniciar a aplicação:

```zsh
python manage.py migrate
```

## Estado e limites conhecidos

Os ciclos vencidos são processados ao consultar metas, ao registar atividades e pelo comando `python manage.py atualizar_ciclos_metas`. Em produção, configure uma tarefa diária no agendador do ambiente para executar esse comando e fechar períodos mesmo quando ninguém acede à aplicação. O comando é idempotente: executar novamente não duplica ciclos nem incrementa o streak outra vez.

O projeto usa sessões próprias para Cliente e Parceiro, em vez do modelo de utilizador nativo do Django. A separação das vistas e dos testes mantém essa decisão localizada e explícita.

## Documentação

- `plan.md`: plano técnico.
- `task.md`: acompanhamento de tarefas.
- `specs/`: requisitos de cadastro, perfil, hábitos, privacidade, metas e Parceiro.
- `docs/adr/ADR-1-django.md`: adoção de Django.
- `docs/adr/ADR-2-metas-e-parceiro.md`: separação de domínio, vistas e permissões para metas e Parceiro.

## Equipa

- Miqueias
- Gabriel
- Heitor
