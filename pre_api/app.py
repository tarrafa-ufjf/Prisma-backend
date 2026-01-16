from flask import request, jsonify, Flask, send_file
from src.analysis_lib.analysis.analyzer import Analyzer

from pre_api.services.student.subject.build_subject_summary import build_subject_summary
from pre_api.services.student.subject.build_subject_info_graphs import build_subject_info_graphs
from pre_api.services.student.subject.build_subject_rankings import build_subject_rankings
from pre_api.services.student.subject.build_subject_indicators import build_subject_indicators
from pre_api.services.student.subject.indicators.build_subject_students_engagement import build_subject_students_engagement
from pre_api.services.student.subject.indicators.build_subject_students_motivation import build_subject_students_motivation
from pre_api.services.student.subject.indicators.build_subject_students_performance import build_subject_students_performance
from pre_api.services.student.subject.indicators.build_subject_students_cognitive import build_subject_students_cognitive
from pre_api.services.student.subject.indicators.build_subject_students_pedagogic import build_subject_students_pedagogic
from pre_api.services.student.subject.indicators.build_subject_students_give_up import build_subject_students_give_up
from pre_api.services.student.student.build_subject_student_summary import build_subject_student_summary
from pre_api.services.student.student.build_subject_student_grades import build_subject_student_grades
from pre_api.services.student.student.build_subject_student_engagement import build_subject_student_engagement
from pre_api.services.student.student.build_subject_student_motivation import build_subject_student_motivation
from pre_api.services.student.student.build_subject_student_performance import build_subject_student_performance
from pre_api.services.student.student.build_subject_student_pedagogic import build_subject_student_pedagogic
from pre_api.services.student.student.build_subject_student_cognitive import build_subject_student_cognitive
from pre_api.services.student.student.build_subject_student_give_up import build_subject_student_give_up
from pre_api.services.student.student.build_subject_student_indicators import build_subject_student_indicators
from pre_api.services.student.general.build_general_subjects_indicators import build_general_subjects_indicators
from pre_api.services.student.general.build_all_subjects import build_all_subjects
from pre_api.services.student.general.build_general_indicators import build_general_indicators
from pre_api.services.student.general.build_general_summary import build_general_summary 
from pre_api.services.student.general.build_general_rankings import build_general_rankings

from pre_api.services.tutors.subject.build_tutors_subject_summary import build_tutors_subject_summary
from pre_api.services.tutors.subject.build_tutors_subject_interaction_channels import build_tutors_subject_interaction_channels
from pre_api.services.tutors.subject.build_tutors_subject_rankings import build_tutors_subject_rankings
from pre_api.services.tutors.subject.build_tutors_subject_indicators import build_tutors_subject_indicators
from services.tutors.subject.indicators.build_tutors_subject_access import build_tutors_subject_access
from services.tutors.subject.indicators.build_tutors_subject_response_forums import build_tutors_subject_response_forums
from services.tutors.tutor.build_tutors_subject_tutor_summary import build_tutors_subject_tutor_summary
from services.tutors.tutor.build_tutors_subject_tutor_indicators import build_tutors_subject_tutor_indicators
from services.tutors.tutor.build_tutors_subject_tutor_access import build_tutors_subject_tutor_access
from services.tutors.tutor.build_tutors_subject_tutor_response_forums import build_tutors_subject_tutor_response_forums
from services.tutors.tutor.build_tutors_subject_tutor_graphs import build_tutors_subject_tutor_graphs
from pre_api.services.tutors.general.build_tutors_general_indicators import build_tutors_general_indicators
from pre_api.services.tutors.general.build_tutors_general_summary import build_tutors_general_summary 
from pre_api.services.tutors.general.build_tutors_general_rankings import build_tutors_general_rankings



from processor import Processor
from flasgger import Swagger
import json
from dotenv import load_dotenv
from flask_cors import CORS
import pandas as pd

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

indicators = ["engagement", 
              "performance", 
              "motivation", 
              "cognitive", 
              "pedagogic",
              "give_up"
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
    
@app.route("/analysis/subject/<int:id>/students/pedagogic", methods=["GET"])
def subject_students_pedagogic(id):
    try:
        data = build_subject_students_pedagogic(id)
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
    
@app.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/pedagogic", methods=["GET"])
def subject_student_pedagogic(subject_id, student_id):
    try:
        data = build_subject_student_pedagogic(subject_id, student_id)
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
    
@app.route("/analysis/general/subjects/indicators", methods=["GET"])
def general_subjects_indicators():
    try:
        data = build_general_subjects_indicators()
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/subjects/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
## Página de análise geral da Disciplina
@app.route("/analysis/general/indicators", methods=["GET"])
def general_indicators():
    try:
        data = build_general_indicators()
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/general/summary", methods=["GET"])
def general_summary():
    try:
        data = build_general_summary()
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/summary"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/general/rankings", methods=["GET"])
def general_rankings():
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
        data = build_general_rankings(kind, limit)
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/rankings"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500

## ======
## TUTORS
## ======

## Página da Disciplina
@app.route("/analysis/tutors/subject/<int:id>/summary", methods=["GET"])
def tutors_subject_summary(id):
    try:
        data = build_tutors_subject_summary(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:id>/indicators", methods=["GET"])
def tutors_subject_indicators(id):
    try:
        data = build_tutors_subject_indicators(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:id>/interaction_channels", methods=["GET"])
def subject_tutors_subject_interaction_channels(id):
    try:
        data = build_tutors_subject_interaction_channels(id) 

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
        
@app.route("/analysis/tutors/subject/<int:id>/rankings", methods=["GET"])
def tutors_subject_rankings(id):
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
        data = build_tutors_subject_rankings(id, kind, limit)

        if data is None:
            return jsonify({"id": id, "ranking": [], "type": f"{kind}"}), 404

        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient="records")

        if not data:  
            return jsonify({"id": id, "ranking": [], "type": f"{kind}"}), 404

        return jsonify({"data": data}), 200
        
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
## Página de Tutores na Disciplina
@app.route("/analysis/tutors/subject/<int:id>/response_forums", methods=["GET"])
def subject_tutors_subject_response_forums(id):
    try:
        data = build_tutors_subject_response_forums(id) 

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:id>/access", methods=["GET"])
def subject_tutors_subject_access(id):
    try:
        data = build_tutors_subject_access(id) 

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
## Página de Tutor na Disciplina
@app.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/summary", methods=["GET"])
def subject_tutors_subject__tutor_summary(subject_id, tutor_id):
    try:
        data = build_tutors_subject_tutor_summary(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/indicators", methods=["GET"])
def subject_tutors_subject_tutor_indicators(subject_id, tutor_id):
    try:
        data = build_tutors_subject_tutor_indicators(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/access", methods=["GET"])
def subject_tutors_subject_tutor_access(subject_id, tutor_id):
    try:
        data = build_tutors_subject_tutor_access(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/response_forums", methods=["GET"])
def subject_tutors_subject_tutor_response_forums(subject_id, tutor_id):
    try:
        data = build_tutors_subject_tutor_response_forums(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/graphs", methods=["GET"])
def subject_tutors_subject_tutor_graphs(subject_id, tutor_id):
    try:
        data = build_tutors_subject_tutor_graphs(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
# Página Global de Tutores
@app.route("/analysis/tutors/general/indicators", methods=["GET"])
def tutors_general_indicators():
    try:
        data = build_tutors_general_indicators()
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/general/summary", methods=["GET"])
def tutors_general_summary():
    try:
        data = build_tutors_general_summary()
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/summary"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
    
@app.route("/analysis/tutors/general/rankings", methods=["GET"])
def tutors_general_rankings():
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
        data = build_tutors_general_rankings(kind, limit)
        if not data:
            return jsonify({"data": {}, "error": f"error /analysis/general/rankings"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@app.route("/analysis", methods=["PUT"])
def analysis():
    # global indicators
    db_inst_config = request.get_json()
    processor = Processor(user=1)
    version = processor.get_version(institution_id=1, db_config=db_inst_config)

    try:
        processor.db_admin.insert_version_in_database(1, version, db_inst_config)
    except Exception as e:
        print(f"Erro ao inserir versão na base de dados: {e}")

    processor.set_subjects_analysis(db_config=db_inst_config)

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