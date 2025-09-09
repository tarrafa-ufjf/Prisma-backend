from database import db, Database
import pandas as pd
from src.analysis.analysis import Analyzer
from sqlalchemy import and_, create_engine, MetaData, Table, Column, Integer, String
import pika
import json
import os

conn = Database()
analyzer = Analyzer()
connector = None

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

def get_connector():
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_DATABASE")

    engine = create_engine(
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return engine
    

def get_global_analysis_table():
    metadata = MetaData()
    global_analysis = Table(
        'gl_indicators_status', metadata,
        Column('s_user', Integer, primary_key=True),
        Column('indicator', Integer, primary_key=True),
        Column('status', String(1), nullable=False)
    )
    return global_analysis

def update_global_analysis_status(s_user: int, indicator: int, status: str):
    engine = get_connector()
    global_analysis = get_global_analysis_table()

    with engine.connect() as conn:
        insert_stmt = global_analysis.update().values(
            s_user=s_user,
            indicator=indicator,
            status=status
        )
        conn.execute(insert_stmt)
        conn.commit()

def create_rabbit_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,  # mantém a conexão viva
            blocked_connection_timeout=300
        )
    )
    channel = connection.channel()
    return channel

def publish_message(queue_name, task, priority=None):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        )
    )
    channel = connection.channel()
    if priority is None:
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(task), properties=pika.BasicProperties(delivery_mode=2))
    else:
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(task), properties=pika.BasicProperties(priority=priority, delivery_mode=2))
    connection.close()

def performance(body):
    analysis_config = body.get("analysis_config")
    res = analyzer.performance_analysis(analysis_config["id"], analysis_config["type"], version, connector)
    return res.to_dict(orient="records")

def engagement(body):
    analysis_config = body.get("analysis_config")
    res = analyzer.engagement_analysis(analysis_config["id"], analysis_config["type"], version, connector)
    return res.to_dict(orient="records")

def analysis(message):
    global connector, analyzer
    
    connector = conn.get_connection_with_config(message["db_config"])

    version = message["version"]

    analyzer.general_query(connector, version)

    return analyzer.global_engagement


#Função que retorna o valor da versão do Moodle
def get_version(message):
    global connector, version, analyzer

    config = message["db_inst_config"]
    print(f'config := {config}')
    
    connector = conn.get_connection_with_config(config)

    version = analyzer.get_moodle_version(connector)

    return version

def global_analysis_engagement(message):
    global connector, version, analyzer

    body = message["body"]

    if connector is None:
        config = body["db_config"]
        connector = conn.get_connection_with_config(config)
    if version is None:
        version = body["version"]

    res = analyzer.general_engagement_analysis(connector, version, body["analysis_config"])
    if res["processed"] != res["total"]:
        publish_message("tasks_to_process", {
            "name": "user:global_analysis_engagement",
            "version": message["version"],
            "body": {
                "type": "global_analysis_engagement",
                "db_config": body["db_config"],
                "analysis_config": res
            }
        }, priority=0)
    else:
        update_global_analysis_status(1, 1, 'D')

def continuously_listen():
    global channel

    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        analysis_type = message.get("body").get("type")

        # print(f"[x] Mensagem recebida para análise: {message}")

        if analysis_type == "engagement":
            response = engagement(message.get("body"))
            done_message = {
                "name" : message.get("name"),
                "body" : {
                    "version" : message.get("version"),
                    "results" : response,
                }
            }
            publish_message("Done", done_message)
        elif analysis_type == "performance":
            response = performance(message.get("body"))
            done_message = {
                "name" : message.get("name"),
                "body" : {
                    "version" : message.get("version"),
                    "results" : response,
                }
            }
            publish_message("Done", done_message)
        elif analysis_type == "global_analysis_engagement":
            global_analysis_engagement(message)
        elif analysis_type == "version":
            version = get_version(message.get("body"))
            channel.basic_publish(
                exchange="",
                routing_key="Done",
                body=json.dumps({
                    "name": "user:get_version",
                    "body": {
                        "version": version
                    }
                })
            )
        else:
            print(f"[!] Tipo de análise desconhecido: {analysis_type}")

        ch.basic_ack(delivery_tag=method.delivery_tag)
        # print("[x] Análise concluída e mensagem removida da fila.")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='tasks_to_process', on_message_callback=callback)

    print(' [*] Aguardando mensagens. Para sair pressione CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    print("Worker iniciado. Aguardando mensagens...")
    channel = create_rabbit_connection()
    continuously_listen()
