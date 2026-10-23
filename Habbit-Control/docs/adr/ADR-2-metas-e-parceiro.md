# ADR-2: Metas e Parceiro de Acompanhamento

## Estado

Aceite.

## Contexto

O projeto já separava autenticação e páginas internas em aplicações Django, mas a implementação de metas e do novo perfil poderia concentrar autenticação, cálculo de ciclos, persistência e renderização num único módulo. O Parceiro também precisa de uma fronteira de autorização clara: consultar apenas metas partilhadas, sem permissões de escrita sobre os dados do Cliente.

## Decisão

- O modelo `Meta` pertence à aplicação de acompanhamento e referencia um `Habito`.
- `MetaCiclo` mantém o progresso e o estado de cada ciclo avaliado.
- O cálculo dos ciclos fica em `pagina_interna.services`, separado das vistas e dos templates.
- `pagina_interna.access` resolve a identidade Cliente a partir da sessão.
- As vistas de gestão e consulta de metas ficam em `pagina_interna.meta_views`.
- Cadastro e login do Parceiro ficam em `login_cadastro_app.partner_views`; o Parceiro usa chave de sessão própria (`parceiro_email`).
- A associação Many-to-Many entre `Meta` e `Parceiro` representa a autorização explícita de leitura.
- As URLs existentes são roteadas para módulos de vistas específicos, mantendo os nomes públicos usados pelos templates e testes.
- Os testes de domínio e permissões de metas ficam separados em `pagina_interna.test_meta`; os testes de perfil permanecem em `pagina_interna.tests`.

## Consequências

- Regras de ciclo podem ser exercitadas sem depender da renderização de uma página.
- A consulta do Parceiro filtra as metas pela associação explícita e não oferece operações de escrita.
- A sessão usa o mecanismo existente do projeto; Cliente e Parceiro não são unificados num novo modelo de autenticação nesta alteração.
- O trabalho futuro sobre calendário civil e fechamento automatizado de ciclos deve ser feito no serviço de ciclos e acompanhado de testes dedicados.

## Validação

`python manage.py test`, `python manage.py check` e `python manage.py makemigrations --check --dry-run`.