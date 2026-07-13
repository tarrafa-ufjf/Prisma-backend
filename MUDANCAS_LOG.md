# Log de Mudancas do Projeto

Este arquivo registra alteracoes relevantes feitas no codigo do projeto, com data e descricao do que mudou.

## 2026-07-13 10:43:44 -03

### Titulo

Contexto detalhado de indicadores no chatbot

### Arquivos afetados

- [`pre_api/services/nl2sql/prompts.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/prompts.py)
- [`pre_api/tests/test_nl2sql_indicators.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/tests/test_nl2sql_indicators.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/MUDANCAS_LOG.md)

### Resumo

O contexto enviado aos agentes NL2SQL foi enriquecido com descricoes por tabela, chaves compostas, significado das principais colunas, valores observados de labels/status/atores/indicadores e orientacoes para escolher entre tabelas locais e globais. Tambem foi adicionado teste para garantir que o prompt mantenha essas informacoes essenciais.

### Impacto

Antes, o agente recebia apenas uma descricao geral do banco de indicadores. Agora, ele tem mais contexto sobre colunas, escalas, valores possiveis e limites das tabelas persistidas, reduzindo consultas incorretas e suposicoes como nomes de alunos/tutores inexistentes nas tabelas de indicadores.

## 2026-07-13 10:32:04 -03

### Titulo

Chatbot usando PostgreSQL de indicadores

### Arquivos afetados

- [`pre_api/services/nl2sql/db.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/db.py)
- [`pre_api/services/nl2sql/config.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/config.py)
- [`pre_api/services/nl2sql/prompts.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/prompts.py)
- [`pre_api/services/nl2sql/tool.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/tool.py)
- [`pre_api/services/nl2sql/graph.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/graph.py)
- [`pre_api/services/nl2sql/execution.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/execution.py)
- [`pre_api/services/nl2sql/candidates.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/candidates.py)
- [`pre_api/services/nl2sql/judge.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/judge.py)
- [`pre_api/services/nl2sql/answer.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/services/nl2sql/answer.py)
- [`pre_api/tests/test_nl2sql_indicators.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/tests/test_nl2sql_indicators.py)
- [`.env`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/.env)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/MUDANCAS_LOG.md)

### Resumo

O chatbot/NL2SQL passou a montar a conexao pelo PostgreSQL local de indicadores usando `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` e `DB_DATABASE`, mantendo `NL2SQL_DB_URI` como override opcional. Os prompts e agentes foram reorientados para o schema de indicadores, `NL2SQL_DIALECT` foi ajustado para `postgres` no ambiente local, e foi adicionada uma ferramenta NL2SQL local que exclui `configs`, `user`, `role`, `roles_users` e `role_users` da introspeccao e bloqueia consultas a essas tabelas antes da execucao.

### Impacto

Antes, o chatbot buscava configuracao Moodle/MySQL salva e orientava os agentes pelo schema Moodle. Agora, somente o chatbot consulta o banco PostgreSQL de indicadores, sem expor credenciais ou tabelas de autenticacao; as rotas administrativas Moodle e os fluxos de analise/scheduler permanecem inalterados.

## 2026-06-25 11:09:27 -03

### Titulo

Remocao da rota raiz obsoleta

### Arquivos afetados

- [`pre_api/app.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/app.py)
- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/auth.py)
- [`pre_api/pages/app.html`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/pages/app.html)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/MUDANCAS_LOG.md)

### Resumo

Removidos o endpoint `GET /`, sua excecao de autenticacao e o formulario HTML obsoleto de configuracao do Moodle. O teste anterior de acesso publico foi substituido por uma verificacao de que a rota nao existe.

### Impacto

Antes, a raiz da API exibia publicamente um formulario incompatível com o fluxo atual de configuracao. Agora, usuarios autenticados recebem HTTP 404 ao acessar `/`, e a configuracao do Moodle permanece disponivel apenas pelos endpoints administrativos atuais.

## 2026-06-25 11:01:51 -03

### Titulo

Rota do chatbot protegida por autenticacao

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/auth.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/MUDANCAS_LOG.md)

### Resumo

Removida a rota `POST /chatbot` da lista de caminhos isentos de autenticacao. Adicionados testes para garantir que requisicoes sem sessao recebam HTTP 401 e que usuarios autenticados continuem conseguindo acessar o chatbot.

### Impacto

Antes, qualquer cliente podia chamar o chatbot sem autenticacao. Agora, a rota exige uma sessao valida, seguindo a mesma protecao aplicada aos demais endpoints privados da API.

## 2026-06-23 11:17:24 -03

### Titulo

Pacote compartilhado instalado pelo uv

### Arquivos afetados

- [`pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pyproject.toml)
- [`.gitignore`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/.gitignore)
- [`pre_api/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/pyproject.toml)
- [`pre_api/uv.lock`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/uv.lock)
- [`worker/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/worker/pyproject.toml)
- [`worker/uv.lock`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/worker/uv.lock)
- [`README.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/README.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/MUDANCAS_LOG.md)

### Resumo

Adicionado um `pyproject.toml` na raiz para empacotar o modulo compartilhado `src` como `prisma-backend-shared`. `pre_api` e `worker` passaram a declarar essa dependencia local editavel via `[tool.uv.sources]`, e os locks foram regenerados para instalar o pacote compartilhado nos ambientes criados pelo uv. O `.gitignore` passou a ignorar metadados locais `*.egg-info/` gerados pelo build editavel.

### Impacto

Antes, `uv run python app.py` dentro de `worker` nao encontrava o modulo `src` e falhava com `ModuleNotFoundError`. Agora, `uv sync` instala a biblioteca compartilhada no ambiente virtual de cada subprojeto, permitindo que os imports `src.analysis_lib...` funcionem sem depender de `PYTHONPATH`.

## 2026-06-23 11:06:05 -03

### Titulo

Migracao dos ambientes Python para uv

### Arquivos afetados

- [`pre_api/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/pyproject.toml)
- [`pre_api/uv.lock`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/pre_api/uv.lock)
- [`worker/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/worker/pyproject.toml)
- [`worker/uv.lock`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/worker/uv.lock)
- [`README.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/README.md)
- [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/CONFIGURACAO_OBSERVERS_SCHEDULER.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Prisma-backend/MUDANCAS_LOG.md)

### Resumo

Os manifests de `pre_api` e `worker` foram ajustados para uso com uv: as dependencias passaram para formato PEP 508, a configuracao `[tool.poetry]` e o backend `poetry-core` foram removidos, e os projetos foram marcados como `package = false` em `[tool.uv]`. Foram gerados locks `uv.lock` para os dois subprojetos e a documentacao passou a orientar `uv sync` e `uv run`.

### Impacto

Antes, a instalacao e execucao locais dependiam de Poetry e dos comandos `poetry install`/`poetry run`. Agora, cada subprojeto e sincronizado com `uv sync` e executado com `uv run`, com dependencias travadas nos respectivos arquivos `uv.lock`.

## 2026-06-16 10:29:45 -03

### Titulo

Docker Compose lendo variaveis do env

### Arquivos afetados

- [`docker-compose.yml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/docker-compose.yml)
- [`README.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/README.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Atualizado o `docker-compose.yml` para interpolar variaveis do `.env` nas configuracoes de PostgreSQL e RabbitMQ, incluindo credenciais, banco local e portas principais. O README foi ajustado para explicar que o `.env.example` alimenta tanto a aplicacao quanto o Docker Compose, mantendo defaults no Compose para execucao local.

### Impacto

Antes, mudar credenciais ou portas exigia atualizar o `.env` da aplicacao e tambem valores fixos no `docker-compose.yml`. Agora, o `.env` passa a ser a fonte principal desses parametros para execucao local, reduzindo duplicacao e risco de configuracoes divergentes.

## 2026-06-16 09:38:43 -03

### Titulo

Melhorias no README principal

### Arquivos afetados

- [`README.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/README.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Reestruturado o README principal com visao geral do projeto, arquitetura, pre-requisitos, configuracao de ambiente, primeira execucao, comandos de execucao da API e do worker, configuracao do Moodle, scheduler, testes, endpoints principais, modelo de mensagens e solucao de problemas.

### Impacto

A documentacao de entrada do projeto ficou mais profissional e completa. Antes, o README tinha instrucoes mais curtas e concentradas em instalacao/execucao; agora tambem orienta configuracao de `.env`, inicializacao da autenticacao local, uso do scheduler, rotas principais e diagnostico de erros comuns.

## 2026-05-20 09:55:30 -03

### Titulo

Criacao manual da tabela de status do scheduler via install

### Arquivos afetados

- [`pre_api/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/database.py)
- [`worker/install.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/install.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A criacao automatica da tabela `scheduler_status` foi removida dos metodos usados em runtime pela API e pelo scheduler. A tabela passou a ser criada pelo fluxo de instalacao em `worker/install.py`, junto das demais tabelas operacionais do projeto.

### Impacto

Antes, chamar `GET /admin/scheduler/status` ou iniciar o scheduler podia criar a tabela automaticamente se ela nao existisse. Agora, a tabela precisa ser criada antes pelo install; caso contrario, o acesso ao status do scheduler depende do schema ainda nao aplicado e falhara como as outras tabelas ausentes.

## 2026-05-20 09:50:32 -03

### Titulo

Status do processo do scheduler para o frontend

### Arquivos afetados

- [`pre_api/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/database.py)
- [`pre_api/scheduler.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/scheduler.py)
- [`pre_api/routes/admin_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/admin_routes.py)
- [`pre_api/tests/test_moodle_config.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_moodle_config.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foi adicionada a tabela `scheduler_status`, atualizada pelo processo `pre_api/scheduler.py` com heartbeat, PID e `next_run_at` dos jobs. A API administrativa ganhou a rota `GET /admin/scheduler/status`, que retorna se o processo do scheduler esta rodando com base no heartbeat recente e lista o proximo disparo por channel. Testes cobrem ausencia de heartbeat, heartbeat recente e heartbeat expirado.

### Impacto

Antes, o frontend nao tinha como distinguir se o processo do scheduler estava ativo nem consultar o proximo horario de ativacao de cada channel. Agora, a tela pode consultar uma rota administrativa unica para exibir `running` do processo e `next_run_at` dos jobs agendados.

## 2026-05-19 12:32:09 -03

### Titulo

Senha obrigatoria nos fluxos de configuracao Moodle

### Arquivos afetados

- [`pre_api/routes/admin_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/admin_routes.py)
- [`pre_api/services/moodle_config_service.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/services/moodle_config_service.py)
- [`pre_api/tests/test_moodle_config.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_moodle_config.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A rota `POST /admin/moodle-config/test` deixou de reaproveitar a senha previamente salva ao testar uma configuracao enviada no payload. O fallback por configuracao existente tambem foi removido do servico que monta a configuracao Moodle. O teste automatizado passou a cobrir `password` ausente e `password` vazio nessa rota mesmo quando ja existe configuracao salva.

### Impacto

Antes, o teste de configuracao podia validar uma requisicao incompleta usando a senha antiga em memoria. Agora, os fluxos de teste e edicao exigem todos os campos da configuracao, incluindo senha nao vazia.

## 2026-05-19 12:29:16 -03

### Titulo

Erro generico ao falhar teste da conexao Moodle

### Arquivos afetados

- [`pre_api/services/moodle_config_service.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/services/moodle_config_service.py)
- [`pre_api/tests/test_moodle_config.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_moodle_config.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Falhas ao testar a conexao com o banco Moodle passaram a retornar uma mensagem generica na API, enquanto o detalhe tecnico da excecao fica registrado no log do servidor. O teste de configuracao Moodle foi ajustado para garantir que a resposta nao exponha a mensagem original do banco/driver.

### Impacto

Antes, a resposta de erro concatenava a excecao original do banco, podendo revelar detalhes de infraestrutura ou credenciais. Agora, o cliente recebe apenas `could not connect to moodle database`, reduzindo vazamento de informacoes sensiveis.

## 2026-05-19 12:22:43 -03

### Titulo

Senha obrigatoria ao editar configuracao Moodle

### Arquivos afetados

- [`pre_api/services/moodle_config_service.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/services/moodle_config_service.py)
- [`pre_api/tests/test_moodle_config.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_moodle_config.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A rota `PUT /admin/moodle-config` deixou de reaproveitar a senha previamente salva quando o payload nao informa `password` ou informa `password` vazio. O teste da configuracao Moodle passou a cobrir a obrigatoriedade de senha mesmo quando ja existe configuracao salva.

### Impacto

Antes, uma edicao da configuracao Moodle sem senha mantinha silenciosamente a senha antiga. Agora, o endpoint de edicao exige que todos os campos da configuracao sejam enviados, incluindo uma senha nao vazia, e retorna `400` quando `password` estiver ausente ou vazio.

## 2026-05-18 09:32:32 -03

### Titulo

Criptografia da senha de configuracao Moodle

### Arquivos afetados

- [`src/analysis_lib/config_crypto.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/src/analysis_lib/config_crypto.py)
- [`pre_api/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/database.py)
- [`worker/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/database.py)
- [`worker/install.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/install.py)
- [`worker/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/pyproject.toml)
- [`worker/poetry.lock`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/poetry.lock)
- [`.env.example`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/.env.example)
- [`pre_api/tests/test_moodle_config.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_moodle_config.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foi adicionada criptografia reversivel para a senha da tabela `configs`, usando `MOODLE_CONFIG_ENCRYPTION_KEY` ou `SECRET_KEY` como segredo da aplicacao. As leituras descriptografam automaticamente a senha para manter o fluxo de conexao com o Moodle, valores antigos em texto puro continuam legiveis, e o salvamento em PostgreSQL amplia a coluna `password` para `VARCHAR(512)` antes de gravar.

### Impacto

Antes, a senha do banco Moodle era persistida em texto puro. Agora, novas gravacoes salvam um valor com prefixo `enc:v1:` e a API/worker continuam recebendo a senha original apenas em memoria ao montar a conexao.

## 2026-05-15 10:42:48 -03

### Titulo

Configuracao Moodle administrada pelo banco local

### Arquivos afetados

- [`pre_api/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/app.py)
- [`pre_api/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/database.py)
- [`pre_api/processor.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/processor.py)
- [`pre_api/routes/admin_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/admin_routes.py)
- [`pre_api/services/moodle_config_service.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/services/moodle_config_service.py)
- [`pre_api/tests/test_moodle_config.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_moodle_config.py)
- [`worker/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/database.py)
- [`worker/install.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/install.py)
- [`.env.example`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/.env.example)
- [`README.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/README.md)
- [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/CONFIGURACAO_OBSERVERS_SCHEDULER.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foi adicionada uma API administrativa para consultar, testar e salvar a configuracao de conexao Moodle no PostgreSQL local. A rota `PUT /analysis` e o scheduler passaram a usar obrigatoriamente a configuracao salva, e o schema de `configs` foi alinhado para uma configuracao atual por instituicao.

### Impacto

Antes, o disparo de analise podia receber credenciais Moodle no corpo da requisicao e o scheduler lia variaveis `MYSQL_*` do `.env`. Agora, administradores devem cadastrar a conexao por `/admin/moodle-config`; a senha nunca e retornada pela API, e analises falham com erro claro quando a configuracao ainda nao foi salva.

## 2026-05-14 13:07:39 -03

### Titulo

Exclusao do admin logado na listagem de usuarios

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A rota `GET /auth/users` passou a excluir da listagem o usuario autenticado que fez a requisicao, alem de continuar retornando apenas usuarios ativos. A paginacao e o total tambem consideram essa exclusao.

### Impacto

Antes, o admin logado aparecia na propria lista administrativa de usuarios, podendo ser editado ou removido acidentalmente pelo painel. Agora, a conta atual nao aparece nesse retorno.

## 2026-05-14 10:49:58 -03

### Titulo

Listagem obrigatoria apenas de usuarios ativos

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A consulta usada por `GET /auth/users` passou a filtrar obrigatoriamente `User.active = true`, sem parametro opcional. O teste de listagem foi ajustado para garantir que usuarios desativados nao aparecem nem entram no total paginado.

### Impacto

Antes, usuarios desativados pelo endpoint `DELETE /auth/users/<id>` continuavam aparecendo na listagem administrativa com `active: false`. Agora, a listagem retorna apenas usuarios ativos.

## 2026-05-14 10:18:04 -03

### Titulo

Restricao do endpoint de edicao de usuarios

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

O endpoint administrativo de edicao de usuarios passou a aceitar apenas `PATCH /auth/users/<user_id>` e agora permite alterar somente `email`, `role` ou `roles`. Campos como `password` e `active` sao rejeitados com erro 400.

### Impacto

Antes, a edicao administrativa tambem aceitava `PUT` e podia alterar senha e status ativo. Agora, o contrato fica mais restrito: edicao de usuario cobre apenas email e permissoes, mantendo senha e ativacao/desativacao fora desse endpoint.

## 2026-05-14 10:15:29 -03

### Titulo

Endpoint administrativo para edicao de usuarios locais

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Adicionado o endpoint administrativo `PATCH/PUT /auth/users/<user_id>` para editar usuarios locais. Administradores podem atualizar email, senha, roles e status ativo do usuario; o backend valida usuario inexistente, campos obrigatorios e conflito de email.

### Impacto

Antes, administradores podiam criar, listar e desativar usuarios locais, mas nao editar dados existentes. Agora, a administracao de usuarios tambem permite alterar credenciais, permissoes e reativar/desativar usuarios pelo mesmo recurso `/auth/users`.

## 2026-05-13 [DATA-HORA-AGORA]

### Titulo

Implementacao de suporte a "Remember Me" no login

### Arquivos afetados

- [`pre_api/app.py`]
- [`pre_api/routes/auth_routes.py`]

### Resumo

Adicionado suporte ao parametro `remember_me` no endpoint `POST /auth/login`. Quando `remember_me: true` eh enviado no payload, o Flask-Login cria um cookie persistente (remember me cookie) que dura 30 dias por padrao. Configuradas opcoes `REMEMBER_COOKIE_SECURE` e `REMEMBER_COOKIE_DURATION` para controlar a seguranca e duracao do cookie via variaveis de ambiente.

### Impacto

**Antes**: Usuario voltava para login ao fechar o navegador inteiro, pois a sessao era efemera (session cookie apagado ao fechar navegador).

**Agora**: Se marcar "manter logado" no login, o usuario permanece autenticado por 30 dias (ou valor configurado em `REMEMBER_COOKIE_DURATION`). Deslogar (`POST /auth/logout`) ainda invalida a sessao imediatamente.

## 2026-05-13 10:45:55 -03

### Titulo

Inicializacao manual das tabelas de autenticacao

### Arquivos afetados

- [`pre_api/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/app.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A `pre_api` deixou de executar `initialize_auth_storage(app)` automaticamente ao iniciar a aplicacao. A criacao das tabelas, roles e admin inicial da autenticacao local fica concentrada no comando manual `poetry run python install_auth.py`.

### Impacto

Antes, subir a API podia criar ou ajustar tabelas de autenticacao como efeito colateral. Agora, a API apenas usa as tabelas ja existentes; ambientes novos precisam executar explicitamente o instalador de auth antes de autenticar usuarios.

## 2026-05-13 10:32:59 -03

### Titulo

Migracao para autenticacao local por sessao

### Arquivos afetados

- [`pre_api/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/app.py)
- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/models.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/models.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/install_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/install_auth.py)
- [`pre_api/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/pyproject.toml)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A autenticacao da `pre_api` deixou de depender do Supabase Auth e passou a usar usuarios locais com Flask-Security-Too, Flask-SQLAlchemy e cookies de sessao. Foram adicionados modelos locais de usuario/papel, bootstrap de tabelas/roles, seed opcional de admin por `AUTH_ADMIN_EMAIL` e `AUTH_ADMIN_PASSWORD`, endpoints JSON de login/logout/me e administracao local de usuarios.

Os testes de autenticacao foram reescritos para validar login por sessao, protecao de endpoints, logout, permissoes de admin e desativacao de usuarios usando SQLite em memoria.

### Impacto

Antes, endpoints protegidos exigiam `Authorization: Bearer <token>` validado no Supabase e as rotas administrativas manipulavam usuarios via Supabase Admin API/perfil remoto. Agora, o frontend deve autenticar em `POST /auth/login`, enviar cookies de sessao nas chamadas protegidas e usar roles locais para autorizacao; `DELETE /auth/users/<id>` desativa o usuario local em vez de remover usuario no Supabase.

## 2026-05-07 10:44:05 -03

### Titulo

Listagem e remocao administrativa de usuarios Supabase

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foram adicionados os endpoints administrativos `GET /auth/users` e `DELETE /auth/users/<user_id>`, ambos protegidos pela verificacao de perfil admin via tabela `profiles`. A criacao de usuarios foi ajustada para `POST /auth/sign-up`, separando o fluxo de cadastro do recurso administrativo de usuarios.

### Impacto

Antes, o backend permitia apenas criar usuarios pelo endpoint de autenticacao. Agora, administradores tambem podem listar usuarios com paginacao opcional (`page` e `per_page`) e remover usuarios pelo ID usando a Admin API do Supabase, com suporte opcional a `should_soft_delete=true`.

## 2026-05-07 10:09:26 -03

### Titulo

Remocao do upsert manual de profiles na criacao de usuario

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

O endpoint `POST /auth/users` deixou de criar ou atualizar manualmente a linha da tabela `profiles` apos criar um usuario no Supabase Auth. A funcao auxiliar de upsert em `profiles` foi removida, e os testes foram ajustados para validar apenas a criacao do usuario no Auth.

### Impacto

Antes, o backend podia sobrescrever/criar o `role` do novo usuario em `profiles` quando o payload incluia `role`. Agora, a criacao do perfil fica inteiramente sob responsabilidade do trigger configurado no Supabase, que cria o perfil automaticamente com `role = user`.

## 2026-05-07 09:55:48 -03

### Titulo

Blueprint de autenticacao para criacao de usuarios Supabase

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/app.py)
- [`pre_api/routes/__init__.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/__init__.py)
- [`pre_api/routes/auth_routes.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/routes/auth_routes.py)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foi adicionado o blueprint `auth_bp` com o endpoint `POST /auth/users` para criacao de usuarios no Supabase Auth via Admin API. Antes de criar o usuario, o endpoint consulta a tabela `profiles` com o token Bearer do usuario logado e exige que o perfil retornado tenha `role` igual a `admin`.

O endpoint valida `email` e `password`, aceita campos opcionais do Supabase como `email_confirm`, `phone_confirm`, `user_metadata` e `app_metadata`, e pode criar/atualizar o perfil do novo usuario quando o payload incluir `role`.

### Impacto

Antes nao havia grupo de endpoints de autenticacao nem criacao administrativa de usuarios pelo backend. Agora usuarios autenticados so conseguem criar novos usuarios se a propria linha em `profiles` indicar papel de admin, mantendo a verificacao alinhada com as politicas RLS do Supabase.

## 2026-05-06 14:13:56 -03

### Titulo

Validacao remota de tokens pelo Supabase Auth

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/pyproject.toml)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A autenticacao deixou de validar o JWT localmente via JWKS e passou a consultar o Supabase Auth em `/auth/v1/user` usando o token Bearer recebido. A configuracao agora usa `SUPABASE_URL` e uma chave de API (`SUPABASE_API_KEY`, `SUPABASE_ANON_KEY` ou `SUPABASE_PUBLISHABLE_KEY`) para chamar o Supabase.

Os testes foram atualizados para cobrir token aceito pelo Supabase, token recusado e indisponibilidade do servico de autenticacao.

### Impacto

Antes, o backend validava assinatura, issuer e audience localmente. Agora, a validade do token e confirmada diretamente pelo Supabase Auth, simplificando o codigo e delegando rotacao/revogacao de chaves ao provedor. Caso o Supabase Auth esteja indisponivel, os endpoints protegidos falham fechados com erro 503.

## 2026-05-06 13:56:18 -03

### Titulo

Autenticacao Supabase nos endpoints da API

### Arquivos afetados

- [`pre_api/auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/auth.py)
- [`pre_api/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/app.py)
- [`pre_api/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/pyproject.toml)
- [`pre_api/tests/test_auth.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/tests/test_auth.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foi adicionada uma camada global de autenticacao para a API Flask usando tokens Bearer do Supabase. O backend agora valida o JWT via JWKS, confere issuer, audience, expiracao e subject, e disponibiliza as claims em `flask.g` para futuras regras de autorizacao.

Tambem foram adicionados testes focados para ausencia de token, header malformado, bypass de `OPTIONS`, rota raiz publica, token valido mockado e falha fechada quando a configuracao Supabase nao existe.

### Impacto

Antes, os endpoints JSON da API podiam ser acessados sem autenticacao. Agora, rotas de API exigem `Authorization: Bearer <token>` valido do Supabase, enquanto `OPTIONS` e a rota raiz continuam liberados. Se `SUPABASE_URL` nao estiver configurada, a API falha fechada nos endpoints protegidos.

## 2026-04-30 13:51:55 -03

### Titulo

Defaults comuns dos jobs do scheduler

### Arquivos afetados

- [`pre_api/scheduler.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/scheduler.py)
- [`pre_api/scheduler_jobs.yml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/scheduler_jobs.yml)
- [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/CONFIGURACAO_OBSERVERS_SCHEDULER.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Os campos comuns `trigger`, `max_instances`, `coalesce` e `replace_existing` foram centralizados em defaults no carregamento dos jobs do scheduler. O arquivo `pre_api/scheduler_jobs.yml` passou a manter apenas os campos especificos de cada job, como `id`, `channel`, `hour`, `minute`, `day_of_week` e `day`.

A documentacao do scheduler foi atualizada para mostrar exemplos sem os campos repetidos e explicar que esses defaults ainda podem ser sobrescritos por job quando necessario.

### Impacto

Antes, cada job precisava repetir a mesma configuracao operacional no YAML. Agora, novos jobs herdam automaticamente os defaults comuns, reduzindo duplicacao e mantendo o comportamento anterior dos agendamentos existentes.

## 2026-04-30 13:32:47 -03

### Titulo

Configuracao YAML para jobs do scheduler

### Arquivos afetados

- [`pre_api/scheduler.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/scheduler.py)
- [`pre_api/scheduler_jobs.yml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/scheduler_jobs.yml)
- [`pre_api/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/pyproject.toml)
- [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/CONFIGURACAO_OBSERVERS_SCHEDULER.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Os jobs do scheduler foram movidos do hard code em `_build_scheduler()` para o arquivo `pre_api/scheduler_jobs.yml`. O scheduler agora carrega e valida a lista de jobs via YAML, separando o `channel` usado por `run_scheduled_analysis(...)` dos demais parametros passados ao APScheduler.

Tambem foi adicionada a dependencia explicita `pyyaml` ao pacote `pre_api` e a documentacao passou a orientar alteracoes de horario, recorrencia e novos canais pelo YAML.

### Impacto

Antes, mudar `hour`, `minute`, `day_of_week`, `day` ou adicionar/remover jobs exigia editar `pre_api/scheduler.py`. Agora, essas configuracoes podem ser alteradas diretamente no YAML, mantendo o codigo do scheduler responsavel apenas por carregar e registrar os jobs.

## 2026-04-30 11:02:07 -03

### Titulo

Reuso da instancia do Worker no listener

### Arquivos afetados

- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

A criacao de `Worker(rabbit_admin)` foi movida de dentro do callback de consumo para o inicio de `continuously_listen()`, mantendo uma unica instancia reutilizada pelas mensagens recebidas pelo processo.

### Impacto

Antes, cada mensagem consumida criava um novo `Worker`, recriando dependencias como analyzer, mapper, engine e publisher. Agora, esses objetos sao inicializados uma vez por listener, reduzindo trabalho repetido a cada callback sem alterar o fluxo de processamento das mensagens.

## 2026-04-30 10:36:26 -03

### Titulo

Nomes completos para indicadores configuraveis

### Arquivos afetados

- [`worker/indicator_publisher.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/indicator_publisher.py)
- [`worker/indicator_channels.yml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/indicator_channels.yml)
- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/CONFIGURACAO_OBSERVERS_SCHEDULER.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Os identificadores curtos dos indicadores foram substituidos por nomes completos no YAML, no dicionario `INDICATOR_OBSERVERS` e no `name` dos observers. Exemplos: `eng` virou `engagement`, `per` virou `performance`, `mot` virou `motivation`, `giv` virou `give_up` e `response_foruns` virou `response_forums`.

O worker tambem foi ajustado nos pontos que leem os resultados por nome, como o filtro especial de `give_up` e a montagem dos indicadores de tutores.

### Impacto

Antes, os resultados, erros e registros de status por indicador usavam abreviacoes menos claras. Agora, os nomes gravados e configurados ficam mais legiveis e alinhados ao significado de cada indicador.

## 2026-04-30 10:23:46 -03

### Titulo

Configuracao YAML para indicadores por canal

### Arquivos afetados

- [`worker/indicator_publisher.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/indicator_publisher.py)
- [`worker/indicator_channels.yml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/indicator_channels.yml)
- [`worker/pyproject.toml`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/pyproject.toml)
- [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/CONFIGURACAO_OBSERVERS_SCHEDULER.md)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

O cadastro padrao de indicadores por ator e canal saiu do hard code em `register_default_indicators(...)` e passou a ser carregado de `worker/indicator_channels.yml`. O worker agora valida a estrutura do YAML, resolve cada nome de indicador por meio de `INDICATOR_OBSERVERS` e registra os observers dinamicamente no `IndicatorPublisher`.

Tambem foi adicionada a dependencia explicita `pyyaml` ao pacote do worker e a documentacao de configuracao foi atualizada para orientar alteracoes no arquivo YAML.

### Impacto

Antes, mudar quais indicadores rodam em canais como `diario`, `semanal`, `mensal`, `teste` ou `completo` exigia editar chamadas `publisher.subscribe(...)` no codigo Python. Agora, a associacao pode ser alterada diretamente no YAML, mantendo o codigo responsavel apenas por carregar, validar e instanciar os observers conhecidos.

## 2026-04-28 13:19:37 -03

### Titulo

Agendamentos dos canais semanal e mensal

### Arquivos afetados

- [`pre_api/scheduler.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/scheduler.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

O scheduler passou a registrar jobs separados para os canais `semanal` e `mensal`, ambos usando o entrypoint `run_scheduled_analysis` com o `channel` correspondente.

### Impacto

Antes, apenas o canal `diario` era disparado automaticamente pelo processo de scheduler. Agora, os canais `semanal` e `mensal` tambem sao enfileirados automaticamente nas suas respectivas recorrencias, aproveitando os filtros de disciplinas ativas ja existentes para cada periodo.

## 2026-04-28 11:43:13 -03

### Titulo

Disciplinas ativas por canais diario, semanal e mensal

### Arquivos afetados

- [`src/analysis_lib/analysis/analyzer.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/src/analysis_lib/analysis/analyzer.py)
- [`src/analysis_lib/analysis/Actors/Student/General/subjects.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/src/analysis_lib/analysis/Actors/Student/General/subjects.py)
- [`src/analysis_lib/mapper/map.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/src/analysis_lib/mapper/map.py)
- [`src/analysis_lib/mapper/connectors/moodle3_1.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/src/analysis_lib/mapper/connectors/moodle3_1.py)
- [`pre_api/processor.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/processor.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

Foram adicionados os metodos `get_week_active_subjects` e `get_month_active_subjects` nas camadas de analise, mapper e conector Moodle, mantendo o mesmo formato de resposta de `get_daily_active_subjects`. A consulta Moodle passou a reutilizar um helper por intervalo em segundos, com janelas moveis de 24 horas, 7 dias e 30 dias.

O `Processor.set_subjects_analysis` agora escolhe a busca de disciplinas ativas conforme o `channel`: `diario`, `semanal` ou `mensal`. Quando `subject_ids` nao e informado, o processor passa a enfileirar a lista calculada de disciplinas em vez de limitar a execucao fixa ao subject `78`.

### Impacto

Antes, somente o canal diario tinha filtro de disciplinas ativas e o enfileiramento sem `subject_ids` ficava preso ao subject `78`. Agora, os canais semanal e mensal tambem podem selecionar disciplinas por atividade recente, e o processamento usa todas as disciplinas retornadas pelo filtro do canal, preservando `subject_ids` como mecanismo explicito de limitacao temporaria.

## 2026-04-28 11:24:20 -03

### Titulo

Filtro de colunas do `give_up` no Worker

### Arquivos afetados

- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Resumo

No fluxo `students_subject_analysis`, o DataFrame do indicador `give_up` agora e reduzido para manter apenas as colunas `user_id` e `give_up` antes de entrar na lista `normalized`.

### Impacto

Antes, labels intermediarias acopladas ao calculo de desistencia podiam seguir para o merge e para o upsert dinamico do Worker. Agora, somente o resultado final de desistencia e o identificador do aluno seguem para persistencia, sem alterar o payload sincrono usado pelo Frontend.

## 2026-04-09

### Titulo

Atomicidade entre dados locais e status por indicador

### Arquivos afetados

- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`worker/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/database.py)
- [`pre_api/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/database.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Objetivo

Evitar commits parciais quando a gravacao dos dados locais e a gravacao do status granular dos indicadores acontecem no worker.

### Resumo

Os metodos `upsert_indicator_status(...)` e `_upsert_dynamic(...)` passaram a aceitar uma conexao externa opcional, permitindo participar de uma transacao ja aberta. No worker, as gravacoes de `local_indicators_students`, `local_indicators_tutors` e dos status em `subject_indicator_status` foram reorganizadas para acontecerem dentro de um mesmo `with engine.begin() as tx_conn`.

No fluxo de tutores, o `UPDATE subjects_status` que grava `start_date`, `end_date` e `update_type` tambem passou a usar essa mesma transacao compartilhada. Assim, se qualquer etapa do bloco falhar, nada e persistido parcialmente.

### Impacto

Antes, os status por indicador podiam ser commitados antes do upsert dos dados locais, deixando o banco em estado inconsistente quando a gravacao principal falhava depois. Agora, esses elementos passam a ser confirmados juntos no mesmo commit, reduzindo divergencias entre dados e status persistidos.

### Titulo

Ajuste do instalador para seguir o padrao de criacao de tabelas

### Arquivos afetados

- [`worker/install.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/install.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Objetivo

Alinhar a criacao da tabela `subject_indicator_status` ao mesmo padrao usado pelas demais tabelas do instalador.

### Resumo

O helper `create_table(...)` passou a aceitar definicoes de coluna com opcoes adicionais, como `nullable=False`, por meio de tuplas `(tipo, opcoes)`. Com isso, a tabela `subject_indicator_status` deixou de ser criada com `Table(...)` manual inline e passou a usar o mesmo fluxo declarativo das outras tabelas do arquivo.

### Impacto

Nao ha mudanca funcional no schema previsto da tabela. O impacto e de padronizacao e manutencao: o instalador fica mais consistente e a definicao da nova tabela passa a seguir o mesmo estilo do restante do arquivo.

### Titulo

Rastreamento granular de status por indicador

### Arquivos afetados

- [`worker/install.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/install.py)
- [`worker/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/database.py)
- [`pre_api/database.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/database.py)
- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Objetivo

Persistir o status individual de cada indicador por disciplina e ator, sem depender apenas do status global salvo em `subjects_status`.

### Resumo

Foi adicionada a tabela `subject_indicator_status` ao instalador do banco, com chave primaria composta por `institution_id`, `subject_id`, `actor` e `indicator_name`. As classes `DatabaseAdmin` do worker e da pre API passaram a expor a definicao dessa tabela e um metodo `upsert_indicator_status(...)` baseado em `INSERT ... ON CONFLICT DO UPDATE`.

No worker, os metodos `students_subject_analysis` e `tutors_subject_analysis` agora percorrem os indicadores retornados por `notify(...)` e registram `D` para indicadores presentes em `results` e `E` para indicadores presentes em `errors`, sempre atualizando tambem o `updated_at`.

### Impacto

Antes, o sistema informava apenas o estado agregado da disciplina em `subjects_status`, sem mostrar quais indicadores foram concluidos ou falharam individualmente. Agora, passa a existir rastreabilidade granular por indicador e por ator, o que melhora diagnostico, auditoria e reprocessamento direcionado sem alterar o fluxo atual de status global da disciplina.

### Titulo

Refatoracao do fluxo de status de `subject_analysis` para 4 estados

### Arquivos afetados

- [`pre_api/processor.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/pre_api/processor.py)
- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`MUDANCAS_LOG.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/MUDANCAS_LOG.md)

### Objetivo

Separar o status de enfileiramento do status de execucao real da analise de disciplinas, adotando os estados `Q`, `P`, `D` e `E`.

### Resumo

Antes, a disciplina era marcada como `P` ainda na API, antes mesmo de ser consumida pelo RabbitMQ, e so depois passava para `D` em caso de sucesso. Isso misturava fila com processamento em andamento e tambem nao garantia um estado explicito de erro quando a execucao falhava.

Agora, o fluxo ficou assim:

- `Q` quando a tarefa e registrada e enviada para a fila;
- `P` quando o worker realmente inicia o processamento da disciplina;
- `D` quando a execucao termina com sucesso;
- `E` quando ocorre excecao durante o processamento no worker.

No worker, a rotina `subject_analysis` passou a marcar `P` logo no inicio, registrar `E` no `except` com log e traceback, e relancar a excecao para nao mascarar falhas. O caminho de sucesso com `D` foi preservado, inclusive no caso sem dados normalizados em `students_subject_analysis`.

### Impacto

O comportamento anterior podia deixar a disciplina com status de processamento em andamento mesmo quando ela ainda estava apenas aguardando consumo da fila. Com a mudanca, o status persistido passa a refletir melhor o ciclo real da tarefa e evita que falhas deixem a execucao indefinidamente em `P`.

## 2026-04-08

### Titulo

Atualizacoes Parciais Assincronas com Upsert Dinamico no Worker

### Arquivos afetados

- [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py)
- [`worker/UPSERT_DINAMICO.md`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/UPSERT_DINAMICO.md)

### Objetivo

Esta mudanca introduziu suporte a atualizacoes parciais assincronas por channel no Worker, evitando que uma execucao apague indicadores calculados anteriormente por outros canais.

Antes, o fluxo assumia que cada execucao recalculava o conjunto completo de indicadores da disciplina. Isso deixava de ser verdade quando canais diferentes passaram a calcular subconjuntos diferentes de colunas, como `diario`, `semanal` ou outros observers parciais.

### Como funcionava antes

#### 1. Analises locais

Nas funcoes `students_subject_analysis` e `tutors_subject_analysis`, o Worker:

- montava um `DataFrame` final com um conjunto fixo de colunas esperadas;
- preenchia com `pd.NA` ou `np.nan` todas as colunas que nao tinham vindo do channel atual;
- executava `DELETE` da disciplina inteira na tabela local;
- fazia `to_sql(..., if_exists="append")` com o `DataFrame` completo.

Na pratica, isso significava:

- se o channel atual calculasse apenas engajamento, as colunas de performance, cognitivo, motivacao etc. eram enviadas como nulas;
- como a disciplina inteira era apagada antes do insert, os dados anteriormente calculados por outros canais eram perdidos;
- o banco passava a refletir apenas o ultimo channel executado, e nao a composicao incremental dos canais.

#### 2. Indicadores globais

Nas funcoes globais, especialmente `save_subject_global_indicators_students`, o calculo usava diretamente o `subject_df` retornado da analise local.

Isso funcionava enquanto o `subject_df` continha todas as colunas. Mas, quando os canais passaram a ser parciais, esse `subject_df` deixou de representar o estado real completo da disciplina.

Consequencias:

- medias globais podiam ser recalculadas sobre um recorte incompleto;
- colunas ausentes podiam virar `NULL` ou distorcer medias;
- a consistencia do agregado dependia da ordem em que os canais rodavam.

#### 3. Tabelas globais

As tabelas `global_indicators_students` e `global_indicators_tutors` tambem usavam `DELETE` seguido de `to_sql`.

Isso criava o mesmo problema de substituicao destrutiva:

- um novo processamento removia o registro anterior antes de inserir o novo;
- em tutores, a discretizacao apagava registros da versao inteira antes de recriar;
- qualquer resultado parcial intermediario podia sobrescrever o estado ja existente.

### Como funciona agora

#### 1. Upsert dinamico nas tabelas locais

Foi introduzido um helper interno de upsert dinamico baseado em:

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert
```

O novo comportamento e:

- o `DataFrame` local e convertido para `records` com `to_dict(orient="records")`;
- o `INSERT ... ON CONFLICT DO UPDATE` usa como chave a PK da tabela;
- o `set_` do update e montado dinamicamente, apenas com as colunas presentes nos `records`;
- colunas que nao vieram no channel atual nao entram no `UPDATE`;
- logo, o banco preserva os valores previamente gravados nessas colunas.

Exemplo conceitual:

- execucao 1 grava apenas colunas de engajamento;
- execucao 2 grava apenas colunas de performance;
- resultado final no banco: a mesma linha do aluno ou tutor passa a ter engajamento e performance, sem perder o que ja existia.

#### 2. `DataFrame` parcial de verdade

Nas funcoes `students_subject_analysis` e `tutors_subject_analysis`:

- o preenchimento artificial de colunas ausentes foi removido;
- o `DataFrame` final agora contem sempre as PKs e apenas as colunas realmente produzidas naquele processamento;
- os `groupby(...).agg(...)` foram ajustados para agregar dinamicamente somente colunas presentes.

Isso muda o contrato interno:

- antes: o retorno era um shape fixo, com varias colunas nulas;
- agora: o retorno e parcial, refletindo exatamente o channel executado.

#### 3. Releitura do banco para calculos globais

##### Students

`save_subject_global_indicators_students` nao calcula mais as medias usando diretamente o `subject_df` parcial recebido da analise.

Agora o fluxo e:

1. extrai `subject_id` e `version` do processamento atual;
2. relê do banco todo o estado da disciplina em `local_indicators_students`;
3. calcula as medias globais sobre esse estado completo;
4. salva o resultado em `global_indicators_students` via upsert dinamico.

Isso garante que:

- o calculo global sempre usa a visao consolidada da disciplina;
- execucoes parciais nao destroem o agregado;
- a ordem dos channels deixa de afetar o resultado final de forma destrutiva.

##### Tutors

Em tutores, duas coisas mudaram:

- `save_NaN_global_indicators_tutors` passou a reler `local_indicators_tutors` antes de garantir o placeholder global da disciplina;
- `discretize_global_indicators_tutors` deixou de apagar registros da versao inteira e passou a fazer upsert por disciplina.

Isso reduz o risco de uma disciplina sobrescrever ou apagar resultados de outras disciplinas da mesma versao.

### Comparativo rapido

#### Antes

- `DELETE` da disciplina ou da versao inteira;
- `to_sql` com shape fixo;
- colunas ausentes preenchidas com nulo;
- ultimo channel podia apagar informacoes de channels anteriores;
- calculo global dependia do `DataFrame` parcial em memoria.

#### Agora

- `upsert` por PK;
- update apenas nas colunas presentes no processamento atual;
- sem preenchimento artificial de colunas ausentes;
- dados anteriores sao preservados;
- calculo global relê o estado consolidado do banco antes de agregar.

### Funcoes impactadas

As principais mudancas ficaram em [`worker/app.py`](/home/alfredolsn/Documents/tarrafa/Tarrafa-backend/worker/app.py):

- `students_subject_analysis`
- `tutors_subject_analysis`
- `save_subject_global_indicators_students`
- `save_NaN_global_indicators_tutors`
- `discretize_global_indicators_tutors`
- helpers novos: `_df_to_records`, `_upsert_dynamic`, `_aggregate_first_by_keys`

### Beneficios da mudanca

- suporte real a atualizacoes parciais assincronas por channel;
- preservacao de indicadores ja calculados;
- menor acoplamento entre channels;
- menor risco de perda de dados por sobrescrita com `NULL`;
- agregacoes globais mais confiaveis, porque passam a usar o estado persistido como fonte da verdade.

### Ponto de atencao

Essa nova abordagem assume que o banco usado por essas tabelas suporta `ON CONFLICT DO UPDATE` do PostgreSQL e que as PKs das tabelas locais e globais estao corretamente definidas.

Tambem e importante validar em ambiente integrado os cenarios abaixo:

- rodar channels diferentes da mesma disciplina em sequencia;
- confirmar que colunas antigas permanecem intactas;
- recalcular globais apos multiplas atualizacoes parciais;
- verificar idempotencia ao reprocessar o mesmo channel.
