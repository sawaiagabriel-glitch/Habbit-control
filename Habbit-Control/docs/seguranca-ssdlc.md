# Segurança e SSDLC — Habbit Control

## 1. Objetivo

Este documento registra as principais práticas de segurança utilizadas no desenvolvimento do Habbit Control.

O objetivo é garantir que segurança, privacidade e proteção dos dados sejam consideradas durante todo o ciclo de desenvolvimento do sistema.

---

## 2. Autenticação

O sistema utiliza autenticação baseada em e-mail e senha.

As principais regras são:

- o e-mail deve ser único;
- a senha não deve ser armazenada em texto puro;
- senhas devem ser armazenadas utilizando hash;
- áreas privadas exigem sessão autenticada;
- credenciais inválidas não devem permitir acesso ao sistema.

---

## 3. Controle de Acesso

Cada usuário deve acessar apenas os dados que possui permissão para visualizar ou modificar.

O sistema deve garantir que:

- um cliente não consiga editar dados de outro cliente;
- hábitos sejam acessíveis apenas pelo seu proprietário;
- registros de atividade respeitem a propriedade do hábito;
- metas sejam acessíveis apenas pelo cliente responsável;
- futuramente, o Parceiro de Acompanhamento visualize somente metas explicitamente compartilhadas.

---

## 4. Validação de Dados

Os dados enviados pelo usuário devem ser validados no backend.

A validação no JavaScript pode melhorar a experiência do usuário, mas não substitui a validação do servidor.

Entre as validações estão:

- campos obrigatórios;
- formato de e-mail;
- unicidade de e-mail;
- validação de senha;
- valores numéricos permitidos;
- campos autorizados para edição;
- consentimento obrigatório da LGPD.

---

## 5. Proteção CSRF

O projeto utiliza as proteções fornecidas pelo Django contra ataques de Cross-Site Request Forgery (CSRF).

Formulários e requisições que modificam dados devem utilizar os mecanismos de proteção CSRF disponibilizados pelo framework.

---

## 6. Senhas

As senhas dos usuários devem:

- nunca ser armazenadas em texto puro;
- utilizar funções seguras de hash;
- ser verificadas através dos mecanismos apropriados do sistema;
- não ser exibidas em páginas, logs ou mensagens de erro.

---

## 7. Variáveis de Ambiente

Informações sensíveis de configuração não devem ficar diretamente no código-fonte.

Sempre que necessário, devem ser utilizadas variáveis de ambiente para dados como:

- configurações de banco de dados;
- chaves secretas;
- credenciais externas;
- configurações específicas de produção.

Arquivos contendo dados sensíveis, como `.env`, não devem ser enviados ao repositório público.

---

## 8. Privacidade e LGPD

O Habbit Control busca aplicar princípios de minimização e proteção de dados pessoais.

Entre as medidas adotadas estão:

- utilização do e-mail como identificador em vez de CPF;
- coleta somente de dados necessários;
- consentimento obrigatório para tratamento de dados;
- restrição de acesso aos dados pessoais;
- proteção contra acesso por outros usuários.

As regras detalhadas estão documentadas em:

`specs/privacidade_lgpd.md`

---

## 9. Segurança no Ciclo de Desenvolvimento

A segurança deve ser considerada durante todo o processo de desenvolvimento.

Fluxo adotado:

1. definir requisito;
2. analisar riscos relacionados;
3. implementar a funcionalidade;
4. criar testes;
5. revisar o código;
6. executar testes de regressão;
7. atualizar a documentação quando necessário.

---

## 10. Testes de Segurança

Os testes devem verificar comportamentos como:

- usuário não autenticado não acessa área privada;
- um cliente não consegue editar dados de outro;
- campos não autorizados são bloqueados;
- cadastro sem consentimento LGPD é rejeitado;
- e-mails duplicados são rejeitados;
- entradas inválidas não são persistidas;
- senhas não ficam armazenadas em texto puro.

---

## 11. Tratamento de Erros

Mensagens de erro devem informar o problema ao usuário sem expor informações internas sensíveis.

O sistema deve evitar exibir:

- senhas;
- informações de configuração;
- detalhes internos do banco de dados;
- dados pertencentes a outros usuários.

---

## 12. Revisão e Manutenção

Sempre que uma funcionalidade nova for adicionada, devem ser avaliados:

- impacto sobre autenticação;
- impacto sobre autorização;
- novos dados armazenados;
- validações necessárias;
- necessidade de novos testes de segurança.

Mudanças relevantes devem ser refletidas nas especificações, testes e documentação do projeto.

---

## 13. Resultado Esperado

Ao final do desenvolvimento, o Habbit Control deve possuir:

- autenticação segura;
- senhas protegidas por hash;
- isolamento de dados entre usuários;
- validação de entradas no backend;
- proteção CSRF;
- configuração sensível fora do código;
- regras de privacidade e LGPD documentadas;
- testes cobrindo comportamentos críticos de segurança.