import os
import pika
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DECIMAL, PrimaryKeyConstraint
from sqlalchemy.exc import SQLAlchemyError

# Carregar variáveis do arquivo .env
load_dotenv()

# Ler variáveis de ambiente
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
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

print(f'Conectado ao banco de dados PostgreSQL em {DB_HOST}:{DB_PORT}/{DB_NAME}')

metadata = MetaData()

def create_table(table_name, columns, primary_key=None):
    try:
        cols = []
        for nome, tipo in columns.items():
            cols.append(Column(nome, tipo))
        if primary_key:
            cols.append(PrimaryKeyConstraint(*primary_key))
        
        tabela = Table(table_name, metadata, *cols)
        metadata.create_all(engine)
        print(f"Tabela '{table_name}' criada com sucesso!")
    except SQLAlchemyError as e:
        print("Erro ao criar tabela:", e)

if __name__ == "__main__":
    columns_engajamento_global = {
        "institution_id": Integer,
        "subject_id": Integer,
        "user_id": Integer,
        "num_posts_required": Integer,
        "label": String(20),
    }

    primary_keys = ["institution_id", "subject_id", "user_id"]
    create_table("engagement_global", columns_engajamento_global, primary_key=primary_keys)

    columns_indicators_status = {
        "institution_id": Integer,
        "indicator": Integer,
        "status": String(1),
    }

    primary_keys = ["institution_id", "indicator"]
    create_table("gl_indicators_status", columns_indicators_status, primary_key=primary_keys)

    columns_configs = {
        "institution_id": Integer,
        "subject_id": Integer,
        "user_id": Integer,
        "grade": Integer,
        "comparative": Float,
        "situation": String(20),
        "label": String(20),
    }

    primary_keys = ["institution_id", "subject_id", "user_id"]

    create_table("performance_global", columns_configs, primary_key=primary_keys)

    columns_configs = {
        "institution_id": Integer,
        "version": String(40),
        "host": String,
        "port": Integer,
        "database": String,
        "user": String,
        "password": String
    }

    primary_keys = ["institution_id", "version"]

    create_table("configs", columns_configs, primary_key=primary_keys)

    columns_configs = {
        "institution_id": Integer,
        "subject_id": Integer,
        "user_id": Integer,
        "num_posts_unrequired": Integer,
        "label": String(20),
    }

    primary_keys = ["institution_id", "subject_id", "user_id"]
    create_table("motivation_global", columns_configs, primary_key=primary_keys)

    columns_configs = {
        "institution_id": Integer,
        "subject_id": Integer,
        "user_id": Integer,
        "assign_level_avg": Float,
        "forum_level_avg": Float,
        "quiz_level_avg": Float,
    }

    primary_keys = ["institution_id", "subject_id", "user_id"]
    create_table("cognitive_global", columns_configs, primary_key=primary_keys)

    columns_configs = {
        "institution_id": Integer,
        "subject_id": Integer,
        "rapida": Integer,
        "normal": Integer,
        "atrasada": Integer,
        "sem_resposta": Integer,
    }

    primary_keys = ["institution_id", "subject_id"]
    create_table("pedagogico_global", columns_configs, primary_key=primary_keys)

    columns_configs = {
        "institution_id": Integer,
        "subject_id": Integer,
        "user_id": Integer,
        "give_up": String(20),
    }

    primary_keys = ["institution_id", "subject_id", "user_id"]
    create_table("give_up_global", columns_configs, primary_key=primary_keys)

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
