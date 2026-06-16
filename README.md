# Tarrafa Backend

Backend do Tarrafa para coleta, processamento e disponibilização de indicadores educacionais a partir de dados do Moodle. O projeto combina uma API Flask, um worker assíncrono e uma biblioteca de análise compartilhada para executar análises de estudantes, tutores, disciplinas e indicadores globais.

## Sumário

- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Configuração do ambiente](#configuração-do-ambiente)
- [Primeira execução](#primeira-execução)
- [Como executar o projeto](#como-executar-o-projeto)
- [Configuração do Moodle](#configuração-do-moodle)
- [Scheduler e canais de análise](#scheduler-e-canais-de-análise)
- [Endpoints principais](#endpoints-principais)
- [Modelo de mensagens](#modelo-de-mensagens)
- [Solução de problemas](#solução-de-problemas)

## Arquitetura

O repositório é organizado em três blocos principais:

| Caminho | Responsabilidade |
| --- | --- |
| `pre_api/` | API Flask, autenticação local, rotas administrativas e rotas de consulta dos indicadores. |
| `worker/` | Consumidor RabbitMQ responsável por processar tarefas de análise e persistir resultados no PostgreSQL local. |
| `src/analysis_lib/` | Biblioteca compartilhada com mapeadores e analisadores usados pela API e pelo worker. |

Serviços de apoio:

- **PostgreSQL**: banco local da aplicação, usado para configuração, status e resultados consolidados.
- **RabbitMQ**: fila de tarefas entre API e worker.
- **pgAdmin**: interface opcional para inspecionar o PostgreSQL local.
- **Moodle/MySQL institucional**: fonte externa de dados, configurada via API administrativa.

Fluxo resumido:

1. A API recebe uma solicitação de análise.
2. A API lê a configuração salva do Moodle e publica tarefas na fila `tasks_to_process`.
3. O worker consome as tarefas, executa os analisadores e grava os resultados no PostgreSQL.
4. A API consulta o PostgreSQL para entregar os indicadores ao frontend ou a consumidores externos.

## Pré-requisitos

- Python `>= 3.10`
- Poetry
- Docker e Docker Compose
- Acesso ao banco Moodle/MySQL institucional
- Portas locais livres:
  - `5432` para PostgreSQL
  - `5672` para RabbitMQ
  - `15672` para painel do RabbitMQ
  - `8080` para pgAdmin

## Configuração do ambiente

Crie o arquivo `.env` na raiz do projeto a partir do exemplo:

```bash
cp .env.example .env
```

O `.env.example` já vem com os valores padrão usados pelo ambiente local do `docker-compose.yml`. Assim, após copiar o arquivo, a aplicação já aponta para o PostgreSQL e o RabbitMQ locais:

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

Importante: o `docker-compose.yml` atual não usa as variáveis `DB_USER`, `DB_PASSWORD` e `DB_DATABASE` do `.env` para criar o container do PostgreSQL. Ele define diretamente `POSTGRES_USER=tarrafa`, `POSTGRES_PASSWORD=tarrafa123` e `POSTGRES_DB=tarrafa_db`. O mesmo vale para o RabbitMQ, que usa `guest/guest` diretamente no Compose. Por isso, o `.env.example` repete esses valores para facilitar a execução local.

Observações:

- O recomendado é trocar credenciais, segredos e senha do administrador antes de usar o projeto em ambientes compartilhados, homologação ou produção.
- Se alterar credenciais do PostgreSQL ou RabbitMQ, atualize os dois lugares: o `.env` usado pela aplicação e o serviço correspondente no `docker-compose.yml`.
- A configuração do Moodle não deve ser colocada diretamente no `.env`; ela é cadastrada pela rota administrativa `PUT /admin/moodle-config`.
- Se executar os comandos fora da raiz do projeto e houver erro de importação, exporte o `PYTHONPATH`:

```bash
export PYTHONPATH=..
```

## Primeira execução

Suba os serviços locais:

```bash
docker compose up -d
```

Se sua instalação usar o binário legado:

```bash
docker-compose up -d
```

Instale as dependências do worker e crie as tabelas principais:

```bash
cd worker
poetry install
poetry run python install.py
```

Instale as dependências da API e inicialize a autenticação local:

```bash
cd ../pre_api
poetry install
poetry run python install_auth.py
```

Ao final, o banco local terá as tabelas de configuração, status, indicadores e autenticação necessárias para iniciar a aplicação.

## Como executar o projeto

Abra dois terminais, um para a API e outro para o worker.

Terminal 1, API:

```bash
cd pre_api
poetry run python app.py
```

Por padrão, o Flask disponibiliza a aplicação em:

```text
http://localhost:5000
```

Terminal 2, worker:

```bash
cd worker
poetry run python app.py
```

O worker ficará aguardando mensagens na fila `tasks_to_process`.

Para limpar os dados locais do worker e recriar a estrutura antes de iniciar:

```bash
cd worker
poetry run python clear.py
poetry run python install.py
poetry run python app.py
```

## Configuração do Moodle

A conexão com o banco Moodle/MySQL institucional é cadastrada por um usuário administrador.

Rotas administrativas:

- `PUT /admin/moodle-config`: salva a configuração do Moodle no PostgreSQL local.
- `GET /admin/moodle-config`: retorna a configuração cadastrada sem expor a senha.
- `POST /admin/moodle-config/test`: testa uma configuração sem salvá-la.

Depois que a configuração estiver salva, a análise pode ser iniciada por:

```http
PUT /analysis
Content-Type: application/json

{
  "channel": "diario"
}
```

O corpo da requisição deve conter apenas opções operacionais, como o canal de análise. A conexão Moodle usada na análise vem da configuração persistida.

## Scheduler e canais de análise

O projeto possui suporte a agendamentos automáticos via APScheduler.

Para executar o scheduler:

```bash
cd pre_api
poetry run python scheduler.py
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


## Endpoints principais

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

## Modelo de mensagens

As tarefas são publicadas na fila `tasks_to_process` e possuem prioridade conforme o tipo de operação. Tarefas solicitadas pelo usuário tendem a ter prioridade maior, enquanto tarefas internas ou derivadas do worker podem ter prioridade menor.

Quando uma análise é grande, o worker pode dividi-la em subtarefas para evitar que uma execução longa bloqueie análises menores. Esse comportamento permite que o sistema continue responsivo durante processamentos globais.

Modelo geral de processamento:

1. A API publica uma tarefa em `tasks_to_process`.
2. O worker inicia a execução da tarefa.
3. O worker persiste os resultados no PostgreSQL local.
4. A API passa a disponibilizar os dados pelas rotas de consulta.

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

## Solução de problemas

Verificar containers:

```bash
docker compose ps
```

Ver logs dos serviços:

```bash
docker compose logs -f postgres
docker compose logs -f rabbitmq
```

Testar se o RabbitMQ está acessível:

```text
http://localhost:15672
```

Credenciais padrão do painel RabbitMQ local:

```text
guest / guest
```

Credenciais padrão do pgAdmin local:

```text
http://localhost:8080
admin@admin.com / admin
```

Erros comuns:

- **Erro de conexão com PostgreSQL**: confirme se `docker compose up -d` foi executado e se as variáveis `DB_*` do `.env` batem com o `docker-compose.yml`.
- **Erro de conexão com RabbitMQ**: confirme se o serviço `rabbitmq` está saudável e se `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER` e `RABBITMQ_PASSWORD` estão corretos.
- **Erro ao iniciar análise**: confirme se `PUT /admin/moodle-config` já foi executado com uma conexão Moodle válida.
- **Erro de importação de `src`**: execute os comandos a partir de `pre_api/` ou `worker/` com as dependências instaladas pelo Poetry; se necessário, exporte `PYTHONPATH=..`.
- **Rotas protegidas retornando erro de autenticação**: execute `poetry run python install_auth.py` dentro de `pre_api/` e confira `AUTH_ADMIN_EMAIL` e `AUTH_ADMIN_PASSWORD` no `.env`.
