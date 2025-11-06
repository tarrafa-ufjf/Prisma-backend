from flask import request, jsonify, Flask, send_file
from src.analysis_lib.analysis.analysis import Analyzer
from pre_api.services.build_subject_summary import build_subject_summary
from pre_api.services.build_subject_info_graphs import build_subject_info_graphs
from pre_api.services.build_subject_rankings import build_subject_rankings
from pre_api.services.build_subject_students_engagement import build_subject_students_engagement
from pre_api.services.build_subject_students_motivation import build_subject_students_motivation
from pre_api.services.build_subject_students_performance import build_subject_students_performance
from pre_api.services.build_subject_students_cognitive import build_subject_students_cognitive
from pre_api.services.build_subject_students_give_up import build_subject_students_give_up
from pre_api.services.student.build_subject_student_summary import build_subject_student_summary
from pre_api.services.student.build_subject_student_grades import build_subject_student_grades
from pre_api.services.student.build_subject_student_engagement import build_subject_student_engagement
from pre_api.services.student.build_subject_student_motivation import build_subject_student_motivation
from pre_api.services.student.build_subject_student_performance import build_subject_student_performance
from pre_api.services.student.build_subject_student_cognitive import build_subject_student_cognitive
from pre_api.services.student.build_subject_student_give_up import build_subject_student_give_up
from pre_api.services.student.build_subject_student_indicators import build_subject_student_indicators
from pre_api.services.build_all_subjects import build_all_subjects
from pre_api.services.build_subject_indicators import build_subject_indicators
from processor import Processor
from flasgger import Swagger
import json
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)
api_base_url = 'http://127.0.0.1:5000'
indicator_index_translate = {"engagement": 1, 
                             "performance": 2,
                              "motivation": 3,
                              "pedagogic": 4,
                              "cognitive": 5,
                              "give_up": 6}
load_dotenv()
analyzer = Analyzer()

indicators = [#"engagement", 
            #   "performance", 
            #    "motivation", 
               "cognitive", 
            #   "pedagogic",
                # "give_up"
]

## General
@app.route("/subjects", methods=["GET"])
def get_all_subjects():
    try:
        data = build_all_subjects()
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500

## Página de Disciplina
@app.route("/analysis/subject/<int:id>/summary", methods=["GET"])
def subject_summary(id):
    try:
        data = build_subject_summary(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:id>/indicators", methods=["GET"])
def subject_indicators(id):
    try:
        data = build_subject_indicators(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:id>/info_graphs", methods=["GET"])
def subject_info_graphs(id):
    try:
        data = build_subject_info_graphs(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
        
@app.route("/analysis/subject/<int:id>/rankings", methods=["GET"])
def subject_rankings(id):
    kind = request.args.get("type", "best-performance")
    limit_str = request.args.get("limit", "5")

    if kind not in ("best-performance", "at-risk"):
        return jsonify({"error": "invalid 'type'. Use 'best-performance' or 'at-risk'"}), 400

    try:
        limit = int(limit_str)
    except ValueError:
        limit = 5
    limit = max(1, min(limit, 100))  

    try:
        data = build_subject_rankings(id, kind, limit)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500

## Página de Alunos na Disciplina
@app.route("/analysis/subject/<int:id>/students/engagement", methods=["GET"])
def subject_students_engagement(id):
    try:
        data = build_subject_students_engagement(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:id>/students/motivation", methods=["GET"])
def subject_students_motivation(id):
    try:
        data = build_subject_students_motivation(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:id>/students/performance", methods=["GET"])
def subject_students_performance(id):
    try:
        data = build_subject_students_performance(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:id>/students/cognitive", methods=["GET"])
def subject_students_cognitive(id):
    try:
        data = build_subject_students_cognitive(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:id>/students/give_up", methods=["GET"])
def subject_students_give_up(id):
    try:
        data = build_subject_students_give_up(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
## Página de Aluno da Disciplina
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/summary", methods=["GET"])
def subject_student_summary(subject_id, student_id):
    try:
        data = build_subject_student_summary(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/grades", methods=["GET"])
def subject_student_grades(subject_id, student_id):
    try:
        data = build_subject_student_grades(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/engagement", methods=["GET"])
def subject_student_engagement(subject_id, student_id):
    try:
        data = build_subject_student_engagement(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/motivation", methods=["GET"])
def subject_student_motivation(subject_id, student_id):
    try:
        data = build_subject_student_motivation(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/performance", methods=["GET"])
def subject_student_performance(subject_id, student_id):
    try:
        data = build_subject_student_performance(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/cognitive", methods=["GET"])
def subject_student_cognitive(subject_id, student_id):
    try:
        data = build_subject_student_cognitive(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/give_up", methods=["GET"])
def subject_student_give_up(subject_id, student_id):
    try:
        data = build_subject_student_give_up(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/indicators", methods=["GET"])
def subject_student_indicators(subject_id, student_id):
    try:
        data = build_subject_student_indicators(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500

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

    # try: 
    response = processor.handle_analysis(indicator, 'get_all_'+indicator+'_global', request, indicator_index=indicator_index_translate[indicator])
    return jsonify(response), 200
    # except Exception as error:
    #     return jsonify({"error": f"erro interno: {str(error)}"}), 500

@app.route("/analysis", methods=["PUT"])
def analysis():
    global indicators
    db_inst_config = request.get_json()
    processor = Processor(user=1)
    version = processor.get_version(institution_id=1, db_config=db_inst_config)

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
    app.run(debug=True)