# ADR-002 — Autenticação por e-mail e sessão

## Status

Aceito

## Contexto

O Habbit-Control precisa identificar cada usuário no cadastro e no login. Dados pessoais como CPF não são necessários para a finalidade principal do sistema e aumentariam a superfície de dados sensíveis armazenados.

Além do Cliente, o sistema passou a ter o perfil Parceiro de Acompanhamento, que também precisa de autenticação própria sem herdar permissões de escrita do Cliente.

## Decisão

- O **e-mail** é o identificador de autenticação do Cliente e do Parceiro.
- O e-mail é obrigatório, único e normalizado (`lower().strip()`) antes de persistir e autenticar.
- Senhas são armazenadas com hash PBKDF2 SHA-256 (`make_password` / `check_password`); nunca em texto puro.
- A autenticação **não** usa o `User` nativo do Django Auth nesta versão: sessões próprias via cookies do Django, com chaves:
  - `cliente_email` para Cliente;
  - `parceiro_email` para Parceiro.
- Rotas de cadastro/login do Parceiro ficam em `partner_views.py`, separadas das do Cliente.
- Login de um perfil limpa a sessão do outro quando aplicável, evitando ambiguidade de identidade.
- Áreas privadas exigem sessão válida; formulários e APIs de escrita usam proteção CSRF do Django.
- Cookies de sessão/CSRF: em desenvolvimento (`DEBUG=True`) aceitam HTTP local (`SameSite=Lax`); em produção (`DEBUG=False`) usam `Secure` e `SameSite=None` (HTTPS).

## Alternativas consideradas

- Usar CPF como login — rejeitado por minimização de dados e complexidade desnecessária.
- Migrar imediatamente para `django.contrib.auth.User` / Allauth — possível evolução futura, mas fora do escopo atual; a sessão customizada já atende Cliente e Parceiro.
- Autenticação social (OAuth) — fora de escopo.

## Consequências

### Positivas

- login simples e alinhado à LGPD (minimização);
- credenciais protegidas por hash;
- isolamento claro entre Cliente e Parceiro;
- CSRF e cookies configuráveis por ambiente;
- testes HTTP exercitam autenticação e autorização com CSRF ativo.

### Negativas

- duplicidade conceitual em relação ao User padrão do Django;
- e-mail duplicado precisa ser barrado em formulário, view e constraint;
- alteração de e-mail exige revalidação de unicidade;
- o usuário depende de um e-mail válido para acessar a conta.
