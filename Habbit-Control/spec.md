# Especificação consolidada — Habbit-Control

## Visão geral

O Habbit-Control é uma aplicação web Django para cadastro de clientes, autenticação por e-mail e senha, gestão de hábitos (positivos e negativos), registro diário de atividades, cálculo de progresso/relatórios, definição de metas com ciclos e streak, compartilhamento com Parceiro de Acompanhamento, compartilhamento público por token, assistente híbrido de metas (OpenAI com fallback determinístico) e dashboard consolidado.

Os requisitos detalhados permanecem nos arquivos de `specs/`. Este documento é apenas um índice consolidado — não substitui nem inventa requisitos.

## Especificações detalhadas

### Cadastro de Cliente

Arquivo: [`specs/cadastro_cliente.md`](specs/cadastro_cliente.md)

Requisitos: `REQ-CAD-01` … `REQ-CAD-07`

Cobre: renderização do formulário de cadastro, submissão válida com hash PBKDF2, rejeição de e-mail duplicado, validação frontend (e-mail/idade), estados/cidades dinâmicos, toggle de senha e obrigatoriedade do consentimento LGPD.

### Login

Arquivo: [`specs/login_cliente.md`](specs/login_cliente.md)

Requisitos: `REQ-LOGIN-01` … `REQ-LOGIN-07`

Cobre: tela de login, autenticação com sessão `cliente_email`, normalização de e-mail, rejeição de credenciais inválidas, UX de senha/validação no cliente e logout.

### Perfil

Arquivo: [`specs/perfil_cliente.md`](specs/perfil_cliente.md)

Requisitos: `REQ-PERFIL-01` … `REQ-PERFIL-07`

Cobre: controle de sessão em `/alterar_dados/`, renderização do perfil, edição inline, API `/api/cliente/update/` com whitelist de campos, alteração segura de senha, rejeição de campos não permitidos e stubs de rotas de garantia.

### Hábitos

Arquivo: [`specs/habitos.md`](specs/habitos.md)

Requisitos: `REQ-HAB-01` … `REQ-HAB-09`

Cobre: cadastro/edição/exclusão de hábitos, validação de frequências, isolamento por titular, listagem em progressos, atividade diária, API de registro de atividade e geração de dados para relatórios (fórmulas positivo/negativo).

### Privacidade / LGPD

Arquivo: [`specs/privacidade_lgpd.md`](specs/privacidade_lgpd.md)

Requisitos: `REQ-LGPD-01` … `REQ-LGPD-04`

Cobre: página pública `/consentimento/`, checkbox obrigatório com link, persistência do aceite e rejeição de cadastro sem consentimento.

### Metas e Sequências

Arquivo: [`specs/metas_e_sequencias.md`](specs/metas_e_sequencias.md)

Requisitos: `REQ-META-01` … `REQ-META-11`, `REQ-STREAK-01` … `REQ-STREAK-05`

Cobre: criação de meta em hábito positivo, estados (`ativa`, `cumprida`, `não cumprida`), `MetaCiclo`, progresso numérico/percentual, exclusão sem apagar hábito/atividades, controle de acesso e regras de streak (incremento, zeramento, não-negatividade, exibição).

### Parceiro

Arquivo: [`specs/parceiro_acompanhamento.md`](specs/parceiro_acompanhamento.md)

Requisitos: `REQ-PAR-01` … `REQ-PAR-05`

Cobre: conta/autenticação do Parceiro (`parceiro_email`), partilha explícita de metas, consulta somente leitura, restrições de escrita e fluxo completo com CSRF.

## Principais grupos de requisitos

| Grupo | Prefixo | Spec |
|-------|---------|------|
| Cadastro | `REQ-CAD-*` | [`specs/cadastro_cliente.md`](specs/cadastro_cliente.md) |
| Login / sessão | `REQ-LOGIN-*` | [`specs/login_cliente.md`](specs/login_cliente.md) |
| Perfil | `REQ-PERFIL-*` | [`specs/perfil_cliente.md`](specs/perfil_cliente.md) |
| Hábitos / atividades / relatórios | `REQ-HAB-*` | [`specs/habitos.md`](specs/habitos.md) |
| LGPD | `REQ-LGPD-*` | [`specs/privacidade_lgpd.md`](specs/privacidade_lgpd.md) |
| Metas | `REQ-META-*` | [`specs/metas_e_sequencias.md`](specs/metas_e_sequencias.md) |
| Streak | `REQ-STREAK-*` | [`specs/metas_e_sequencias.md`](specs/metas_e_sequencias.md) |
| Parceiro | `REQ-PAR-*` | [`specs/parceiro_acompanhamento.md`](specs/parceiro_acompanhamento.md) |

## Documentação relacionada

- Plano técnico: [`plan.md`](plan.md)
- Acompanhamento de tarefas: [`task.md`](task.md)
- ADRs: [`docs/adr/`](docs/adr/)
- Segurança / SSDLC: [`docs/seguranca-ssdlc.md`](docs/seguranca-ssdlc.md)
- Revisão final: [`docs/review/revisao-final.md`](docs/review/revisao-final.md)
