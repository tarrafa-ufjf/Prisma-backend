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
            time.sleep(0.5)
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

@app.route("/performance", methods=["GET"])
def performance():
    global db_config, channel, version

    course_id = request.args.get('performance-id', type=int)
    type_ = request.args.get('performance-query')

    if not course_id and request.args.get('performance-query') != 'general':
        return jsonify({"error": "Course ID is required"}), 400
    
    analysis_config = {
        "type" : request.args.get('performance-query'),
        "id" : course_id
    }

    if type_ != 'general':
        name = "user:performance"
        task = {
            "name" : name,
            "version" : version,
            "body" : {
                "db_inst_config" : db_config,
                "analysis_config" : analysis_config,
                "type" : "performance",
            }
        }
        publish_message("tasks_to_process", task, priority=2)
        body = get_done_message(name)
        return jsonify(body), 200
    else:
        name = "user:global_analysis_performance"
        wait_until_done(1, 2, 'D')  # Indicador 2: performance, Status 'D' (Done)
        rows = get_all_performance_global()
        data = [dict(row) for row in rows]  
        return jsonify(data), 200

@app.route("/motivation", methods=["GET"])
def motivation():
    global db_config, channel, version

    course_id = request.args.get('motivation-id', type=int)
    type_ = request.args.get('motivation-query')

    if not course_id and request.args.get('motivation-query') != 'general':
        return jsonify({"error": "Course ID is required"}), 400
    
    analysis_config = {
        "type" : request.args.get('motivation-query'),
        "id" : course_id
    }

    if type_ != 'general':
        name = "user:motivation"
        task = {
            "name" : name,
            "version" : version,
            "body" : {
                "db_inst_config" : db_config,
                "analysis_config" : analysis_config,
                "type" : "motivation",
            }
        }
        publish_message("tasks_to_process", task, priority=2)
        body = get_done_message(name)
        return jsonify(body), 200
    else:
        name = "user:global_analysis_motivation"
        wait_until_done(1, 3, 'D')  # Indicador 3: Motivation, Status 'D' (Done)
        rows = get_all_motivation_global()
        data = [dict(row) for row in rows]  
        return jsonify(data), 200

@app.route("/engagement", methods=["GET"])
def engagement():
    global db_config, channel, version

    version = get_version_in_database(1)

    course_id = request.args.get('engagement-id', type=int)
    type_ = request.args.get('engagement-query')

    if not course_id and request.args.get('engagement-query') != 'general':
        return jsonify({"error": "Course ID is required"}), 400
    
    analysis_config = {
        "type" : request.args.get('engagement-query'),
        "id" : course_id
    }

    if type_ != 'general':
        name = "user:engagement"
        task = {
            "name" : name,
            "version" : version,
            "body" : {
                "db_inst_config" : db_config,
                "analysis_config" : analysis_config,
                "type" : "engagement",
            }
        }
        print(f"Publishing task: {task}")
        publish_message("tasks_to_process", task, priority=2)
        body = get_done_message(name)
        return jsonify(body), 200
    else:
        name = "user:global_analysis_engagement"
        wait_until_done(1, 1, 'D')  # Indicador 1: Engagement, Status 'D' (Done)
        rows = get_all_engajamento_global()
        data = [dict(row) for row in rows]  
        return jsonify(data), 200

def get_all_engajamento_global():
    engine = get_connector()
    metadata = MetaData()
    engajamento_global = Table("engajamento_global", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(engajamento_global).where(engajamento_global.c.s_user == 1) #TODO
        result = conn.execute(query).mappings().all()  # retorna lista de dicts
        return result

def get_all_performance_global():
    engine = get_connector()
    metadata = MetaData()
    performance_global = Table("performance_global", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(performance_global).where(performance_global.c.s_user == 1) #TODO
        result = conn.execute(query).mappings().all()  # retorna lista de dicts
        return result

def get_all_motivation_global():
    engine = get_connector()
    metadata = MetaData()
    motivation_global = Table("motivation_global", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(motivation_global).where(motivation_global.c.s_user == 1) #TODO
        result = conn.execute(query).mappings().all()  # retorna lista de dicts
        return result

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

    if verify_if_there_is_version_in_database(1):
        version = get_version_in_database(1)
        print(f"Version found in database: {version}")
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

    indicators = ["Engagement", "Performance"]
    # indicators = ["Motivation"]
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

    return send_from_directory('pages', 'analysis.html'), 200


@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True)