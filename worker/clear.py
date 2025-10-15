import os
import pika
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Carregar variáveis do arquivo .env
load_dotenv()

# Ler variáveis de ambiente
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_DATABASE")

RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

# Criar engine de conexão com o banco
engine = create_engine(
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

metadata = MetaData()
metadata.reflect(bind=engine)

def limpar_tabelas():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for tabela in reversed(metadata.sorted_tables):
                print(f"Limpando tabela: {tabela.name}")
                conn.execute(tabela.delete())
            trans.commit()
            print("Todas as tabelas foram limpas com sucesso!")
        except SQLAlchemyError as e:
            trans.rollback()
            print("Erro ao limpar tabelas:", e)

def limpar_filas():
    # Criar credenciais e conexão com o RabbitMQ
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    )
    channel = connection.channel()

    filas = ["tasks_to_process", "Done"]

    for fila in filas:
        try:
            channel.queue_purge(queue=fila)
            print(f"Fila '{fila}' limpa com sucesso!")
        except Exception as e:
            print(f"Erro ao limpar fila '{fila}': {e}")

    channel.close()
    connection.close()

if __name__ == "__main__":
    limpar_tabelas()
    limpar_filas()
