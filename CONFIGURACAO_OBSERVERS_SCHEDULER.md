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

A conexao com o banco Moodle deve ser cadastrada antes por um usuario administrador em `PUT /admin/moodle-config`. O endpoint testa a conexao, detecta a versao do Moodle e salva a configuracao no PostgreSQL local. O endpoint `GET /admin/moodle-config` retorna a configuracao sem expor a senha, e `POST /admin/moodle-config/test` testa uma configuracao sem salvar.

A rota `PUT /analysis` usa sempre a configuracao Moodle salva no banco e aceita apenas opcoes operacionais no corpo da requisicao, como o campo opcional `channel`.

Exemplo:

```json
{
  "channel": "diario"
}
```

Se `channel` nao for informado, o valor padrao sera `diario`.

## Como configurar quais indicadores rodam em cada canal

O cadastro fica em `worker/indicator_channels.yml`.

Cada ator contem seus canais, e cada canal contem a lista de indicadores que devem rodar. A estrutura sempre segue este formato:

```yaml
ator:
  canal:
    - indicador
```

Os niveis significam:

- primeiro nivel: ator da analise, como `student` ou `tutor`;
- segundo nivel: canal, como `diario`, `semanal`, `mensal`, `completo` ou outro nome textual criado para o projeto;
- lista do canal: nomes dos indicadores cadastrados no worker.

Campos aceitos no primeiro nivel:

- `student`: executa observers de estudantes;
- `tutor`: executa observers de tutores.

Indicadores aceitos para `student`:

- `engagement`
- `performance`
- `motivation`
- `cognitive`
- `pedagogic`
- `give_up`

Indicadores aceitos para `tutor`:

- `response_forums`
- `feedback`
- `login`

Campos aceitos no segundo nivel:

- `diario`: canal padrao das execucoes diarias;
- `semanal`: canal usado para execucoes semanais, se configurado;
- `mensal`: canal usado para execucoes mensais, se configurado;
- `completo`: canal usado para executar o conjunto completo de indicadores configurado;
- qualquer outro nome textual, como `quinzenal` ou `diagnostico`, desde que o mesmo nome seja usado no disparo manual ou no scheduler.

Regras importantes:

- o nome do ator precisa existir como chave no YAML;
- cada canal precisa apontar para uma lista, mesmo que tenha apenas um indicador;
- o nome do indicador precisa existir em `INDICATOR_OBSERVERS`, em `worker/indicator_publisher.py`;
- se um canal nao estiver cadastrado para um ator, aquele ator nao executara indicadores naquele canal;
- repetir o mesmo indicador no mesmo canal fara o observer ser registrado mais de uma vez, entao evite duplicatas.

Exemplo atual, com canais diarios e completos:

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

Exemplo para adicionar desempenho de estudantes ao canal semanal:

```yaml
student:
  semanal:
    - engagement
    - performance
```

Depois dessa alteracao, toda tarefa de disciplina com `channel="semanal"` passara a executar tambem o observer associado ao indicador `performance`.

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

Depois de criar o observer, adicione-o ao dicionario `INDICATOR_OBSERVERS` em `worker/indicator_publisher.py` e cadastre o nome do indicador em `worker/indicator_channels.yml`, no ator e canal desejados.

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

Os jobs ficam em `pre_api/scheduler_jobs.yml`. Tambem e possivel apontar para outro arquivo pela variavel:

```bash
SCHEDULER_CONFIG_PATH=/caminho/para/scheduler_jobs.yml
```

O arquivo sempre precisa ter a chave `jobs`, que aponta para uma lista de agendamentos:

```yaml
jobs:
  - id: daily_analysis
    channel: diario
    hour: 0
    minute: 30
```

Cada item da lista representa um job do APScheduler. O projeto usa `trigger: cron` por padrao, entao os campos de calendario seguem a sintaxe de cron do APScheduler.

Campos obrigatorios:

- `id`: identificador unico do job, como `daily_analysis`; precisa ser texto e nao pode repetir outro job;
- `channel`: canal que sera enviado para `run_scheduled_analysis(channel=...)`, como `diario`, `semanal`, `mensal`, `completo` ou um canal novo criado no projeto.

Campos de horario e recorrencia mais usados:

- `hour`: hora do dia, de `0` a `23`;
- `minute`: minuto da hora, de `0` a `59`;
- `second`: segundo do minuto, de `0` a `59`;
- `day_of_week`: dia da semana, como `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`;
- `day`: dia do mes, de `1` a `31`;
- `month`: mes, de `1` a `12`, ou nomes como `jan`, `feb`, `mar`;
- `year`: ano especifico;
- `week`: semana ISO do ano;
- `start_date`: data/hora minima para o job comecar a valer;
- `end_date`: data/hora maxima para o job continuar valendo;
- `timezone`: timezone especifico do job, se precisar sobrescrever o timezone geral.

Formatos aceitos nos campos de cron:

- numero simples: `hour: 8` roda as 08h;
- texto com lista: `day: "1,15"` roda nos dias 1 e 15;
- intervalo: `hour: "8-18"` permite horas de 8 ate 18;
- passo: `minute: "*/15"` roda a cada 15 minutos;
- combinacao com dias da semana: `day_of_week: "mon-fri"` roda de segunda a sexta;
- asterisco: `hour: "*"` aceita qualquer hora.

Opcoes operacionais do job:

- `trigger`: por padrao e `cron`; normalmente nao precisa ser informado;
- `max_instances`: por padrao e `1`, evitando duas execucoes simultaneas do mesmo job;
- `coalesce`: por padrao e `true`; se o scheduler perder horarios enquanto estiver parado, junta execucoes pendentes em uma unica execucao;
- `replace_existing`: por padrao e `true`; se um job com o mesmo `id` ja existir no scheduler, ele sera substituido.

Campos proibidos:

- `func`
- `args`
- `kwargs`

Esses campos sao bloqueados porque o scheduler sempre chama internamente `run_scheduled_analysis(...)` e monta o `channel` com seguranca pelo proprio codigo.

Exemplo de job diario:

```yaml
jobs:
  - id: daily_analysis
    channel: diario
    hour: 8
    minute: 0
```

Exemplo de job semanal, toda segunda-feira as 07h30:

```yaml
jobs:
  - id: weekly_analysis
    channel: semanal
    day_of_week: mon
    hour: 7
    minute: 30
```

Exemplo de job mensal, no primeiro dia do mes as 06h:

```yaml
jobs:
  - id: monthly_analysis
    channel: mensal
    day: 1
    hour: 6
    minute: 0
```

Exemplo de job a cada 15 minutos:

```yaml
jobs:
  - id: frequent_analysis
    channel: diario
    minute: "*/15"
```

Por padrao, todos os jobs usam `trigger: cron`, `max_instances: 1`, `coalesce: true` e `replace_existing: true`. Esses campos nao precisam ser repetidos no YAML, mas ainda podem ser informados em um job especifico caso seja necessario sobrescrever o padrao.

## Como adicionar um novo canal agendado

Para criar um canal novo, siga esta ordem:

1. Cadastre os observers do canal em `worker/indicator_publisher.py`.
2. Garanta que `pre_api/processor.py` sabe escolher as disciplinas para esse canal. Se nenhuma regra especifica for adicionada, ele usara `get_all_subjects(...)`.
3. Adicione um novo item em `pre_api/scheduler_jobs.yml`, informando o novo `channel`.

Exemplo:

```yaml
jobs:
  - id: biweekly_analysis
    channel: quinzenal
    day: "1,15"
    hour: 7
    minute: 30
```

## Configuracao usada pelo scheduler

O scheduler busca a configuracao do banco Moodle na tabela `configs`, a mesma mantida por `PUT /admin/moodle-config`.

Variaveis de ambiente relacionadas ao scheduler:

- `SCHEDULER_TIMEZONE` opcional
- `SCHEDULER_CONFIG_PATH` opcional

Se nao houver configuracao Moodle salva, `run_scheduled_analysis(...)` registra a falha no terminal e nao enfileira a analise.

## Como executar

Em um terminal, execute o worker:

```bash
cd worker
uv run python app.py
```

Em outro terminal, execute a API:

```bash
cd pre_api
uv run python app.py
```

Para ativar os agendamentos automaticos, execute tambem:

```bash
cd pre_api
uv run python scheduler.py
```

O scheduler e um processo separado da API Flask. Se ele nao estiver rodando, a rota manual `/analysis` continua funcionando, mas os disparos automaticos nao acontecem.
