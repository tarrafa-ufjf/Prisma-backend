# Instalação

primeiramente rode o comando para inicializar os bancos e serviços com o docker

```bash
docker compose up -d
```

Após isso, Entre no diretório **worker** e rode os comando:

```bash
poetry install
```

```bash
poetry run python install.py
```

**Observação:** Pretendemos, futuramente, simplificar todos os processos utilizando um arquivo bash.

# Modelo das Tasks

Nesta seção, é mostrada como as tasks são feitas para realizar a comunicação entre todos os sistemas.

*Tasks* possuem uma determinada prioridade que pode ser **Alta** ou **Baixa** dependendo do tipo da tarefa. Um exemplo de tarefa de prioridade alta é a tarefa inicial de verificar a versão utilizada pelo sistema. Nesta tarefa, a API envia uma requisição para a fila de tarefas do **RabbitMQ** na fila de tarefas a iniciar. O Worker, que fica verificando a todo momento se há tarefas na fila "Idle" irá verificar que há uma tarefa de prioridade alta na fila e irá executar seguindo o seguinte fluxo:

1. Irá colocar a tarefa na fila Processing;
2. Iniciará a execução da tarefa;
3. Quando a tarefa terminar, adicionar uma mensagem na fila **Done** para a API consumir.

