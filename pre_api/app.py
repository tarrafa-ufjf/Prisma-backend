from flask import request, jsonify, Flask, send_file
from processor import Processor
from dotenv import load_dotenv

app = Flask(__name__)
api_base_url = 'http://127.0.0.1:5000'
indicator_index_translate = {"engagement": 1, "performance": 2, "motivation": 3,"pedagogic": 4}
load_dotenv()

indicators = ["engagement", "performance", "motivation"]

@app.route("/analysis/<indicator>", methods=["GET"])
def indicatorAnalysis(indicator):
    indicator = indicator.lower()
    processor = Processor(user=1)

    global indicator_index_translate
    if indicator not in indicator_index_translate:
        return jsonify({"error": "indicator inválido"}), 400

    try: 
        response = processor.handle_analysis(indicator, 'get_all_'+indicator+'_global', request, indicator_index=indicator_index_translate[indicator])
        return jsonify(response), 200
    except Exception as error:
        return jsonify({"error": f"erro interno: {str(error)}"}), 500

@app.route("/analysis", methods=["PUT"])
def analysis():
    global indicators
    db_inst_config = request.get_json()
    processor = Processor(user=1)
    version = processor.get_version(user_id=1, db_config=db_inst_config)

    try:
        processor.db_admin.insert_version_in_database(1, version, db_inst_config)
    except Exception as e:
        print(f"Erro ao inserir versão na base de dados: {e}")

    processor.set_global_analysis(indicators, db_config=db_inst_config)

    result = {"message": "Análises iniciadas com sucesso",
              "version": version}
    return jsonify(result), 200

@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True, port=5050)