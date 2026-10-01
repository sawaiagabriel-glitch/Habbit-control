# Habbit Control — Especificação do Sistema

## 1. Visão Geral

O Habbit Control é um sistema de acompanhamento de hábitos que permite aos usuários criar hábitos, definir metas de frequência, 
registrar atividades realizadas e acompanhar sua evolução ao longo do tempo.

O sistema diferencia hábitos positivos, que o usuário deseja realizar com determinada frequência, e hábitos negativos,
que o usuário deseja reduzir ou limitar.

Além do usuário principal, o sistema contará com o perfil de acompanhante, que poderá acompanhar a
evolução dos hábitos compartilhados pelo usuário, respeitando as permissões definidas pelo sistema.

## 2. Problema

Pessoas que desejam criar hábitos positivos ou reduzir hábitos negativos podem ter dificuldade para acompanhar sua evolução de
maneira organizada e mensurável.

O Habbit Control busca centralizar o registro dessas atividades e utilizar as metas e o histórico do usuário
para apresentar sua evolução ao longo do tempo.

## 3. Perfis de Usuário

O cliente é o usuário principal do sistema.

Ele poderá:
- criar e acessar sua conta;
- cadastrar hábitos;
- classificar hábitos como positivos ou negativos;
- definir metas de frequência;
- registrar atividades realizadas;
- consultar seu progresso;
- visualizar relatórios;

## 4. Requisitos em EARS

### RF-01 — Cadastro de cliente

WHEN o visitante preencher corretamente os dados obrigatórios de cadastro,
THE SYSTEM SHALL criar uma conta de cliente e armazenar seus dados.

### RF-02 — Autenticação

WHEN o cliente informar credenciais válidas,
THE SYSTEM SHALL autenticar o cliente e iniciar sua sessão.

IF o cliente informar credenciais inválidas,
THEN THE SYSTEM SHALL negar o acesso e informar que os dados de autenticação são inválidos.

### RF-03 — Cadastro de hábito

WHEN o cliente cadastrar um novo hábito com os campos obrigatórios válidos,
THE SYSTEM SHALL associar o hábito ao cliente e armazená-lo de forma persistente.

### RF-04 — Registro de atividade

WHEN o cliente registrar uma atividade para um hábito em uma determinada data,
THE SYSTEM SHALL armazenar o registro associado ao respectivo hábito.

IF já existir um registro para o mesmo hábito na mesma data,
THEN THE SYSTEM SHALL impedir a criação de um segundo registro.

### RF-05 — Acompanhamento de progresso

WHEN o cliente acessar o progresso de um hábito,
THE SYSTEM SHALL calcular e apresentar sua evolução com base nos registros realizados e na frequência definida.

### RF-06 — Relatório

WHEN o cliente solicitar o relatório de seus hábitos,
THE SYSTEM SHALL apresentar os dados de evolução calculados a partir dos registros armazenados.