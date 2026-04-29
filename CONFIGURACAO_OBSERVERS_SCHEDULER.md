# Configuracao de observers, canais e scheduler

Este documento explica como configurar o sistema de observers de indicadores, os canais de execucao e o agendamento automatico das analises.

## Visao geral do fluxo

O fluxo atual tem tres pontos principais:

1. A `pre_api` recebe uma requisicao ou um disparo agendado e chama `Processor.set_subjects_analysis(...)`.
2. O `Processor` escolhe quais disciplinas entram na fila conforme o `channel` informado e publica tarefas no RabbitMQ.
3. O `worker` consome cada tarefa, le o `channel` da mensagem e usa o `IndicatorPublisher` para executar apenas os observers cadastrados para aquele ator e canal.

Arquivos principais:

- `pre_api/app.py`: entrada HTTP `/analysis` e funcao `run_scheduled_analysis(...)`.
- `pre_api/processor.py`: selecao de disciplinas e publicacao das tarefas.
- `pre_api/scheduler.py`: agendamentos automaticos por cron.
- `worker/app.py`: consumo das tarefas e persistencia dos resultados.
- `worker/indicator_publisher.py`: contrato dos observers, publisher e cadastro dos indicadores por canal.

## Canais disponiveis

Os canais sao nomes textuais usados para definir que conjunto de indicadores deve rodar.

Atualmente existem os seguintes canais cadastrados no publisher:

- `diario`
- `semanal`
- `mensal`
- `completo`

O canal tambem influencia a selecao de disciplinas na `pre_api`:

- `diario`: usa `Analyzer.get_daily_active_subjects(...)`;
- `semanal`: usa `Analyzer.get_week_active_subjects(...)`;
- `mensal`: usa `Analyzer.get_month_active_subjects(...)`;
- qualquer outro valor: usa `Analyzer.get_all_subjects(...)`.

## Como disparar uma analise manual por canal

A rota `PUT /analysis` aceita as configuracoes do banco Moodle no corpo da requisicao e tambem aceita o campo opcional `channel`.

Exemplo:

```json
{
  "host": "localhost",
  "port": 3306,
  "user": "usuario",
  "password": "senha",
  "database": "moodle",
  "channel": "diario"
}
```

Se `channel` nao for informado, o valor padrao sera `diario`.

## Como configurar quais indicadores rodam em cada canal

O cadastro fica em `worker/indicator_publisher.py`, na funcao `register_default_indicators(...)`.

Cada inscricao segue o formato:

```python
publisher.subscribe("student", "diario", StudentEngagementObserver(analyzer))
```

Os parametros significam:

- primeiro argumento: ator da analise, como `student` ou `tutor`;
- segundo argumento: canal, como `diario`, `semanal`, `mensal` ou `completo`;
- terceiro argumento: observer que calcula um indicador.

Exemplo para adicionar desempenho de estudantes ao canal semanal:

```python
publisher.subscribe("student", "semanal", StudentPerformanceObserver(analyzer))
```

Depois dessa alteracao, toda tarefa de disciplina com `channel="semanal"` passara a executar tambem o observer `StudentPerformanceObserver`.

## Como criar um novo observer

Todos os observers devem herdar de `BaseIndicatorObserver` e implementar o metodo `calculate(...)`.

Modelo:

```python
class StudentExampleObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("example")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.example_analysis(subject_id, "subject", version, connector)
```

O nome passado para `super().__init__(...)` identifica o resultado no publisher. Esse nome tambem e usado pelo `worker` para buscar o DataFrame retornado e registrar status granular por indicador.

Depois de criar o observer, cadastre-o em `register_default_indicators(...)` no ator e canal desejados:

```python
publisher.subscribe("student", "completo", StudentExampleObserver(analyzer))
```

Para observers de tutores, o `worker` envia contexto extra no `notify(...)`, como:

- `start_at`
- `end_at`
- `tutor_ids`

Esses valores podem ser lidos no observer por `context.get("start_at")`, `context.get("end_at")` e `context.get("tutor_ids")`.

## Como configurar o scheduler

O scheduler fica em `pre_api/scheduler.py` e usa APScheduler com `BackgroundScheduler`.

O timezone padrao e `America/Sao_Paulo`, mas pode ser alterado pela variavel de ambiente:

```bash
SCHEDULER_TIMEZONE=America/Sao_Paulo
```

Jobs atuais:

- `daily_analysis`: roda `run_scheduled_analysis(channel="diario")` todos os dias em um determinado horario;
- `weekly_analysis`: roda `run_scheduled_analysis(channel="semanal")` um dia na semana  em um determinado horairo;
- `monthly_analysis`: roda `run_scheduled_analysis(channel="mensal")` um dia no mes em um determinado horario.

Para alterar horario ou recorrencia, edite os parametros do `scheduler.add_job(...)`.

Exemplo:

```python
scheduler.add_job(
    run_scheduled_analysis,
    kwargs={"channel": "diario"},
    trigger="cron",
    hour=8,
    minute=0,
    id="daily_analysis",
    max_instances=1,
    coalesce=True,
    replace_existing=True,
)
```

Campos mais importantes:

- `kwargs={"channel": "diario"}` define qual canal sera enfileirado;
- `trigger="cron"` indica agendamento por calendario;
- `hour` e `minute` definem o horario;
- `day_of_week="mon"` restringe para segunda-feira;
- `day=1` restringe para o primeiro dia do mes;
- `max_instances=1` evita execucoes concorrentes do mesmo job;
- `coalesce=True` junta execucoes perdidas em uma unica execucao;
- `replace_existing=True` permite recriar o job com o mesmo `id`.

## Como adicionar um novo canal agendado

Para criar um canal novo, siga esta ordem:

1. Cadastre os observers do canal em `worker/indicator_publisher.py`.
2. Garanta que `pre_api/processor.py` sabe escolher as disciplinas para esse canal. Se nenhuma regra especifica for adicionada, ele usara `get_all_subjects(...)`.
3. Adicione um novo `scheduler.add_job(...)` em `pre_api/scheduler.py`, chamando `run_scheduled_analysis` com o novo `channel`.

Exemplo:

```python
scheduler.add_job(
    run_scheduled_analysis,
    kwargs={"channel": "quinzenal"},
    trigger="cron",
    day="1,15",
    hour=7,
    minute=30,
    id="biweekly_analysis",
    max_instances=1,
    coalesce=True,
    replace_existing=True,
)
```

## Variaveis de ambiente usadas pelo scheduler

O scheduler monta a configuracao do banco Moodle a partir do `.env` usando `pre_api/app.py`.

Variaveis necessarias:

- `MYSQL_HOST`
- `MYSQL_GRAD_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `SCHEDULER_TIMEZONE` opcional

Se alguma variavel obrigatoria estiver ausente, `run_scheduled_analysis(...)` registra a falha no terminal e nao enfileira a analise.

## Como executar

Em um terminal, execute o worker:

```bash
cd worker
poetry run python app.py
```

Em outro terminal, execute a API:

```bash
cd pre_api
poetry run python app.py
```

Para ativar os agendamentos automaticos, execute tambem:

```bash
cd pre_api
poetry run python scheduler.py
```

O scheduler e um processo separado da API Flask. Se ele nao estiver rodando, a rota manual `/analysis` continua funcionando, mas os disparos automaticos nao acontecem.