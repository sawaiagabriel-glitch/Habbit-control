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

- Python 3.10 ou superior. A imagem Docker usa Python 3.13, a mesma linha da versão usada no desenvolvimento atual.
- Dependências listadas em `Habbit-Control/requirements.txt`.
- Docker Desktop, apenas para a execução em contentor.
- SQLite para desenvolvimento local. A aplicação também aceita uma URL de base de dados através de `DATABASE_URL`.

## Executando com Docker

Pré-requisito: Docker Desktop instalado.

Na pasta do repositório clonado, entre na aplicação Django (onde estão `manage.py` e `docker-compose.yml`):

```bash
git clone https://github.com/sawaiagabriel-glitch/Habbit-control.git
cd Habbit-control/Habbit-Control
```

Crie o ficheiro `.env` a partir do exemplo. Preencha `OPENAI_API_KEY` só na máquina local, se quiser o assistente com a OpenAI. Sem essa chave, o assistente usa o fallback determinístico. Não versione o `.env`.

```bash
# Linux/macOS
cp .env.example .env
```

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

Depois:

```bash
docker compose up --build
```

A aplicação fica disponível em [http://localhost:8000](http://localhost:8000).

Para parar e remover os contentores:

```bash
docker compose down
```

O banco SQLite é o ficheiro `db.sqlite3` na pasta `Habbit-Control`. O serviço `web` monta essa pasta em `/app`, por isso o ficheiro permanece no computador ao recriar o contentor.

Para executar os testes:

```bash
docker compose run --rm web python manage.py test
```

## Executar sem Docker

Na pasta `Habbit-Control`:

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Depois:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

A aplicação fica disponível em [http://127.0.0.1:8000](http://127.0.0.1:8000/).

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

## Assistente de Metas (OpenAI opcional)

O assistente de criação de metas é híbrido: quando a OpenAI estiver configurada, gera uma sugestão personalizada via Responses API; caso contrário (ou em qualquer falha), usa automaticamente o algoritmo determinístico local. A IA apenas sugere valores — nunca cria nem salva uma Meta.

1. Instale as dependências:

```zsh
python -m pip install -r requirements.txt
```

2. Crie um ficheiro `.env` a partir do exemplo (na pasta `Habbit-Control/`):

```zsh
cp .env.example .env
```

3. Defina a chave (opcional):

```env
OPENAI_API_KEY=
OPENAI_META_ASSISTANT_MODEL=
```

- Sem `OPENAI_API_KEY`, o assistente continua a funcionar com o fallback determinístico.
- `OPENAI_META_ASSISTANT_MODEL` é opcional; se vazio, o backend usa o default configurado em `settings.py` (`gpt-4.1-mini`).
- Nunca coloque uma chave real no repositório, no frontend ou na documentação.

## Testes e verificações

Executar todos os testes:

```zsh
python manage.py test
```

Executar apenas os testes de metas e parceiro:

```zsh
python manage.py test apps.pagina_interna.test_meta
```

Os testes incluem criação de metas, períodos civis, transições e streak, exclusão sem apagar histórico, partilha através dos formulários e bloqueio das operações de escrita do Parceiro. Os testes HTTP de autenticação e atividade usam verificação CSRF ativa. Os testes do assistente mockam a OpenAI e não fazem chamadas reais à API.

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

## Deploy no Railway

O serviço Django fica na pasta `Habbit-Control`. O Railway precisa usar essa pasta como diretório raiz. O arranque de produção é `sh start.sh`: aplica as migrations existentes, recolhe os ficheiros estáticos e inicia o Gunicorn com `habit_control.wsgi:application`. O `runserver` e o `docker compose` continuam a ser apenas para desenvolvimento local. O `railway.json` pede o builder Nixpacks para o Railway não usar o Dockerfile local.

O link público de uma meta já é montado com o esquema e o host do pedido (`request.scheme` e `request.get_host`). Com `SECURE_PROXY_SSL_HEADER`, o Railway faz esse link sair em HTTPS, por exemplo `https://DOMINIO/meta/publica/TOKEN/`.

1. Faça commit e push da branch `dev` para o GitHub. Não inclua o ficheiro `.env`.
2. Crie um projeto novo no Railway.
3. Escolha **Deploy from GitHub Repo**.
4. Selecione o repositório `Habbit-control`.
5. No serviço da aplicação, abra **Settings** e defina **Root Directory** como `Habbit-Control` antes do primeiro deploy. Sem isso, o Railway não encontra `manage.py` nem `requirements.txt`.
6. Adicione um serviço **PostgreSQL** ao mesmo projeto.
7. No serviço da aplicação, confirme que a variável `DATABASE_URL` foi criada e aponta para esse PostgreSQL. Não copie o `db.sqlite3` local. O schema no PostgreSQL nasce das migrations já existentes, executadas no arranque.
8. Configure as variáveis do serviço da aplicação:

```text
SECRET_KEY=<gerar um valor longo e aleatório>
DEBUG=False
OPENAI_API_KEY=<chave da sua conta, se quiser o assistente com a OpenAI>
OPENAI_META_ASSISTANT_MODEL=gpt-4.1-mini
OPENAI_META_ASSISTANT_TIMEOUT=15
NIXPACKS_PYTHON_VERSION=3.13
```

`NIXPACKS_PYTHON_VERSION` alinha o build ao Python 3.13 usado no desenvolvimento. Sem `OPENAI_API_KEY`, o assistente continua no fallback local.

9. Em **Settings → Networking → Generate Domain**, publique o domínio HTTPS.
10. O Railway injeta `RAILWAY_PUBLIC_DOMAIN`. O código acrescenta esse domínio a `ALLOWED_HOSTS` e `https://` mais esse domínio a `CSRF_TRUSTED_ORIGINS`. Mesmo assim, depois de o domínio existir, pode fixar as variáveis à mão:

```text
ALLOWED_HOSTS=DOMINIO_DO_RAILWAY
CSRF_TRUSTED_ORIGINS=https://DOMINIO_DO_RAILWAY
```

Use só o hostname em `ALLOWED_HOSTS`, sem `https://`. Em `CSRF_TRUSTED_ORIGINS`, inclua o `https://`.
11. Faça redeploy depois de gravar as variáveis.
12. Teste na URL pública: página inicial e login, cadastro, Dashboard, hábitos, atividade, metas, chatbot, partilha com Parceiro e o link público numa janela anónima.

Sem `DATABASE_URL`, o projeto continua a usar o SQLite local. Com `DEBUG=True`, cookies e redirecionamento HTTPS permanecem adequados a `http://127.0.0.1:8000`.

## Documentação

- `spec.md`: índice consolidado das specs.
- `plan.md`: plano técnico.
- `task.md`: acompanhamento de tarefas.
- `specs/`: requisitos de cadastro, perfil, hábitos, privacidade, metas e Parceiro.
- `docs/adr/ADR-001-django.md` … `ADR-004-metas-streak-parceiro.md`: decisões de arquitetura.
- `docs/review/revisao-final.md`: revisão final (spec ↔ código ↔ testes).
- `docs/seguranca-ssdlc.md`: práticas de segurança.

## Equipa

- Miqueias
- Gabriel
- Heitor
