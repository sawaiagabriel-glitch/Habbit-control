# ADR-002 — Uso de e-mail para autenticação

**Status:** Aceito

## Contexto

O Habbit Control precisa identificar cada usuário durante o cadastro e o login.

Inicialmente, existiam dados pessoais que poderiam ser utilizados para identificar o usuário, como o CPF. Porém, o CPF não é necessário para a finalidade principal do sistema e aumentaria a quantidade de dados pessoais armazenados.

Foi necessário escolher um identificador mais simples e adequado para autenticação.

## Decisão

Foi definido que o sistema utilizará o **e-mail** como principal identificador de autenticação do Cliente.

O e-mail deve:

- ser obrigatório;
- ser único;
- ser normalizado antes de ser salvo e utilizado no login.

As senhas devem ser armazenadas utilizando **hash** e nunca em texto puro.

O ID interno do banco de dados continuará sendo utilizado para identificar os registros internamente.

## Consequências

### Positivas

- simplifica o processo de login;
- reduz a coleta de dados pessoais desnecessários;
- facilita a identificação única do usuário;
- melhora o alinhamento com princípios de privacidade e minimização de dados;
- elimina a necessidade de usar CPF como identificador de acesso.

### Negativas

- o sistema precisa impedir o cadastro de e-mails duplicados;
- alterações de e-mail precisam ser validadas;
- o usuário depende de um e-mail válido para utilizar sua conta.