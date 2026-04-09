# Log de Mudancas do Projeto

Este arquivo registra alteracoes relevantes feitas no codigo do projeto, com data e descricao do que mudou.

## 2026-04-09

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
