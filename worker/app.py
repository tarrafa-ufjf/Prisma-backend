from worker.database import db, Database
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

# TODO
def engagement(analysis_config):
    res = analyzer.engagement_analysis(analysis_config["id"], analysis_config["type"], version, connector)

    return jsonify(res.to_dict(orient="records")), 200

# TODO
def analysis():
    global connector, version
    port = request.args.get('port', type=int)
    config = {
            'host':     request.args['host'],
            'port':     port,
            'db':       request.args['database'],
            'user':     request.args['user'],
            'password': request.args['password'],
        }
    connector = conn.get_connection_with_config(config)

    version = analyzer.get_moodle_version(connector)

    analyzer.general_query(connector, version)

    return send_from_directory('src/pages', 'analysis.html'), 200

if __name__ == '__main__':
    print("Worker iniciado. Aguardando mensagens...")
    channel = create_rabbit_connection()
