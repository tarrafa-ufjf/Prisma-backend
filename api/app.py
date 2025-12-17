from flask import request, jsonify, Flask
from sqlalchemy import and_, select, create_engine, MetaData, Table, Column, Integer, String
from src.analysis_lib.analysis.analyzer import Analyzer
import os
from dotenv import load_dotenv 
import time
from database import Database, DatabaseAdmin

app = Flask(__name__)
conn = Database()
analyzer = Analyzer()
connector = None
version = None
db_config = None
load_dotenv()

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
        'indicators_status', metadata,
        Column('institution_id', Integer, primary_key=True),
        Column('indicator', Integer, primary_key=True),
        Column('status', String(1), nullable=False)
    )
    return global_analysis

def insert_global_analysis_status(institution_id: int, indicator: int, status: str):
    engine = get_connector()
    global_analysis = get_global_analysis_table()

    with engine.connect() as conn:
        insert_stmt = global_analysis.insert().values(
            institution_id=institution_id,
            indicator=indicator,
            status=status
        )
        conn.execute(insert_stmt)
        conn.commit()

def wait_until_done(institution_id, indicator, status, poll_interval=2):
    engine = get_connector()
    global_analysis = get_global_analysis_table()

    while True:
        with engine.connect() as conn:
            query = select(global_analysis.c.status).where(
                and_(
                    global_analysis.c.institution_id == institution_id,
                    global_analysis.c.status == status,
                    global_analysis.c.indicator == indicator
                )
            )
            result = conn.execute(query).fetchone()

            if result and result.status == "D":
                return True

        time.sleep(poll_interval)  # espera antes de checar de novo

def get_db_config_from_database(institution_id: int):
    engine = get_connector()
    metadata = MetaData()
    configs = Table("configs", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(configs).where(configs.c.institution_id == institution_id)
        result = conn.execute(query).mappings().first()  # pega apenas o primeiro

        if result:
            return {
                "host": result["host"],
                "port": result["port"],
                "db": result["database"],
                "user": result["user"],
                "password": result["password"]
            }
        
        return None

@app.route("/set_version", methods=["POST"])
def set_version():
    global db_config, version

    try:
        db_config = request.json.get("db_inst_config")
        db_admin = DatabaseAdmin()
        version = get_version(db_config)
        db_admin.insert_version_in_database(1, version, db_config)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    
@app.route("/analysis", methods=["PUT"])
def analysis():
    message = request.get_json()
    body = message.get("body", {})
    analysis_type = body["type"]

    config = body.get("db_inst_config") or db_config

    analysis_config = body.get("analysis_config", {})
    if not analysis_config:
        return jsonify({"error": "Configuração de análise ausente"}), 400

    message = {
        "body": {
            "db_inst_config": config,
            "analysis_config": analysis_config,
            "type": analysis_type,
        },
        "version": message.get("version")
    }

    result = select_indicator(analysis_type, message)
    return jsonify(result), 200

def get_all_from_table(table_name, institution_id=1):
    engine = get_connector()
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(table).where(table.c.institution_id == institution_id)  # TODO
        return conn.execute(query).mappings().all()

#Função que retorna o valor da versão do Moodle
def get_version(config):
    global analyzer
    connector = conn.get_connection_with_config(config)
    version = analyzer.get_moodle_version(connector)

    return version


def performance(message):
    body = message.get("body")
    connector = conn.get_connection_with_config(body["db_inst_config"])

    analysis_config = body.get("analysis_config")
    response = analyzer.performance_analysis(analysis_config["id"], analysis_config["type"], message.get("version"), connector)
    return response.to_dict(orient="records")

def engagement(message):
    body = message["body"]
    connector = conn.get_connection_with_config(body["db_inst_config"])

    analysis_config = body.get("analysis_config")
    res = analyzer.engagement_analysis(analysis_config["id"], analysis_config["type"], message.get("version"), connector)
    
    return res.to_dict(orient="records")

def motivation(message):
    body = message["body"]
    connector = conn.get_connection_with_config(body["db_inst_config"])

    analysis_config = body.get("analysis_config")
    res = analyzer.motivation_analysis(analysis_config["id"], analysis_config["type"], message.get("version"), connector)
    return res

def pedagogic(message):
    body = message["body"]
    connector = conn.get_connection_with_config(body["db_inst_config"])

    analysis_config = body.get("analysis_config")
    res = analyzer.pedagogic_analysis(analysis_config["id"], analysis_config["type"], message.get("version"), connector)
    return res.to_dict(orient="records")


def get_all_engajamento_global(institution_id=1):
    return get_all_from_table("engajamento_global", institution_id)


def get_all_performance_global(institution_id=1):
    return get_all_from_table("performance_global", institution_id)


def get_all_motivation_global(institution_id=1):
    return get_all_from_table("motivation_global", institution_id)

def get_all_pedagogic_global(institution_id=1):
    return get_all_from_table("pedagogic_global", institution_id)

def get_version_in_database(user):
    engine = get_connector()
    metadata = MetaData()
    configs = Table("configs", metadata, autoload_with=engine)

    with engine.connect() as conn:
        query = select(configs).where(configs.c.institution_id == user)
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
            institution_id=user,
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
        query = select(configs).where(configs.c.institution_id == user)
        result = conn.execute(query).mappings().all()  # retorna lista de dicts
        if len(result) > 0:
            return True
        return False

@app.route("/")
def hello():
    return jsonify({"status" : "OK"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)