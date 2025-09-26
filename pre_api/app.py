from flask import request, jsonify, Flask, send_file
from src.tarrafa.processor import Processor
from dotenv import load_dotenv
import requests

app = Flask(__name__)
load_dotenv()

@app.route("/pedagogic", methods=["GET"])
def pedagogic():
    processor = Processor(user=1)
    response, status = processor.handle_analysis("pedagogic", 'get_all_pedagogic_global', request, indicator_index=4)
    return jsonify(response), status

@app.route("/performance", methods=["GET"])
def performance():
    processor = Processor(user=1)
    response, status = processor.handle_analysis("performance", 'get_all_performance_global', request, indicator_index=2)
    return jsonify(response), status

@app.route("/motivation", methods=["GET"])
def motivation():
    processor = Processor(user=1)
    response, status = processor.handle_analysis("motivation", 'get_all_motivation_global', request, indicator_index=3)
    return jsonify(response), status

@app.route("/engagement", methods=["GET"])
def engagement():
    processor = Processor(user=1)
    response, status = processor.handle_analysis("engagement", 'get_all_engajamento_global', request, indicator_index=1)
    return jsonify(response), status

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

    processor = Processor(user=1)

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