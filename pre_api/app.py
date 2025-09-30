from flask import request, jsonify, Flask, send_file
from src.tarrafa.processor import Processor
from dotenv import load_dotenv
import requests

app = Flask(__name__)
api_base_url = 'http://127.0.0.1:5000'
indicator_index_translate = {"engagement": 1, "performance": 2, "motivation": 3,"pedagogic": 4}
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
    try:
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
            _ = requests.post(api_base_url + "/set_version", json={"db_inst_config": db_config})

        indicators = ["Engagement", "Performance", "Motivation"]
        processor.set_global_analysis(indicators, db_config)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/analysis/<indicator>", methods=["GET"])
def indicatorAnalysis(indicator):
    indicator = indicator.lower()
    global indicator_index_translate
    if indicator not in indicator_index_translate:
        return jsonify({"error": "indicator inválido"}), 400
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    body = {
        "id": request.args.get("id", type=int),
        "query": request.args.get("query"),
        "analysis_type": indicator,
        "indicator_index": indicator_index_translate[indicator]
    }

    try: 
        response = requests.post(api_base_url + "/handle-analysis",json=body,headers=headers)
        response.raise_for_status()
        data = response.json()
        return jsonify(data), 200
    except requests.RequestException as error:
        return jsonify({"error": f"falha requisição externa: {str(error)}"}), response.status_code
    except Exception as error:
        return jsonify({"error": f"erro interno: {str(error)}"}), 500

@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True, port=5050)