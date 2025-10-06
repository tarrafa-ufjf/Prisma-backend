from flask import request, jsonify, Flask, send_file
from processor import Processor
from flasgger import Swagger
import json
from dotenv import load_dotenv

app = Flask(__name__)
swagger = Swagger(app)
api_base_url = 'http://127.0.0.1:5000'
indicator_index_translate = {"engagement": 1, 
                             "performance": 2,
                              "motivation": 3,
                              "pedagogic": 4,
                              "cognitive": 5}
load_dotenv()

indicators = ["engagement", "performance", "motivation", "cognitive"]

@app.route("/analysis/general-data/<id>", methods=["GET"])
def courseGeneralData(id):
    """
    Rota de api responsavel por buscar a analise de dados gerais da disciplina
    ---
    responses:
        200:
            description: A analise de dados gerais da disciplina
            examples:
                application/json: { 
                    "data": {
                        "avg_grade_all": 65.83,
                        "course_id": 222,
                        "taxa_aprovacao": 63.39,
                        "total_enrolled": 146
                    }
                }
        400:
            description: Erro no tipo do id
            examples:
                application/json: {
                    "error": "id must be a number"
                }
        404:
            description: Erro no valor do id
            examples:
                application/json: {
                    "data": {},
                    "error": "there is no course with id 102383"
                }
        500:
            description: Erro ao procurar arquivos json
            examples:
                application/json: {
                    "error": "error to decode json"
                }
    """
    try:
        id = int(id)
        try:
            with open('mock_json/general_data.json', 'r') as file:
                json_data = json.load(file)
            found_item = next(filter(lambda item: item.get('course_id') == id, json_data), None)
            if found_item:
                return jsonify({"data": found_item}), 200
            return jsonify({"data": {}, "error": "there is no course with id " + str(id)}), 404
        except FileNotFoundError:
            return jsonify({"error": "file not found"}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "error to decode json"}), 500
    except ValueError:
        return jsonify({"error": "id must be a number"}), 400

@app.route("/analysis/general-info/<id>", methods=["GET"])
def courseGeneralInfo(id):
    """
    Rota de api responsavel por buscar a analise de informações da disciplina
    ---
    responses:
        200:
            description: A analise de informações da disciplina
            examples:
                application/json: {
                    "data": {
                        "abrev": "[D18] - LIC-POR",
                        "date": 1553177261,
                        "id": 222,
                        "name": "[D18] - Aquisi\u00e7\u00e3o de Leitura e Escrita - Letras Portugu\u00eas"
                    }
                }
        400:
            description: Erro no tipo do id
            examples:
                application/json: {
                    "error": "id must be a number"
                }
        404:
            description: Erro no valor do id
            examples:
                application/json: {
                    "data": {},
                    "error": "there is no course with id 102383"
                }
        500:
            description: Erro ao procurar arquivos json
            examples:
                application/json: {
                    "error": "error to decode json"
                }
    """
    try:
        id = int(id)
        try:
            with open('mock_json/general_info.json', 'r') as file:
                json_data = json.load(file)
            found_item = next(filter(lambda item: item.get('id') == id, json_data), None)
            if found_item:
                return jsonify({"data": found_item}), 200
            return jsonify({"data": {}, "error": "there is no course with id " + str(id)}), 404
        except FileNotFoundError:
            return jsonify({"error": "file not found"}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "error to decode json"}), 500
    except ValueError:
        return jsonify({"error": "id must be a number"}), 400

@app.route("/analysis/graphs/<id>", methods=["GET"])
def courseGraphs(id):
    """
    Rota de api responsavel por buscar a analise dos graficos da disciplina
    ---
    responses:
        200:
            description: A analise dos graficos da disciplina
            examples:
                application/json: {
                    "data": {
                        "id": 222,
                        "situations": [
                        {
                            "qtd": 101,
                            "situacao": "Reprovado"
                        },
                        {
                            "qtd": 12,
                            "situacao": "RI"
                        }
                        ],
                        "usage_by_module": [
                        {
                            "course_id": 222,
                            "modulo": "assign",
                            "pct_modulo_no_curso": 23.08,
                            "qtd": 9
                        },
                        {
                            "course_id": 222,
                            "modulo": "url",
                            "pct_modulo_no_curso": 23.08,
                            "qtd": 9
                        },
                        {
                            "course_id": 222,
                            "modulo": "forum",
                            "pct_modulo_no_curso": 17.95,
                            "qtd": 7
                        },
                        {
                            "course_id": 222,
                            "modulo": "folder",
                            "pct_modulo_no_curso": 15.38,
                            "qtd": 6
                        },
                        {
                            "course_id": 222,
                            "modulo": "resource",
                            "pct_modulo_no_curso": 10.26,
                            "qtd": 4
                        },
                        {
                            "course_id": 222,
                            "modulo": "chat",
                            "pct_modulo_no_curso": 2.56,
                            "qtd": 1
                        },
                        {
                            "course_id": 222,
                            "modulo": "lti",
                            "pct_modulo_no_curso": 2.56,
                            "qtd": 1
                        },
                        {
                            "course_id": 222,
                            "modulo": "page",
                            "pct_modulo_no_curso": 2.56,
                            "qtd": 1
                        },
                        {
                            "course_id": 222,
                            "modulo": "quiz",
                            "pct_modulo_no_curso": 2.56,
                            "qtd": 1
                        }
                        ]
                    }
                }
        400:
            description: Erro no tipo do id
            examples:
                application/json: {
                    "error": "id must be a number"
                }
        404:
            description: Erro no valor do id
            examples:
                application/json: {
                    "data": {},
                    "error": "there is no course with id 102383"
                }
        500:
            description: Erro ao procurar arquivos json
            examples:
                application/json: {
                    "error": "error to decode json"
                }
    """
    try:
        id = int(id)
        try:
            with open('mock_json/graphs.json', 'r') as file:
                json_data = json.load(file)
            found_item = next(filter(lambda item: item.get('id') == id, json_data), None)
            if found_item:
                return jsonify({"data": found_item}), 200
            return jsonify({"data": {}, "error": "there is no course with id " + str(id)}), 404
        except FileNotFoundError:
            return jsonify({"error": "file not found"}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "error to decode json"}), 500
    except ValueError:
        return jsonify({"error": "id must be a number"}), 400


@app.route("/analysis/percentual/<id>", methods=["GET"])
def coursePercentual(id):
    """
    Rota de api responsavel por buscar a analise percentual da disciplina
    ---
    responses:
        200:
            description: A analise percentual da disciplina
            examples:
                application/json: {
                    "data": {
                        "boa_interacao_avaliativa": 17.86,
                        "boa_interacao_nao_avalativa": 1.79,
                        "bom_desempenho": 74.34,
                        "id": 222,
                        "relacao_aluno_professor": 0.0
                    }
                }
        400:
            description: Erro no tipo do id
            examples:
                application/json: {
                    "error": "id must be a number"
                }
        404:
            description: Erro no valor do id
            examples:
                application/json: {
                    "data": {},
                    "error": "there is no course with id 102383"
                }
        500:
            description: Erro ao procurar arquivos json
            examples:
                application/json: {
                    "error": "error to decode json"
                }
    """
    try:
        id = int(id)
        try:
            with open('mock_json/percentual.json', 'r') as file:
                json_data = json.load(file)
            found_item = next(filter(lambda item: item.get('id') == id, json_data), None)
            if found_item:
                return jsonify({"data": found_item}), 200
            return jsonify({"data": {}, "error": "there is no course with id " + str(id)}), 404
        except FileNotFoundError:
            return jsonify({"error": "file not found"}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "error to decode json"}), 500
    except ValueError:
        return jsonify({"error": "id must be a number"}), 400


@app.route("/analysis/ranking/<id>", methods=["GET"])
def classRanking(id):
    """
    Rota de api responsavel por buscar o ranking da disciplina
    ---
    responses:
        200:
            description: O ranking da disciplina
            examples:
                application/json: {
                    "data": {
                        "id": 222,
                        "ranking_best": [
                        {
                            "final_grade": 99.0,
                            "name": "GIRLENO CANDIDO",
                            "percentual": 50.0,
                            "pos": 1,
                            "user_id": 1069
                        },
                        {
                            "final_grade": 97.5,
                            "name": "GILM\u00c1RIO",
                            "percentual": 49.0,
                            "pos": 2,
                            "user_id": 1060
                        },
                        {
                            "final_grade": 97.5,
                            "name": "MARINA",
                            "percentual": 49.0,
                            "pos": 3,
                            "user_id": 1680
                        },
                        {
                            "final_grade": 97.0,
                            "name": "JOELMA",
                            "percentual": 48.0,
                            "pos": 4,
                            "user_id": 856
                        },
                        {
                            "final_grade": 97.0,
                            "name": "ELIENE",
                            "percentual": 48.0,
                            "pos": 5,
                            "user_id": 1033
                        }
                        ],
                        "ranking_difficulties": [
                        {
                            "final_grade": 0.0,
                            "name": "J\u00c9SSIKA MIKAELLE",
                            "percentual": 0.0,
                            "pos": 1,
                            "user_id": 847
                        },
                        {
                            "final_grade": 0.0,
                            "name": "CAMILA MIRANDA",
                            "percentual": 0.0,
                            "pos": 2,
                            "user_id": 861
                        },
                        {
                            "final_grade": 0.0,
                            "name": "EVANEIDE",
                            "percentual": 0.0,
                            "pos": 3,
                            "user_id": 1043
                        },
                        {
                            "final_grade": 0.0,
                            "name": "YANA",
                            "percentual": 0.0,
                            "pos": 4,
                            "user_id": 1047
                        },
                        {
                            "final_grade": 0.0,
                            "name": "LUANA CRISTINA",
                            "percentual": 0.0,
                            "pos": 5,
                            "user_id": 1082
                        }
                        ]
                    }
                }
        400:
            description: Erro no tipo do id
            examples:
                application/json: {
                    "error": "id must be a number"
                }
        404:
            description: Erro no valor do id
            examples:
                application/json: {
                    "data": {},
                    "error": "there is no course with id 102383"
                }
        500:
            description: Erro ao procurar arquivos json
            examples:
                application/json: {
                    "error": "error to decode json"
                }
    """
    try:
        id = int(id)
        try:
            with open('mock_json/rankings_students.json', 'r') as file:
                json_data = json.load(file)
            found_item = next(filter(lambda item: item.get('id') == id, json_data), None)
            if found_item:
                return jsonify({"data": found_item}), 200
            return jsonify({"data": {}, "error": "there is no course with id " + str(id)}), 404
        except FileNotFoundError:
            return jsonify({"error": "file not found"}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "error to decode json"}), 500
    except ValueError:
        return jsonify({"error": "id must be a number"}), 400
    

@app.route("/analysis/<indicator>", methods=["GET"])
def indicatorAnalysis(indicator):
    indicator = indicator.lower()
    processor = Processor(user=1)

    global indicator_index_translate
    if indicator not in indicator_index_translate:
        return jsonify({"error": "indicador inválido"}), 400

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