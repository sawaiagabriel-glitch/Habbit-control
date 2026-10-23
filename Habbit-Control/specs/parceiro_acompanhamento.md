# Parceiro de Acompanhamento

## Objetivo

Permitir que um Cliente partilhe metas específicas com outra pessoa, dando-lhe um perfil próprio de conta e acesso limitado à consulta do progresso partilhado.

## Requisitos

### REQ-PAR-01: Conta e autenticação

O sistema permite criar uma conta de Parceiro com nome, email único e senha armazenada como hash. O Parceiro inicia sessão por uma rota separada e a sua sessão é identificada por `parceiro_email`.

Implementação: `apps/login_cadastro_app/models.py` (`Parceiro`), `apps/login_cadastro_app/partner_views.py` (`cadastro_parceiro`, `login_parceiro`).

### REQ-PAR-02: Partilha explícita

Ao criar uma meta, o Cliente pode selecionar zero ou mais Parceiros registados. Apenas os Parceiros associados à meta podem consultá-la.

Implementação: `apps/pagina_interna/models.py` (`Meta.parceiros`), `apps/pagina_interna/forms.py` (`MetaForm`).

### REQ-PAR-03: Consulta de metas partilhadas

Um Parceiro autenticado consulta as metas que foram associadas à sua conta, incluindo o nome do hábito, o Cliente, o alvo, o período, o progresso do ciclo atual, o estado e a sequência.

Implementação: `/parceiro/metas/`, `apps/pagina_interna/meta_views.py` (`metas_partilhadas`), `apps/pagina_interna/templates/pagina_interna/metas_partilhadas.html`.

### REQ-PAR-04: Restrições de permissão

O Parceiro não pode criar, editar ou excluir hábitos/metas, registar atividades ou alterar dados do Cliente. As rotas internas de Cliente exigem `cliente_email`; a página de parceiro não oferece ações de escrita.

Cobertura: `apps/pagina_interna/test_meta.py` (`test_parceiro_nao_pode_escrever_dados_de_cliente`).

### REQ-PAR-05: Fluxo completo de partilha com CSRF

O Cliente cria e partilha uma meta através do formulário autenticado. O Parceiro inicia sessão pela página própria e visualiza a meta partilhada. Os formulários de cadastro e login mantêm a proteção CSRF ativa.

Cobertura: `apps/pagina_interna/test_meta.py` (`test_cliente_partilha_meta_pelo_formulario_e_parceiro_visualiza`, `test_parceiro_autentica_e_visualiza_metas_partilhadas`).
