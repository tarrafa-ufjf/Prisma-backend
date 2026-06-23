# Observer, Channel, and Scheduler Configuration

This document explains how to configure the indicator observer system, execution channels, and automatic analysis scheduling.

## Flow Overview

The current flow has three main points:

1. `pre_api` receives a request or scheduled trigger and calls `Processor.set_subjects_analysis(...)`.
2. `Processor` chooses which subjects enter the queue according to the provided `channel` and publishes tasks to RabbitMQ.
3. `worker` consumes each task, reads the message `channel`, and uses `IndicatorPublisher` to execute only the observers registered for that actor and channel.

Main files:

- `pre_api/app.py`: HTTP `/analysis` entry point and `run_scheduled_analysis(...)` function.
- `pre_api/processor.py`: subject selection and task publishing.
- `pre_api/scheduler.py`: automatic cron schedules.
- `worker/app.py`: task consumption and result persistence.
- `worker/indicator_publisher.py`: observer contract, publisher, and indicator registration by channel.

## Available Channels

Channels are text names used to define which set of indicators should run.

The following channels are currently registered in the publisher:

- `diario`
- `semanal`
- `mensal`
- `completo`

The channel also affects subject selection in `pre_api`:

- `diario`: uses `Analyzer.get_daily_active_subjects(...)`;
- `semanal`: uses `Analyzer.get_week_active_subjects(...)`;
- `mensal`: uses `Analyzer.get_month_active_subjects(...)`;
- any other value: uses `Analyzer.get_all_subjects(...)`.

## Triggering a Manual Analysis by Channel

The Moodle database connection must first be registered by an administrator through `PUT /admin/moodle-config`. The endpoint tests the connection, detects the Moodle version, and saves the configuration in the local PostgreSQL database. The `GET /admin/moodle-config` endpoint returns the configuration without exposing the password, and `POST /admin/moodle-config/test` tests a configuration without saving it.

The `PUT /analysis` route always uses the saved Moodle configuration and accepts only operational options in the request body, such as the optional `channel` field.

Example:

```json
{
  "channel": "diario"
}
```

If `channel` is not provided, the default value is `diario`.

## Configuring Which Indicators Run in Each Channel

The registry lives in `worker/indicator_channels.yml`.

Each actor contains its channels, and each channel contains the list of indicators that should run. The structure always follows this format:

```yaml
actor:
  channel:
    - indicator
```

The levels mean:

- first level: analysis actor, such as `student` or `tutor`;
- second level: channel, such as `diario`, `semanal`, `mensal`, `completo`, or another text name created for the project;
- channel list: names of indicators registered in the worker.

Accepted first-level fields:

- `student`: runs student observers;
- `tutor`: runs tutor observers.

Accepted indicators for `student`:

- `engagement`
- `performance`
- `motivation`
- `cognitive`
- `pedagogic`
- `give_up`

Accepted indicators for `tutor`:

- `response_forums`
- `feedback`
- `login`

Accepted second-level fields:

- `diario`: default daily execution channel;
- `semanal`: channel used for weekly executions, if configured;
- `mensal`: channel used for monthly executions, if configured;
- `completo`: channel used to execute the full configured indicator set;
- any other text name, such as `quinzenal` or `diagnostico`, as long as the same name is used in the manual trigger or scheduler.

Important rules:

- the actor name must exist as a YAML key;
- each channel must point to a list, even if it has only one indicator;
- the indicator name must exist in `INDICATOR_OBSERVERS`, in `worker/indicator_publisher.py`;
- if a channel is not registered for an actor, that actor will not execute indicators in that channel;
- repeating the same indicator in the same channel registers the observer more than once, so avoid duplicates.

Current example, with daily and full channels:

```yaml
student:
  diario:
    - engagement
    - performance
    - motivation
    - cognitive
    - pedagogic
    - give_up
  completo:
    - engagement
    - performance
    - motivation
    - cognitive
    - pedagogic
    - give_up

tutor:
  diario:
    - response_forums
    - feedback
    - login
  completo:
    - response_forums
    - feedback
    - login
```

Example for adding student performance to the weekly channel:

```yaml
student:
  semanal:
    - engagement
    - performance
```

After this change, every subject task with `channel="semanal"` will also execute the observer associated with the `performance` indicator.

## Creating a New Observer

All observers must inherit from `BaseIndicatorObserver` and implement the `calculate(...)` method.

Template:

```python
class StudentExampleObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("example")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.example_analysis(subject_id, "subject", version, connector)
```

The name passed to `super().__init__(...)` identifies the result in the publisher. This name is also used by the `worker` to find the returned DataFrame and register granular status by indicator.

After creating the observer, add it to the `INDICATOR_OBSERVERS` dictionary in `worker/indicator_publisher.py` and register the indicator name in `worker/indicator_channels.yml`, under the desired actor and channel.

For tutor observers, the `worker` sends extra context in `notify(...)`, such as:

- `start_at`
- `end_at`
- `tutor_ids`

These values can be read in the observer with `context.get("start_at")`, `context.get("end_at")`, and `context.get("tutor_ids")`.

## Configuring the Scheduler

The scheduler lives in `pre_api/scheduler.py` and uses APScheduler with `BackgroundScheduler`.

The default timezone is `America/Sao_Paulo`, but it can be changed with the environment variable:

```bash
SCHEDULER_TIMEZONE=America/Sao_Paulo
```

Jobs live in `pre_api/scheduler_jobs.yml`. You can also point to another file with the variable:

```bash
SCHEDULER_CONFIG_PATH=/path/to/scheduler_jobs.yml
```

The file must always have a `jobs` key pointing to a schedule list:

```yaml
jobs:
  - id: daily_analysis
    channel: diario
    hour: 0
    minute: 30
```

Each list item represents an APScheduler job. The project uses `trigger: cron` by default, so calendar fields follow APScheduler cron syntax.

Required fields:

- `id`: unique job identifier, such as `daily_analysis`; it must be text and must not repeat another job;
- `channel`: channel sent to `run_scheduled_analysis(channel=...)`, such as `diario`, `semanal`, `mensal`, `completo`, or a new channel created in the project.

Most common time and recurrence fields:

- `hour`: hour of the day, from `0` to `23`;
- `minute`: minute of the hour, from `0` to `59`;
- `second`: second of the minute, from `0` to `59`;
- `day_of_week`: weekday, such as `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`;
- `day`: day of the month, from `1` to `31`;
- `month`: month, from `1` to `12`, or names such as `jan`, `feb`, `mar`;
- `year`: specific year;
- `week`: ISO week of the year;
- `start_date`: minimum date/time for the job to start applying;
- `end_date`: maximum date/time for the job to keep applying;
- `timezone`: job-specific timezone, if it needs to override the general timezone.

Accepted cron field formats:

- simple number: `hour: 8` runs at 08:00;
- text with list: `day: "1,15"` runs on days 1 and 15;
- range: `hour: "8-18"` allows hours from 8 through 18;
- step: `minute: "*/15"` runs every 15 minutes;
- weekday combination: `day_of_week: "mon-fri"` runs Monday through Friday;
- asterisk: `hour: "*"` accepts any hour.

Operational job options:

- `trigger`: defaults to `cron`; normally does not need to be provided;
- `max_instances`: defaults to `1`, preventing two simultaneous executions of the same job;
- `coalesce`: defaults to `true`; if the scheduler misses times while stopped, pending executions are merged into one execution;
- `replace_existing`: defaults to `true`; if a job with the same `id` already exists in the scheduler, it will be replaced.

Forbidden fields:

- `func`
- `args`
- `kwargs`

These fields are blocked because the scheduler always calls `run_scheduled_analysis(...)` internally and safely builds the `channel` in code.

Daily job example:

```yaml
jobs:
  - id: daily_analysis
    channel: diario
    hour: 8
    minute: 0
```

Weekly job example, every Monday at 07:30:

```yaml
jobs:
  - id: weekly_analysis
    channel: semanal
    day_of_week: mon
    hour: 7
    minute: 30
```

Monthly job example, on the first day of the month at 06:00:

```yaml
jobs:
  - id: monthly_analysis
    channel: mensal
    day: 1
    hour: 6
    minute: 0
```

Job every 15 minutes example:

```yaml
jobs:
  - id: frequent_analysis
    channel: diario
    minute: "*/15"
```

By default, all jobs use `trigger: cron`, `max_instances: 1`, `coalesce: true`, and `replace_existing: true`. These fields do not need to be repeated in YAML, but they can still be provided for a specific job if the default needs to be overridden.

## Adding a New Scheduled Channel

To create a new channel, follow this order:

1. Register the channel observers in `worker/indicator_publisher.py`.
2. Make sure `pre_api/processor.py` knows how to choose subjects for this channel. If no specific rule is added, it will use `get_all_subjects(...)`.
3. Add a new item in `pre_api/scheduler_jobs.yml`, providing the new `channel`.

Example:

```yaml
jobs:
  - id: biweekly_analysis
    channel: quinzenal
    day: "1,15"
    hour: 7
    minute: 30
```

## Configuration Used by the Scheduler

The scheduler reads the Moodle database configuration from the `configs` table, the same one maintained by `PUT /admin/moodle-config`.

Scheduler-related environment variables:

- `SCHEDULER_TIMEZONE` optional
- `SCHEDULER_CONFIG_PATH` optional

If there is no saved Moodle configuration, `run_scheduled_analysis(...)` logs the failure in the terminal and does not enqueue the analysis.

## How to Run

In one terminal, run the worker:

```bash
cd worker
uv run python app.py
```

In another terminal, run the API:

```bash
cd pre_api
uv run python app.py
```

To activate automatic schedules, also run:

```bash
cd pre_api
uv run python scheduler.py
```

The scheduler is a separate process from the Flask API. If it is not running, the manual `/analysis` route continues to work, but automatic triggers do not happen.
