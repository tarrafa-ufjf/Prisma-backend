import os
import pika
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DECIMAL
from sqlalchemy.exc import SQLAlchemyError

# Carregar variáveis do arquivo .env
load_dotenv()

# Ler variáveis de ambiente
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_DATABASE")

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

# Criar credenciais
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

# Criar conexão
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )
)

channel = connection.channel()

# Criar engine de conexão
engine = create_engine(
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

metadata = MetaData()

def criar_tabela(nome_tabela, colunas):
    try:
        cols = []
        for nome, tipo in colunas.items():
            if nome == "id":
                cols.append(Column(nome, tipo, primary_key=True, autoincrement=True))
            else:
                cols.append(Column(nome, tipo))
        
        tabela = Table(nome_tabela, metadata, *cols)
        metadata.create_all(engine)
        print(f"Tabela '{nome_tabela}' criada com sucesso!")
    except SQLAlchemyError as e:
        print("Erro ao criar tabela:", e)

if __name__ == "__main__":
    colunas_engajamento_global = {
        "id": Integer,
        "course_id": Integer,
        "value": Integer
    }
    criar_tabela("engajamento_global", colunas_engajamento_global)

    channel.queue_declare(
        queue="tasks_to_process",
        durable=True,
        arguments={"x-max-priority": 2}
    )

    channel.queue_declare(
        queue="Done",
        durable=True
    )

    print("Filas de prioridade criadas no RabbitMQ! Pronto para receber tasks!")

    channel.close()
