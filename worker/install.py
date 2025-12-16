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

    columns_subjects_status = {
        "institution_id": Integer,
        "subject_id": Integer,
        "status": String(1),   # P=Processing, D=Done, E=Error
    }
    primary_keys = ["institution_id", "subject_id"]
    create_table("subjects_status", columns_subjects_status, primary_key=primary_keys)

    columns_gl_local_students = {
        "institution_id": Integer,
        "version": String(40),
        "subject_id": Integer,
        "student_id": Integer,

        "n_posts_engagement": Integer,
        "label_engagement": String(32),

        "n_posts_motivation": Integer,
        "label_motivation": String(32),

        "grade_performance": Float,
        "grade_comparative_performance": Float,
        "label_performance": String(32),

        "mean_forum_interactions_cognitive": Float,
        "mean_quiz_interactions_cognitive": Float,
        "mean_assign_interactions_cognitive": Float,
        "label_cognitive": String(32),

        "n_responses_relation_teacher_student": Integer,
        "label_relation_teacher_student": String(32),

        "label_give_up": String(32),
    }
    create_table(
        "local_indicators_students",
        columns_gl_local_students,
        primary_key=["institution_id", "version", "subject_id", "student_id"]
    )

    columns_gl_global = {
        "institution_id": Integer,
        "version": String(40),
        "subject_id": Integer,

        "mean_posts_engagement": Float,
        "label_engagement": String(32),

        "mean_posts_motivation": Float,
        "label_motivation": String(32),

        "mean_grade_performance": Float,
        "label_performance": String(32),

        "mean_interactions_cognitive": Float,
        "label_cognitive": String(32),

        "mean_responses_relation_teacher_student": Float,
        "label_relation_teacher_student": String(32),
        
        "mean_give_up": Float,
        "label_give_up": String(32),
    }
    create_table(
        "global_indicators",
        columns_gl_global,
        primary_key=["institution_id", "version", "subject_id"]
    )

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
