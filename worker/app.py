from database import db, Database
import pandas as pd
from src.analysis.analysis import Analyzer
import pika
import json
import time
import os

conn = Database()
analyzer = Analyzer()
connector = None

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

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

def continuously_listen():
    global channel

    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        analysis_type = message.get("body").get("type")

        print(f"[x] Mensagem recebida para análise: {message}")

        if analysis_type == "engagement":
            response = engagement(message.get("body"))
            done_message = {
                "name" : message.get("name"),
                "body" : {
                    "version" : message.get("version"),
                    "results" : response,
                }
            }

            channel.basic_publish(
                exchange="",
                routing_key="Done",
                body=json.dumps(done_message)
            )
        elif analysis_type == "global_analysis":
            analysis(message)
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
        print("[x] Análise concluída e mensagem removida da fila.")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='tasks_to_process', on_message_callback=callback)

    print(' [*] Aguardando mensagens. Para sair pressione CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    print("Worker iniciado. Aguardando mensagens...")
    channel = create_rabbit_connection()
    continuously_listen()
