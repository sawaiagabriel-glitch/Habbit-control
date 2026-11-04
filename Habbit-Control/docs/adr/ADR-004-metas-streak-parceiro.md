# ADR-004 — Metas, MetaCiclo, streak, Parceiro e compartilhamento

## Status

Aceito

## Contexto

Além do CRUD de hábitos, o Habbit-Control precisa de objetivos mensuráveis no tempo, histórico de cumprimento, motivação por sequência (streak) e acompanhamento por terceiros com permissões mínimas.

Concentrar autenticação, cálculo de ciclos, persistência e renderização no mesmo módulo aumentaria acoplamento. O Parceiro exige fronteira clara: ler apenas o que foi partilhado, sem escrever nos dados do Cliente. Também surgiu a necessidade de sugestão assistida de metas (IA opcional) e de link público somente leitura.

## Decisão

### Modelagem de Meta e MetaCiclo

- `Meta` pertence a um único `Habito` positivo (constraint de unicidade por hábito).
- Campos operacionais: `quantidade_minima`, `periodo` (`dia`/`semana`/`mes`/`ano`), `streak`, `data_inicio`.
- `MetaCiclo` persiste cada intervalo civil avaliado: `inicio`, `fim`, `progresso`, `estado` (`ativa` / `cumprida` / `nao_cumprida`) e `data_cumprimento`.
- Períodos seguem o calendário civil (fuso `America/Sao_Paulo` nas regras de serviço).
- Cálculo e fechamento de ciclos ficam em `pagina_interna.services` (`atualizar_ciclos_meta`), separados de views/templates.
- Fechamento também é exposto pelo comando idempotente `manage.py atualizar_ciclos_metas` (agendável diariamente).
- Vistas de gestão/consulta em `meta_views.py`; identidade Cliente resolvida em `access.py`.

### Streak

- Criação: `streak = 0`.
- Incremento (`+1`) somente no **fechamento** de um ciclo que terminou `cumprida`.
- Zeramento (`0`) no fechamento de ciclo `nao_cumprida`.
- Cumprimento antecipado dentro do período muda o estado, mas **não** antecipa o incremento do streak.
- Campo `PositiveIntegerField` — nunca negativo.

### Parceiro e compartilhamento explícito

- Model `Parceiro` com cadastro/login em `partner_views.py` e sessão `parceiro_email`.
- Relação M2M `Meta.parceiros` representa autorização explícita de leitura.
- Parceiro consulta `/parceiro/metas/`; não cria/edita hábitos, metas, atividades nem perfil do Cliente.
- URLs públicas de nome estável roteiam para módulos de vista específicos.

### Compartilhamento público

- Campos `compartilhamento_ativo` e `token_publico` na `Meta`.
- Titular ativa/desativa o link; página pública é somente leitura e não expõe dados pessoais do Cliente.
- Independente da partilha com Parceiro autenticado.

### Assistente e PlanoMetaAssistente

- `meta_assistant.py` opera de forma híbrida: OpenAI Responses API quando há chave; fallback determinístico em falha/ausência.
- A IA **sugere**; não cria Meta automaticamente.
- `PlanoMetaAssistente` (OneToOne com `Meta`) persiste título, objetivo, prazo, etapas e critérios quando a meta é criada a partir do plano do assistente; exclusão da Meta remove o plano (CASCADE).
- Chave `OPENAI_API_KEY` e parâmetros relacionados vêm de variáveis de ambiente (`.env`), fora do repositório.

### Testes

- Domínio e permissões de metas/parceiro: `test_meta.py`.
- Compartilhamento público: `test_meta_compartilhamento.py`.
- Assistente (mocks OpenAI): `test_meta_assistant.py`.

## Alternativas consideradas

- Guardar estado só na `Meta` sem histórico de ciclos — rejeitado; perde auditoria por período.
- Usar o User/grupos do Django para Parceiro — possível no futuro; nesta versão a sessão customizada e o M2M bastam.
- Sempre exigir OpenAI para sugerir metas — rejeitado; fallback local mantém o fluxo offline/sem chave.
- Soft-delete de metas — fora de escopo.

## Consequências

### Positivas

- regras de ciclo e streak testáveis sem UI;
- histórico de ciclos encerrados preservado;
- Parceiro com least privilege;
- link público opcional sem misturar com conta de Parceiro;
- assistente útil com ou sem OpenAI;
- comando de gestão evita dependência exclusiva de acesso humano para fechar períodos.

### Negativas

- maior complexidade de datas/calendário e estados;
- produção precisa agendar `atualizar_ciclos_metas`;
- alterações retroativas não reabrem ciclos já fechados (sem reprocessamento de streak consolidado);
- dois modos de compartilhamento (Parceiro vs público) exigem documentação e testes distintos;
- dependência opcional da OpenAI introduz fallbacks e mocks na suíte.
