from flask import request, jsonify, Flask, send_file, send_from_directory
from sqlalchemy import and_, select, create_engine, MetaData, Table, Column, Integer, String
import os
from dotenv import load_dotenv
import pika
import json, time

app = Flask(__name__)
connector = None
version = None
db_config = None
load_dotenv()

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

# Criar credenciais
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

# Criar conexão
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
    )
)
channel = connection.channel()   

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

def insert_global_analysis_status(s_user: int, indicator: int, status: str):
    engine = get_connector()
    global_analysis = get_global_analysis_table()

    with engine.connect() as conn:
        insert_stmt = global_analysis.insert().values(
            s_user=s_user,
            indicator=indicator,
            status=status
        )
        conn.execute(insert_stmt)
        conn.commit()

def publish_message(queue_name, task, priority=None):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    )
    channel = connection.channel()
    if priority is None:
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(task), properties=pika.BasicProperties(delivery_mode=2))
    else:
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(task), properties=pika.BasicProperties(priority=priority, delivery_mode=2))
    connection.close()


def get_done_message(name):
    global channel
    found = False
    res = None
    while not found:
        # Pega apenas 1 mensagem da fila (não bloqueia)
        time.sleep(0.25)
        method_frame, _, body = channel.basic_get(queue="Done", auto_ack=False)

        if method_frame:
            message = json.loads(body.decode())
            nome = message.get("name") 

            if nome == name:
                # print(f"[x] Mensagem encontrada: {message}")
                # Confirma a retirada da fila
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                found = True
                res = message.get("body")
            else:
                # Recoloca a mensagem no final da fila
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                time.sleep(0.1)
        else:
            time.sleep(0.25)
    return res

def wait_until_done(s_user, indicator, status, poll_interval=2):
    engine = get_connector()
    global_analysis = get_global_analysis_table()

    while True:
        with engine.connect() as conn:
            query = select(global_analysis.c.status).where(
                and_(
                    global_analysis.c.s_user == s_user,
                    global_analysis.c.status == status,
                    global_analysis.c.indicator == indicator
                )
            )
            result = conn.execute(query).fetchone()

            if result and result.status == "D":
                return True

        time.sleep(poll_interval)  # espera antes de checar de novo


def handle_analysis(analysis_type, global_fn, indicator_index=0):
    global db_config, channel, version

    version = get_version_in_database(1)

    course_id = request.args.get("id", type=int)
    type_ = request.args.get("query")

    if not course_id and type_ != "general":
        return jsonify({"error": "Course ID is required"}), 400

    analysis_config = {"type": type_, "id": course_id}


    if type_ != "general":
        name = f"user:{analysis_type}"
        task = {
            "name": name,
            "version": version,
            "body": {
                "db_inst_config": db_config,
                "analysis_config": analysis_config,
                "type": analysis_type,
            },
        }
        publish_message("tasks_to_process", task, priority=2)
        body = get_done_message(name)
        return jsonify(body), 200

    else:
        name = f"user:global_analysis_{analysis_type}"
        wait_until_done(1, indicator_index, "D")
        rows = global_fn()
        data = [dict(row) for row in rows]
        return jsonify(data), 200

@app.route("/pedagogic", methods=["GET"])
def pedagogic():
    return handle_analysis("pedagogic", get_all_from_table, indicator_index=4)

@app.route("/performance", methods=["GET"])
def performance():
    return handle_analysis("performance", get_all_performance_global, indicator_index=2)

@app.route("/motivation", methods=["GET"])
def motivation():
    return handle_analysis("motivation", get_all_motivation_global, indicator_index=3)

@app.route("/engagement", methods=["GET"])
def engagement():
    return handle_analysis("engagement", get_all_engajamento_global, indicator_index=1)

def get_all_from_table(table_name, user_id=1):
    engine = get_connector()
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(table).where(table.c.s_user == user_id)  # TODO
        return conn.execute(query).mappings().all()


def get_all_engajamento_global(user_id=1):
    return get_all_from_table("engajamento_global", user_id)


def get_all_performance_global(user_id=1):
    return get_all_from_table("performance_global", user_id)


def get_all_motivation_global(user_id=1):
    return get_all_from_table("motivation_global", user_id)

def get_all_pedagogic_global(user_id=1):
    return get_all_from_table("pedagogic_global", user_id)

def get_version_in_database(user):
    engine = get_connector()
    metadata = MetaData()
    configs = Table("configs", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(configs).where(configs.c.s_user == user)
        result = conn.execute(query).mappings().all()  # retorna lista de dicts
        if len(result) > 0:
            return result[0]['version']
        else:
            return None

def insert_version_in_database(user, version, db_config):
    engine = get_connector()
    metadata = MetaData()
    configs = Table("configs", metadata, autoload_with=engine)

    with engine.connect() as conn:
        insert_stmt = configs.insert().values(
            s_user=user,
            version=version,
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['db'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.execute(insert_stmt)
        conn.commit()

def verify_if_there_is_version_in_database(user):
    engine = get_connector()
    metadata = MetaData()
    configs = Table("configs", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(configs).where(configs.c.s_user == user)
        result = conn.execute(query).mappings().all()  # retorna lista de dicts
        if len(result) > 0:
            return True
        return False

@app.route("/analysis", methods=["POST"])
def analysis():
    try:
        global version, db_config, channel
        data = request.get_json()
        db_config = {
            'host':     data['host'],
            'port':     data['port'],
            'db':       data['database'],
            'user':     data['user'],
            'password': data['password'],
        }

        if verify_if_there_is_version_in_database(1):
            version = get_version_in_database(1)
            if version is None:
                name = "user:get_version"
                task = {
                    "name" : name,
                    "version" : "",
                    "body" : {
                        "db_inst_config" : db_config,
                        "type" : "version",
                        "analysis_config": {}
                    },
                }
                publish_message("tasks_to_process", task)
                body = get_done_message(name)
                version = body['version']
                insert_version_in_database(1, version, db_config)
        else:
            set_version_task()

        indicators = ["Engagement", "Performance", "Motivation"]
        set_global_analysis(indicators)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

def set_version_task():
    name = "user:get_version"
    task = {
        "name" : name,
        "version" : "",
        "body" : {
            "db_inst_config" : db_config,
            "type" : "version",
            "analysis_config": {}
        },
    }
    publish_message("tasks_to_process", task)
    body = get_done_message(name)
    version = body['version']
    insert_version_in_database(1, version, db_config)

def set_global_analysis(indicators):
    counter = 1
    for indicator in indicators:
        task = {
            "name" : f"user:set_global_{indicator.lower()}",
            "version" : version,
            "body" : {
                "db_inst_config" : db_config,
                "type" : f"global_analysis_{indicator.lower()}",
                "analysis_config" : {
                    "id" : None,
                    "type" : "geral",
                    "batch_size" : 20,
                    "processed" : 0,
                    "total" : 0
                }
            }
        }

        try:
            insert_global_analysis_status(1, counter, 'P')  # Indicador 1: Engagement, Status 'I' (Idle
            counter += 1
            publish_message("tasks_to_process", task, priority=1)
        except Exception as e:
            continue

@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True, port=5050)