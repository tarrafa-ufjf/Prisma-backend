from flask import request, jsonify, Flask, send_file
from database import DatabaseAdmin
from rabbit import RabbitMQAdmin
from sqlalchemy import and_, select
from dotenv import load_dotenv
import json, time
import requests

app = Flask(__name__)
version = None
db_config = None
load_dotenv()

class Processor:
    def __init__(self, rabbit_admin, db_config=None):
        self.rabbit_admin = rabbit_admin
        self.db_admin = DatabaseAdmin()
        self.db_config = db_config

    def get_done_message(self, name):
        global channel
        found = False
        res = None
        while not found:
            time.sleep(0.25)
            method_frame, _, body = channel.basic_get(queue="Done", auto_ack=False)
            if method_frame:
                message = json.loads(body.decode())
                nome = message.get("name") 
                if nome == name:
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    found = True
                    res = message.get("body")
                else:
                    channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                    time.sleep(0.1)
            else:
                time.sleep(0.25)
        return res

    def wait_until_done(self, s_user, indicator, status, poll_interval=2):
        engine = self.db_admin.get_connector()
        global_analysis = self.db_admin.get_global_analysis_table()

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

    def handle_analysis(self, analysis_type, global_fn, indicator_index=0):
        self.version = self.db_admin.get_version_in_database(1)
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
                    "db_inst_config": self.db_config,
                    "analysis_config": analysis_config,
                    "type": analysis_type,
                },
            }
            self.rabbit_admin.publish_message("tasks_to_process", task, priority=2)
            body = self.get_done_message(name)
            return jsonify(body), 200

        else:
            name = f"user:global_analysis_{analysis_type}"
            self.wait_until_done(1, indicator_index, "D")

            if global_fn == 'get_all_from_table':
                self.db_admin.get_all_from_table(analysis_type, user_id=1)
            elif global_fn == 'get_all_performance_global':
                rows = self.get_all_performance_global(user_id=1)
            elif global_fn == 'get_all_engajamento_global':
                rows = self.get_all_engajamento_global(user_id=1)
            elif global_fn == 'get_all_motivation_global':
                rows = self.get_all_motivation_global(user_id=1)
            elif global_fn == 'get_all_pedagogic_global':
                rows = self.get_all_pedagogic_global(user_id=1)

            data = [dict(row) for row in rows]
            return jsonify(data), 200
    
    def get_all_engajamento_global(self, user_id=1):
        return self.db_admin.get_all_from_table("engajamento_global", user_id)

    def get_all_performance_global(self, user_id=1):
        return self.db_admin.get_all_from_table("performance_global", user_id)

    def get_all_motivation_global(self, user_id=1):
        return self.db_admin.get_all_from_table("motivation_global", user_id)

    def get_all_pedagogic_global(self, user_id=1):
        return self.db_admin.get_all_from_table("pedagogic_global", user_id)
    
    def set_global_analysis(self, indicators, db_config=None):
        counter = 1
        for indicator in indicators:
            task = {
                "name" : f"user:set_global_{indicator.lower()}",
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
                self.db_admin.insert_global_analysis_status(1, counter, 'P')  # Indicador 1: Engagement, Status 'I' (Idle
                counter += 1
                self.rabbit_admin.publish_message("tasks_to_process", task, priority=1)
            except Exception as e:
                print(f"Erro ao inserir status para {indicator}: {e}")

@app.route("/pedagogic", methods=["GET"])
def pedagogic():
    rabbit_admin = RabbitMQAdmin()
    processor = Processor(rabbit_admin, version, db_config)
    return processor.handle_analysis("pedagogic", 'get_all_from_table', indicator_index=4)

@app.route("/performance", methods=["GET"])
def performance():
    rabbit_admin = RabbitMQAdmin()
    processor = Processor(rabbit_admin, version, db_config)
    return processor.handle_analysis("performance", 'get_all_performance_global', indicator_index=2)

@app.route("/motivation", methods=["GET"])
def motivation():
    rabbit_admin = RabbitMQAdmin()
    processor = Processor(rabbit_admin, version, db_config)
    return processor.handle_analysis("motivation", 'get_all_motivation_global', indicator_index=3)

@app.route("/engagement", methods=["GET"])
def engagement():
    rabbit_admin = RabbitMQAdmin()
    processor = Processor(rabbit_admin, version, db_config)
    return processor.handle_analysis("engagement", 'get_all_engajamento_global', indicator_index=1)

@app.route("/analysis", methods=["POST"])
def analysis():
    # try:
    data = request.get_json()
    db_config = {
        'host':     data['host'],
        'port':     data['port'],
        'db':       data['database'],
        'user':     data['user'],
        'password': data['password'],
    }

    rabbit_admin = RabbitMQAdmin()
    processor = Processor(rabbit_admin, db_config)

    if processor.db_admin.verify_if_there_is_version_in_database(1):
        version = processor.db_admin.get_version_in_database(1)
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
            processor.rabbit_admin.publish_message("tasks_to_process", task)
            body = processor.get_done_message(name)
            version = body['version']
            processor.db_admin.insert_version_in_database(1, version, db_config)
    else:
        _ = requests.post("http://localhost:5000/set_version", json={"db_inst_config": db_config})

    indicators = ["Engagement", "Performance", "Motivation"]
    processor.set_global_analysis(indicators, db_config)

    return jsonify({"status": "ok"}), 200
    # except Exception as e:
    #     return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True, port=5050)