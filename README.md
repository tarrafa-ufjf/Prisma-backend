# Instalação

primeiramente, rode o comando para inicializar os bancos e serviços com o docker

```bash
docker compose up -d
```

Se o comando acima não funcionar, tente:

```bash
docker-compose up -d
```

Após todos os containers estarem executando, entre no diretório **worker** e rode os comando:

```bash
poetry install
```

```bash
poetry run python install.py
```

Feito isso, entre no diretório da **API** e rode o comando:

```bash
poetry install
```

# Como executar o sistema

Feita a instalação mostrada no passo anterior, para rodar o sistema será necessário abrir 2 terminais: um para o diretório da **API** e outro para o diretório **worker**. Em ambos os terminais, rode o comando a seguir:

```bash
poetry run python app.py
```

Feito isso, no terminal da **API**, acesse o link disponibilizado pelo Flask. Irá abrir uma página no navegador onde o usuário irá inserir as informações de acesso ao banco de dados institucional, como o link do host, a porta, o usuário, etc. Após inserir os dados, o sistema irá iniciar a análise global enquanto o usuário pode fazer as análises locais.

# Modelo de troca de mensagens

Nesta seção, é mostrada como as tasks são feitas para realizar a comunicação entre todos os sistemas.

*Tasks* possuem uma determinada prioridade que varia entre 0 e 2 dependendo do tipo da tarefa. Exemplos de tarefas de nível 2 são as tarefas solicitadas pelo usuário, de nível 0 e 1, as tarefas inseridas pelo Worker. Uma tarefa a ser feita sempre é inserida na fila **tasks_to_process**. O Worker, que fica verificando a todo momento se há tarefas na fila **tasks_to_process**, irá pegar a tarefa na primeira posição da fila e executá-la. Se a tarefa for grande, como nos casos das análises globais, o Worker irá dividi-las em sub-tarefas seguindo um valor fixo. Um exemplo seria o seguinte:

Há uma tarefa de análise global de um indicador global a ser feita, e, nessa tarefa, há cerca de 2000 análises a serem realizadas. O que o worker irá fazer é, com base em um parâmetro inteiro de valor **x** presente na tarefa, rodar a análise **x** vezes e reintroduzir a tarefa com o valor de onde parou no processamento na fila novamente com uma prioridade pequena. Isso é feito para permitir com que o usuário realize análises mais simples enquanto a análise global é realizada.

De modo mais simplificado, o modelo geral é o seguinte:

1. Irá colocar a tarefa na fila Processing;
2. Iniciará a execução da tarefa;
3. Quando a tarefa terminar, adicionar uma mensagem na fila **Done** para a API consumir.

A fila **Done** é responsável por armazenar e enviar as tarefas que foram finalizadas pelo Worker para a API consumir quando considerar apropriado. As tarefas podem indicar que uma determinada análise obteve sucesso ao inserir os resultados no banco de dados local ou conter informações brutas no formato JSON para a API consumir diretamente. O último caso está relacionado com as análises locais, que são mais simples de serem feitas.


# Modelo das tasks

As mensagens das tarefas foram padronizadas para que o seu consumo e leitura sejam facilitados em todas as camadas do sistema. O modelo de mensagem escolhido para a fila **tasks_to_process** foi o seguinte:

```javascript
{
    "name" : name,
    "version" : version,
    "body" : {
        "db_inst_config" : db_config,
        "analysis_config" : {
            "type" : request.args.get('performance-query'),
            "id" : subject_id
        },
        "type" : "performance",
    }
}
```

O campo "nome" informa o nome da tarefa que, por enquanto, é padronizada como sendo:

``` javascript
"id_instituicao:tipo_tarefa"
```

O campo "version" informa a versão do moodle utilizada. **Observação:** Esse campo poderá ser tirado em versões posteriores do sistema.

O campo "body" contém o corpo da mensagem, ele é composto por: 

1. Configurações de acesso ao banco de dados institucional;
2. Configurações de análise do indicador;
3. O indicador relacionado.

Para a fila **Done**, foi escolhido o seguinte padrão:

``` javascript
{
    "name" : name,
    "body" : {
        "version" : version,
        "results" : response,
    }
}
```

O campo "name" informa o nome da tarefa finalizada e o campo "body" traz informações sobre os resultados da execução da tarefa.