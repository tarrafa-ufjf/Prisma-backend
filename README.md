# Instalação

primeiramente rode o comando para inicializar os bancos e serviços com o docker

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

# Modelo das Tasks

Nesta seção, é mostrada como as tasks são feitas para realizar a comunicação entre todos os sistemas.

*Tasks* possuem uma determinada prioridade que pode ser **Alta** ou **Baixa** dependendo do tipo da tarefa. Um exemplo de tarefa de prioridade alta é a tarefa inicial de verificar a versão utilizada pelo sistema. Nesta tarefa, a API envia uma requisição para a fila de tarefas do **RabbitMQ** na fila de tarefas a iniciar. O Worker, que fica verificando a todo momento se há tarefas na fila "Idle" irá verificar que há uma tarefa de prioridade alta na fila e irá executar seguindo o seguinte fluxo:

1. Irá colocar a tarefa na fila Processing;
2. Iniciará a execução da tarefa;
3. Quando a tarefa terminar, adicionar uma mensagem na fila **Done** para a API consumir.

