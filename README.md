<p align="center">
  <img src="docs/assets/prisma_banner.png" alt="Prisma Banner" width="65%">
</p>

<p align="center">
  A web interface for academic monitoring through dashboards, indicators, and educational data visualizations.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-004b8d" alt="Version">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-2fb594" alt="License"></a>
  <img src="https://img.shields.io/badge/Research-Tool-orange" alt="Tool">
</p>

# Tarrafa Backend

Tarrafa backend for collecting, processing, and serving educational indicators from Moodle data. The project combines a Flask API, an asynchronous worker, and a shared analysis library to run analyses for students, tutors, courses, and global indicators.

## Architecture

The repository is organized into three main blocks:

| Path | Responsibility |
| --- | --- |
| `pre_api/` | Flask API, local authentication, administrative routes, and indicator query routes. |
| `worker/` | RabbitMQ consumer responsible for processing analysis tasks and persisting results in the local PostgreSQL database. |
| `src/analysis_lib/` | Shared library with mappers and analyzers used by the API and the worker. |

Supporting services:

- **PostgreSQL**: local application database, used for configuration, status, and consolidated results.
- **RabbitMQ**: task queue between the API and the worker.
- **pgAdmin**: optional interface for inspecting the local PostgreSQL database.
- **Institutional Moodle/MySQL**: external data source, configured through the administrative API.

Summary flow:

1. The API receives an analysis request.
2. The API reads the saved Moodle configuration and publishes tasks to the `tasks_to_process` queue.
3. The worker consumes the tasks, runs the analyzers, and writes the results to PostgreSQL.
4. The API queries PostgreSQL to deliver indicators to the frontend or to external consumers.

## Requirements

- Python `>= 3.10`
- uv
- Docker and Docker Compose
- Access to the institutional Moodle/MySQL database
- Available local ports:
  - `5432` for PostgreSQL
  - `5672` for RabbitMQ
  - `15672` for the RabbitMQ management panel
  - `8080` for pgAdmin

## Environment Configuration

Create a `.env` file in the project root from the example:

```bash
cp .env.example .env
```

The `.env.example` file already includes the default values used by the local environment. After copying the file, both the application and `docker-compose.yml` use these variables to configure PostgreSQL and RabbitMQ:

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

Important: Docker Compose automatically loads the `.env` file from the project root to interpolate variables such as `DB_USER`, `DB_PASSWORD`, `DB_DATABASE`, `DB_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, and `RABBITMQ_PORT`. If `.env` does not exist, `docker-compose.yml` still includes default values for local execution.

Notes:

- It is recommended to replace credentials, secrets, and the administrator password before using the project in shared, staging, or production environments.
- If you change PostgreSQL or RabbitMQ credentials or ports, update `.env` before starting the containers.
- The Moodle configuration should not be placed directly in `.env`; it is registered through the `PUT /admin/moodle-config` administrative route.
- Run Python commands from inside `pre_api/` or `worker/`; `uv sync` installs the shared `src/` package as a local editable dependency.

## First Run

Start the local services:

```bash
docker compose up -d
```

If your installation uses the legacy binary:

```bash
docker-compose up -d
```

Install the worker dependencies and create the main tables:

```bash
cd worker
uv sync
uv run python install.py
```

Install the API dependencies and initialize local authentication:

```bash
cd ../pre_api
uv sync
uv run python install_auth.py
```

After this, the local database will have the configuration, status, indicator, and authentication tables required to start the application.

## Running the Project

Open two terminals, one for the API and one for the worker.

Terminal 1, API:

```bash
cd pre_api
uv run python app.py
```

By default, Flask serves the application at:

```text
http://localhost:5000
```

Terminal 2, worker:

```bash
cd worker
uv run python app.py
```

The worker will wait for messages in the `tasks_to_process` queue.

To clear the worker's local data and recreate the structure before starting:

```bash
cd worker
uv run python clear.py
uv run python install.py
uv run python app.py
```

## Moodle Configuration

The connection to the institutional Moodle/MySQL database is registered by an administrator user.

Administrative routes:

- `PUT /admin/moodle-config`: saves the Moodle configuration in the local PostgreSQL database.
- `GET /admin/moodle-config`: returns the registered configuration without exposing the password.
- `POST /admin/moodle-config/test`: tests a configuration without saving it.

After the configuration has been saved, an analysis can be started with:

```http
PUT /analysis
Content-Type: application/json

{
  "channel": "diario"
}
```

The request body should contain only operational options, such as the analysis channel. The Moodle connection used in the analysis comes from the persisted configuration.

## Scheduler and Analysis Channels

The project supports automatic scheduling through APScheduler.

To run the scheduler:

```bash
cd pre_api
uv run python scheduler.py
```

Jobs are configured in:

```text
pre_api/scheduler_jobs.yml
```

The scheduler status can be checked at:

```http
GET /admin/scheduler/status
```

To configure analysis channels, indicator observers, and automatic schedules, see [`CONFIGURACAO_OBSERVERS_SCHEDULER.md`](CONFIGURACAO_OBSERVERS_SCHEDULER.md).

## Main Endpoints

Authentication:

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /auth/users`
- `POST /auth/users`
- `PATCH /auth/users/<user_id>`
- `DELETE /auth/users/<user_id>`

Administration:

- `GET /admin/moodle-config`
- `PUT /admin/moodle-config`
- `POST /admin/moodle-config/test`
- `GET /admin/scheduler/status`

Analysis:

- `PUT /analysis`

Student queries:

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

Tutor queries:

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

## Message Model

Tasks are published to the `tasks_to_process` queue and have priority according to the operation type. Tasks requested by the user tend to have higher priority, while internal or worker-derived tasks may have lower priority.

When an analysis is large, the worker can split it into subtasks to prevent a long execution from blocking smaller analyses. This behavior allows the system to remain responsive during global processing.

General processing model:

1. The API publishes a task to `tasks_to_process`.
2. The worker starts executing the task.
3. The worker persists the results in the local PostgreSQL database.
4. The API makes the data available through the query routes.

Example task:

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

## Troubleshooting

Check containers:

```bash
docker compose ps
```

View service logs:

```bash
docker compose logs -f postgres
docker compose logs -f rabbitmq
```

Test whether RabbitMQ is reachable:

```text
http://localhost:15672
```

Default credentials for the local RabbitMQ panel:

```text
guest / guest
```

Default credentials for the local pgAdmin instance:

```text
http://localhost:8080
admin@admin.com / admin
```

Common errors:

- **PostgreSQL connection error**: confirm that `docker compose up -d` has been run and that the `DB_*` variables in `.env` match `docker-compose.yml`.
- **RabbitMQ connection error**: confirm that the `rabbitmq` service is healthy and that `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, and `RABBITMQ_PASSWORD` are correct.
- **Error starting an analysis**: confirm that `PUT /admin/moodle-config` has already been run with a valid Moodle connection.
- **`src` import error**: run `uv sync` again inside `pre_api/` or `worker/` so the shared local package is installed in that environment.
- **Protected routes return an authentication error**: run `uv run python install_auth.py` inside `pre_api/` and check `AUTH_ADMIN_EMAIL` and `AUTH_ADMIN_PASSWORD` in `.env`.

## License

This project is licensed under the MIT license. See the license reference in [LICENSE](./LICENSE).
