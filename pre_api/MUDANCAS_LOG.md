# Mudancas Log

## 2026-05-11 14:08:09 -03 - Renomeia endpoint de criacao de usuarios

- Arquivos afetados: `routes/auth_routes.py`, `tests/test_auth.py`, `MUDANCAS_LOG.md`
- Resumo: alterado o endpoint de criacao de usuario autenticado por admin de `POST /auth/sign-up` para `POST /auth/users`; a funcao da rota passou de `sign_up` para `create_user`; testes ajustados para o novo caminho.
- Impacto: a criacao de usuarios agora segue o mesmo recurso REST usado para listagem e exclusao em `/auth/users`, evitando a leitura equivocada de que se trata de cadastro publico do proprio usuario.
