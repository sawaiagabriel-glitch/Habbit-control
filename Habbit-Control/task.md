# Habbit Control — Tarefas do Projeto

##  Documentação

- [x] Criar spec.md.
- [x] Criar plan.md.
- [x] Criar tasks.md.
- [x] Criar pasta docs.
- [x] Criar registros ADR.
- [x] Documentar segurança e SSDLC.
- [ ] Documentar estratégia de testes.
- [ ] Criar documentação de revisão em docs/review.


##  Hábitos

- [ ] Revisar cadastro de hábitos.
- [ ] Validar classificação entre hábito positivo e negativo.
- [ ] Revisar definição de frequência atual e desejada.
- [ ] Validar regras para edição e exclusão de hábitos.

##  Registro de Atividades

- [ ] Revisar o registro diário de atividades.
- [ ] Validar a regra de um registro por hábito por dia.
- [ ] Validar os dados informados antes de salvar um registro.
- [ ] Exibir mensagens adequadas quando um registro for inválido.

## Progresso e Relatórios

- [ ] Revisar cálculo de progresso de hábitos positivos.
- [ ] Revisar cálculo de progresso de hábitos negativos.
- [ ] Testar os cálculos com diferentes valores.
- [ ] Revisar apresentação dos relatórios.

##  Testes

- [x] Criar testes de autenticação.
- [ ] Criar testes de hábitos.
- [ ] Criar testes de registros de atividades.
- [ ] Criar testes das regras de progresso.

## Metas



- [ ] Criar model de Meta.
- [ ] Vincular cada meta a um hábito.
- [ ] Permitir definir quantidade mínima.
- [ ] Permitir escolher período: dia, semana, mês ou ano.
- [ ] Criar meta com estado inicial ativa.
- [ ] Criar meta com streak inicial igual a 0.
- [ ] Calcular progresso da meta.
- [ ] Alterar estado para cumprida quando atingir a quantidade mínima.
- [ ] Alterar estado para não cumprida quando o período terminar abaixo da meta.
- [ ] Criar novo ciclo após o encerramento do período.
- [ ] Testar regras de metas com TDD.

## Streak

- [ ] Incrementar streak quando um período for cumprido.
- [ ] Zerar streak quando um período não for cumprido.
- [ ] Garantir que o streak só seja atualizado no encerramento do período.
- [ ] Criar testes para períodos consecutivos cumpridos.
- [ ] Criar teste para quebra de sequência.

## Parceiro de Acompanhamento

- [ ] Criar segundo perfil de usuário.
- [ ] Definir permissões do Parceiro de Acompanhamento.
- [ ] Impedir que o parceiro edite hábitos do cliente.
- [ ] Impedir que o parceiro altere dados pessoais do cliente.
- [ ] Criar testes de autorização para o novo perfil.

## Compartilhamento de Metas

- [ ] Permitir que o cliente compartilhe uma meta com um parceiro.
- [ ] Registrar o relacionamento entre cliente, parceiro e meta.
- [ ] Permitir que o parceiro visualize metas compartilhadas.
- [ ] Impedir acesso a metas não compartilhadas.
- [ ] Criar testes para compartilhamento e controle de acesso.

##  Revisão Final

- [ ] Verificar se o código corresponde à spec.md.
- [ ] Verificar se todos os requisitos possuem implementação.
- [ ] Executar os testes do sistema.
- [ ] Revisar documentação.
- [ ] Registrar evidências de funcionamento.

