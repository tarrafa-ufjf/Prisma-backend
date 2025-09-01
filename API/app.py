from flask import request, jsonify, Flask, send_file, send_from_directory
from database import db, Database
import os
import pika
import json, time

app = Flask(__name__)
conn = Database()
connector = None
version = None
db_config = None

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

def get_done_message(name):
    global channel
    found = False
    res = None
    while not found:
        # Pega apenas 1 mensagem da fila (não bloqueia)
        method_frame, _, body = channel.basic_get(queue="Done", auto_ack=False)

        if method_frame:
            message = json.loads(body.decode())
            nome = message.get("name") 

            if nome == name:
                print(f"[x] Mensagem encontrada: {message}")
                # Confirma a retirada da fila
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                found = True
                res = message.get("body")
            else:
                # Recoloca a mensagem no final da fila
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                time.sleep(0.1)
        else:
            time.sleep(0.5)
    return res

@app.route("/engagement", methods=["GET"])
def engagement():
    global db_config, channel, version

    course_id = request.args.get('engagement-id', type=int)
    if not course_id and request.args.get('engagement-query') != 'geral':
        return jsonify({"error": "Course ID is required"}), 400
    
    analysis_config = {
        "type" : request.args.get('engagement-query'),
        "id" : course_id
    }
    
    name = "user:engagement"
    task = {
        "name" : name,
        "db_config" : db_config,
        "a_config" : analysis_config,
        "version" : version,
        "type" : "engagement"
    }
    channel.basic_publish(
        exchange="",
        routing_key="tasks_to_process",
        body=json.dumps(task),
        properties=pika.BasicProperties(
            priority=2,
            delivery_mode=2
        )
    )

    body = get_done_message(name)

    return jsonify(body.to_dict(orient="records")), 200

@app.route("/analysis", methods=["GET"])
def analysis():
    global version, db_config, channel
    port = request.args.get('port', type=int)
    db_config = {
        'host':     request.args['host'],
        'port':     port,
        'db':       request.args['database'],
        'user':     request.args['user'],
        'password': request.args['password'],
    }

    name = "user:get_version"
    task = {
        "name" : name,
        "body" : {
            "db_inst_config" : db_config,
        },
        "type" : "version"
    }
    channel.basic_publish(
        exchange="",
        routing_key="tasks_to_process",
        body=json.dumps(task),
        properties=pika.BasicProperties(
            priority=2,
            delivery_mode=2
        )
    )

    body = get_done_message(name)

    print('------------------------------------------')
    print(f"[x] Versão do Moodle: {body['version']}")
    print('------------------------------------------')

    # task = {
    #     "name" : "user:global_analysis",
    #     "version" : body["version"],
    #     "db_config" : db_config,
    #     "type" : "global_analysis"
    # }

    # channel.basic_publish(
    #     exchange="",
    #     routing_key="tasks_to_process",
    #     body=json.dumps(task),
    #     properties=pika.BasicProperties(
    #         priority=1,
    #         delivery_mode=2
    #     )
    # )

    return send_from_directory('pages', 'analysis.html'), 200


@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True)