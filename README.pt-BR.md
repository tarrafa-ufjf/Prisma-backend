<p align="center">
  <img src="docs/assets/prisma_banner.png" alt="Banner Prisma" width="65%">
</p>

<p align="center">
  Uma interface web para monitoramento acadêmico por meio de dashboards, indicadores e visualizações de dados educacionais.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-004b8d" alt="Versão">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-2fb594" alt="Licença"></a>
  <img src="https://img.shields.io/badge/Research-Tool-orange" alt="Ferramenta">
</p>

# Tarrafa Backend

📝 **Disponível em outros idiomas:** [English](./README.md)

Backend do Tarrafa para coletar, processar e servir indicadores educacionais a partir de dados do Moodle. O projeto combina uma API Flask, um worker assíncrono e uma biblioteca compartilhada de análises para executar análises de estudantes, tutores, disciplinas e indicadores gerais.

## Arquitetura

O repositório é organizado em três blocos principais:

| Caminho | Responsabilidade |
| --- | --- |
| `pre_api/` | API Flask, autenticação local, rotas administrativas e rotas de consulta de indicadores. |
| `worker/` | Consumidor RabbitMQ responsável por processar tarefas de análise e persistir resultados no PostgreSQL local. |
| `src/analysis_lib/` | Biblioteca compartilhada com mapeadores e analisadores usados pela API e pelo worker. |

Serviços de apoio:

- **PostgreSQL**: banco de dados local da aplicação, usado para configuração, status e resultados consolidados.
- **RabbitMQ**: fila de tarefas entre a API e o worker.
- **pgAdmin**: interface opcional para inspecionar o banco PostgreSQL local.
- **Moodle/MySQL institucional**: fonte de dados externa, configurada pela API administrativa.

Fluxo resumido:

1. A API recebe uma solicitação de análise.
2. A API lê a configuração Moodle salva e publica tarefas na fila `tasks_to_process`.
3. O worker consome as tarefas, executa os analisadores e grava os resultados no PostgreSQL.
4. A API consulta o PostgreSQL para entregar indicadores ao frontend ou a consumidores externos.

## Requisitos

- Python `>= 3.11`
- uv
- Docker e Docker Compose
- Acesso ao banco Moodle/MySQL institucional
- Portas locais disponíveis:
  - `5432` para PostgreSQL
  - `5672` para RabbitMQ
  - `15672` para o painel de gerenciamento do RabbitMQ
  - `8080` para pgAdmin

## Configuração de Ambiente

Crie um arquivo `.env` na raiz do projeto a partir do exemplo:

```bash
cp .env.example .env
```

O arquivo `.env.example` já inclui os valores padrão usados pelo ambiente local. Depois de copiar o arquivo, tanto a aplicação quanto o `docker-compose.yml` usam essas variáveis para configurar PostgreSQL e RabbitMQ:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=tarrafa
DB_PASSWORD=tarrafa123
DB_DATABASE=tarrafa_db

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

SECRET_KEY=change_me_to_a_long_random_secret
MOODLE_CONFIG_ENCRYPTION_KEY=change_me_to_a_different_long_random_secret
SECURITY_PASSWORD_SALT=change_me_to_a_long_random_salt
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=false
REMEMBER_COOKIE_SAMESITE=Lax
AUTH_ADMIN_EMAIL=admin@example.com
AUTH_ADMIN_PASSWORD=change_me_admin_password



SCHEDULER_TIMEZONE=America/Sao_Paulo
```

Importante: o Docker Compose carrega automaticamente o arquivo `.env` da raiz do projeto para interpolar variáveis como `DB_USER`, `DB_PASSWORD`, `DB_DATABASE`, `DB_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD` e `RABBITMQ_PORT`. Se o `.env` não existir, o `docker-compose.yml` ainda inclui valores padrão para execução local.

Observações:

- Recomenda-se substituir credenciais, segredos e a senha de administrador antes de usar o projeto em ambientes compartilhados, de homologação ou de produção.
- Se você alterar credenciais ou portas do PostgreSQL ou RabbitMQ, atualize o `.env` antes de iniciar os containers.
- A configuração do Moodle não deve ser colocada diretamente no `.env`; ela é registrada pela rota administrativa `PUT /admin/moodle-config`.
- Execute comandos Python dentro de `pre_api/` ou `worker/`; `uv sync` instala o pacote compartilhado `src/` como dependência local editável.

## Primeira Execução

Inicie os serviços locais:

```bash
docker compose up -d
```

Se sua instalação usa o binário legado:

```bash
docker-compose up -d
```

Instale as dependências do worker e crie as tabelas principais:

```bash
cd worker
uv sync
uv run python install.py
```

Instale as dependências da API e inicialize a autenticação local:

```bash
cd ../pre_api
uv sync
uv run python install_auth.py
```

Depois disso, o banco local terá as tabelas de configuração, status, indicadores e autenticação necessárias para iniciar a aplicação.

## Executando o Projeto

Abra dois terminais, um para a API e outro para o worker.

Terminal 1, API:

```bash
cd pre_api
uv run python app.py
```

Por padrão, o Flask serve a aplicação em:

```text
http://localhost:5000
```

Terminal 2, worker:

```bash
cd worker
uv run python app.py
```

O worker aguardará mensagens na fila `tasks_to_process`.

Para limpar os dados locais do worker e recriar a estrutura antes de iniciar:

```bash
cd worker
uv run python clear.py
uv run python install.py
uv run python app.py
```

## Configuração do Moodle

A conexão com o banco Moodle/MySQL institucional é registrada por um usuário administrador.

Rotas administrativas:

- `PUT /admin/moodle-config`: salva a configuração do Moodle no banco PostgreSQL local.
- `GET /admin/moodle-config`: retorna a configuração registrada sem expor a senha.
- `POST /admin/moodle-config/test`: testa uma configuração sem salvá-la.

Depois que a configuração for salva, uma análise pode ser iniciada com:

```http
PUT /analysis
Content-Type: application/json

{
  "channel": "diario"
}
```

O corpo da requisição deve conter apenas opções operacionais, como o canal de análise. A conexão Moodle usada na análise vem da configuração persistida.

## Scheduler e Canais de Análise

O projeto oferece suporte a agendamento automático por meio do APScheduler.

Para executar o scheduler:

```bash
cd pre_api
uv run python scheduler.py
```

Os jobs são configurados em:

```text
pre_api/scheduler_jobs.yml
```

O status do scheduler pode ser consultado em:

```http
GET /admin/scheduler/status
```

Para configurar canais de análise, observers de indicadores e agendamentos automáticos, consulte [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](CONFIGURACAO_OBSERVERS_SCHEDULER.md).

## Principais Endpoints

Autenticação:

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /auth/users`
- `POST /auth/users`
- `PATCH /auth/users/<user_id>`
- `DELETE /auth/users/<user_id>`

Administração:

- `GET /admin/moodle-config`
- `PUT /admin/moodle-config`
- `POST /admin/moodle-config/test`
- `GET /admin/scheduler/status`

Análise:

- `PUT /analysis`

Consultas de estudantes:

- `GET /subjects`
- `GET /analysis/subject/<id>/summary`
- `GET /analysis/subject/<id>/indicators`
- `GET /analysis/subject/<id>/info_graphs`
- `GET /analysis/subject/<id>/rankings`
- `GET /analysis/subject/<id>/students/<indicator>`
- `GET /analysis/subject/<subject_id>/student/<student_id>/<indicator>`
- `GET /analysis/general/summary`
- `GET /analysis/general/indicators`
- `GET /analysis/general/rankings`
- `GET /analysis/general/subjects/indicators`

Consultas de tutores:

- `GET /subjects/tutors`
- `GET /analysis/tutors/subject/<id>/summary`
- `GET /analysis/tutors/subject/<id>/indicators`
- `GET /analysis/tutors/subject/<id>/interaction_channels`
- `GET /analysis/tutors/subject/<id>/rankings`
- `GET /analysis/tutors/subject/<id>/response_forums`
- `GET /analysis/tutors/subject/<id>/access`
- `GET /analysis/tutors/subject/<id>/feedback`
- `GET /analysis/tutors/subject/<subject_id>/tutor/<tutor_id>/<indicator>`
- `GET /analysis/tutors/general/summary`
- `GET /analysis/tutors/general/indicators`
- `GET /analysis/tutors/general/rankings`
- `GET /analysis/tutors/general/subjects/indicators`

## Modelo de Mensagens

As tarefas são publicadas na fila `tasks_to_process` e possuem prioridade de acordo com o tipo de operação. Tarefas solicitadas pelo usuário tendem a ter prioridade mais alta, enquanto tarefas internas ou derivadas do worker podem ter prioridade menor.

Quando uma análise é grande, o worker pode dividi-la em subtarefas para impedir que uma execução longa bloqueie análises menores. Esse comportamento permite que o sistema continue responsivo durante processamentos globais.

Modelo geral de processamento:

1. A API publica uma tarefa em `tasks_to_process`.
2. O worker inicia a execução da tarefa.
3. O worker persiste os resultados no banco PostgreSQL local.
4. A API disponibiliza os dados pelas rotas de consulta.

Exemplo de tarefa:

```json
{
  "name": "1:subject_analysis",
  "version": "4.1",
  "body": {
    "db_inst_config": {
      "host": "localhost",
      "port": 3306,
      "database": "moodle",
      "user": "moodle_user",
      "password": "secret"
    },
    "analysis_config": {
      "subject_id": 123,
      "channel": "diario"
    },
    "type": "subject_analysis"
  }
}
```

## Solução de Problemas

Verifique os containers:

```bash
docker compose ps
```

Veja os logs dos serviços:

```bash
docker compose logs -f postgres
docker compose logs -f rabbitmq
```

Teste se o RabbitMQ está acessível:

```text
http://localhost:15672
```

Credenciais padrão para o painel local do RabbitMQ:

```text
guest / guest
```

Credenciais padrão para a instância local do pgAdmin:

```text
http://localhost:8080
admin@admin.com / admin
```

Erros comuns:

- **Erro de conexão com PostgreSQL**: confirme que `docker compose up -d` foi executado e que as variáveis `DB_*` no `.env` correspondem ao `docker-compose.yml`.
- **Erro de conexão com RabbitMQ**: confirme que o serviço `rabbitmq` está saudável e que `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER` e `RABBITMQ_PASSWORD` estão corretos.
- **Erro ao iniciar uma análise**: confirme que `PUT /admin/moodle-config` já foi executado com uma conexão Moodle válida.
- **Erro de importação de `src`**: execute `uv sync` novamente dentro de `pre_api/` ou `worker/` para que o pacote local compartilhado seja instalado nesse ambiente.
- **Rotas protegidas retornam erro de autenticação**: execute `uv run python install_auth.py` dentro de `pre_api/` e verifique `AUTH_ADMIN_EMAIL` e `AUTH_ADMIN_PASSWORD` no `.env`.

## Licença

Este projeto é licenciado sob a licença MIT. Consulte a referência da licença em [LICENSE](./LICENSE).
