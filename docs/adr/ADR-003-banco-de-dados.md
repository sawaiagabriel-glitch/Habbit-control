# ADR-003 — Estratégia de banco de dados

## Status

Aceito

## Contexto

O Habbit-Control precisa persistir clientes, parceiros, hábitos, registros de atividade, metas, ciclos de meta, planos do assistente e relacionamentos de compartilhamento.

O ambiente de desenvolvimento deve ser simples de executar pela equipe, sem exigir instalação de servidor de banco. Ao mesmo tempo, o sistema deve permitir evolução para outro SGBD em ambientes externos.

## Decisão

- Desenvolvimento local usa **SQLite** (padrão Django), com arquivo local gerenciado por migrations.
- Persistência via **Django ORM** e models nas apps `login_cadastro_app` e `pagina_interna`.
- Evolução de schema exclusivamente por **migrations** do Django.
- Ambientes externos podem configurar outro banco através de `DATABASE_URL` (quando presente nas settings).
- Constraints de domínio relevantes ficam no banco/ORM quando possível (ex.: unicidade de e-mail, unicidade de meta por hábito, `unique_together` de atividade por hábito/data).

## Alternativas consideradas

- PostgreSQL desde o início em todos os ambientes — melhor para concorrência, porém mais pesado para onboarding local.
- Persistência apenas em arquivos JSON/CSV — inadequado para relacionamentos, restrições e evolução controlada.

## Consequências

### Positivas

- setup local rápido;
- migrations versionadas e auditáveis;
- integração nativa com o Django e com a suíte de testes;
- possibilidade de trocar o SGBD sem reescrever a camada de domínio;
- facilita reprodução do projeto por outros integrantes.

### Negativas

- SQLite tem limites de concorrência de escrita;
- diferenças sutis de comportamento entre SQLite e outros bancos podem aparecer em produção;
- alterações de model exigem criação e aplicação correta de migrations.
