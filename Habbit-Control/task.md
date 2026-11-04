# Habbit Control — Tarefas do Projeto

## Documentação

- [x] Criar `spec.md` consolidado (índice das specs).
- [x] Criar `plan.md`.
- [x] Criar/atualizar `task.md`.
- [x] Criar pasta `docs`.
- [x] Consolidar registros ADR em `docs/adr/` (ADR-001 a ADR-004).
- [x] Documentar segurança e SSDLC (`docs/seguranca-ssdlc.md`).
- [x] Documentar estratégia de testes (`../docs/estrategia-testes.md`).
- [x] Criar documentação de revisão em `docs/review/revisao-final.md`.

## Cadastro, Login e Perfil

- [x] Cadastro de Cliente com validação, e-mail único e hash PBKDF2.
- [x] Consentimento LGPD obrigatório e página `/consentimento/`.
- [x] Login por e-mail/senha com sessão `cliente_email`.
- [x] Logout e proteção CSRF nos formulários.
- [x] Perfil `/alterar_dados/` com edição inline e API whitelist.
- [x] Testes de autenticação, cadastro e perfil (`login_cadastro_app/tests.py`, `pagina_interna/tests.py`).

## Hábitos

- [x] Cadastro de hábitos (positivo/negativo).
- [x] Classificação entre hábito positivo e negativo.
- [x] Frequência atual e desejada com períodos `dia`/`semana`/`mes`/`ano`.
- [x] Edição e exclusão de hábitos com isolamento por titular.
- [ ] Parcial: suíte dedicada de testes automatizados só de CRUD de hábitos (cobertura indireta via metas/dashboard/atividade).

## Registro de Atividades

- [x] Registro diário de atividades (`/atividade_diaria/`, API `/api/registrar_atividade/`).
- [x] Regra de um registro por hábito por dia (`unique_together`).
- [x] Validação backend de quantidade (>= 0) e titularidade.
- [x] Mensagens/erros JSON adequados em casos inválidos.
- [x] Testes de registro com CSRF e recalculo de meta (`test_meta.py`).

## Progresso e Relatórios

- [x] Cálculo de progresso de hábitos positivos.
- [x] Cálculo de progresso de hábitos negativos.
- [x] Apresentação em `/progressos/` e `/relatorios/` (Chart.js via API).
- [x] Dashboard consolidando hábitos, metas e atividades.
- [ ] Parcial: testes automatizados específicos das fórmulas de relatório de hábitos (além da cobertura de progresso de metas).

## Metas

- [x] Model `Meta` vinculado a hábito positivo (unicidade por hábito).
- [x] Model `MetaCiclo` com estados `ativa` / `cumprida` / `nao_cumprida`.
- [x] Quantidade mínima e períodos `dia` / `semana` / `mes` / `ano`.
- [x] Estado inicial `ativa` e streak inicial `0`.
- [x] Cálculo de progresso numérico e percentual (cap 100%).
- [x] Transição para cumprida ao atingir a quantidade mínima (`data_cumprimento`).
- [x] Fechamento de período não cumprido e abertura de novo ciclo.
- [x] Comando `atualizar_ciclos_metas` idempotente.
- [x] Exclusão de meta sem apagar hábito/atividades.
- [x] Testes TDD em `test_meta.py`.

## Streak

- [x] Incrementar streak no encerramento de período cumprido.
- [x] Zerar streak quando o período não for cumprido.
- [x] Streak atualizado apenas no fechamento do período.
- [x] Testes de períodos consecutivos e quebra de sequência.

## Parceiro de Acompanhamento

- [x] Model `Parceiro` com cadastro/login em rotas próprias (`parceiro_email`).
- [x] Permissões: consulta somente leitura de metas partilhadas.
- [x] Impedir edição de hábitos/dados do Cliente pelo Parceiro.
- [x] Partilha explícita via M2M `Meta.parceiros`.
- [x] Testes de autorização e fluxo completo com CSRF (`test_meta.py`).

## Compartilhamento de Metas

- [x] Compartilhamento com Parceiro na criação/edição da meta.
- [x] Parceiro visualiza apenas metas associadas à sua conta.
- [x] Compartilhamento público por token (`compartilhamento_ativo`, `token_publico`).
- [x] Ativar/desativar link público pelo titular.
- [x] Página pública somente leitura sem expor dados pessoais.
- [x] Testes em `test_meta.py` e `test_meta_compartilhamento.py`.

## Assistente de Metas e Dashboard

- [x] Chatbot/assistente híbrido (`meta_assistant.py`) com OpenAI + fallback determinístico.
- [x] Model `PlanoMetaAssistente` persistido na criação da meta (quando houver plano).
- [x] API de sugestão não cria Meta; criação explícita em endpoint separado.
- [x] Chave OpenAI via `.env` / settings (fora do Git).
- [x] Dashboard com resumo de hábitos, metas manuais e metas do assistente.
- [x] Testes em `test_meta_assistant.py` e `tests.py` (Dashboard).

## Segurança

- [x] CSRF ativo em formulários e testes HTTP relevantes.
- [x] Isolamento por usuário (Cliente/Parceiro/meta de terceiros).
- [x] Validações de backend e whitelist de campos de perfil.
- [x] Configuração sensível por variáveis de ambiente (`.env`).
- [x] Documentação SSDLC atualizada.

## Testes

- [x] Testes de autenticação/cadastro.
- [x] Testes de perfil e Dashboard.
- [x] Testes de metas, streak, Parceiro e compartilhamento.
- [x] Testes do assistente (mock OpenAI + fallback).
- [ ] Parcial: suíte específica isolada para CRUD puro de hábitos e fórmulas de relatório de hábitos.

## Revisão Final

- [x] Verificar aderência das specs ao código implementado.
- [x] Registrar evidências em `docs/review/revisao-final.md`.
- [x] Revisar documentação consolidada (`spec.md`, ADRs, `task.md`).
