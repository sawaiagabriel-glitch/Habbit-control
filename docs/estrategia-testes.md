
# Estratégia de Testes — Habbit Control

## Objetivo

Garantir que as principais funcionalidades e regras de negócio do sistema funcionem corretamente e que novas alterações não causem regressões.

## Tipos de Teste

### Testes Unitários

Utilizados para validar regras isoladas, como:
- validação de cadastro;
- validação de senha;
- regras de metas;
- cálculo de progresso;
- cálculo de streak.

### Testes de Integração

Utilizados para verificar a interação entre componentes, como:
- Cliente e Hábito;
- Hábito e RegistroAtividade;
- Meta e RegistroAtividade.

### Testes Funcionais

Utilizados para validar fluxos completos do usuário.

### Testes de Segurança

Utilizados para verificar:
- autenticação;
- autorização;
- isolamento entre usuários;
- validação de campos;
- proteção de dados.

## Execução

A suíte completa é executada com:

python manage.py test

## Critério de Sucesso

Uma alteração só deve ser considerada concluída quando:
- os testes relacionados passam;
- a suíte completa não apresenta regressões;
- o comportamento continua coerente com as specs.