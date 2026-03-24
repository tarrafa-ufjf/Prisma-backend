from flask import Blueprint, request, jsonify

from services.student.subject.build_subject_summary import build_subject_summary
from services.student.subject.build_subject_info_graphs import build_subject_info_graphs
from services.student.subject.build_subject_rankings import build_subject_rankings
from services.student.subject.build_subject_indicators import build_subject_indicators
from services.student.subject.indicators.build_subject_students_engagement import build_subject_students_engagement
from services.student.subject.indicators.build_subject_students_motivation import build_subject_students_motivation
from services.student.subject.indicators.build_subject_students_performance import build_subject_students_performance
from services.student.subject.indicators.build_subject_students_cognitive import build_subject_students_cognitive
from services.student.subject.indicators.build_subject_students_pedagogic import build_subject_students_pedagogic
from services.student.subject.indicators.build_subject_students_give_up import build_subject_students_give_up
from services.student.student.build_subject_student_summary import build_subject_student_summary
from services.student.student.build_subject_student_grades import build_subject_student_grades
from services.student.student.build_subject_student_engagement import build_subject_student_engagement
from services.student.student.build_subject_student_motivation import build_subject_student_motivation
from services.student.student.build_subject_student_performance import build_subject_student_performance
from services.student.student.build_subject_student_pedagogic import build_subject_student_pedagogic
from services.student.student.build_subject_student_cognitive import build_subject_student_cognitive
from services.student.student.build_subject_student_give_up import build_subject_student_give_up
from services.student.student.build_subject_student_indicators import build_subject_student_indicators
from services.student.general.build_general_subjects_indicators import build_general_subjects_indicators
from services.student.general.build_all_subjects import build_all_subjects
from services.student.general.build_general_indicators import build_general_indicators
from services.student.general.build_general_summary import build_general_summary
from services.student.general.build_general_rankings import build_general_rankings

from .helpers import parse_ranking_query_params

student_bp = Blueprint("student_routes", __name__)


@student_bp.route("/subjects", methods=["GET", "OPTIONS"])
def get_all_subjects():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_all_subjects()
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/summary", methods=["GET", "OPTIONS"])
def subject_summary(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_summary(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/indicators", methods=["GET", "OPTIONS"])
def subject_indicators(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_indicators(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/info_graphs", methods=["GET", "OPTIONS"])
def subject_info_graphs(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_info_graphs(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/rankings", methods=["GET", "OPTIONS"])
def subject_rankings(id):
    if request.method == "OPTIONS":
        return "", 200
    kind, limit, error_response, status_code = parse_ranking_query_params()
    if error_response is not None:
        return error_response, status_code

    try:
        data = build_subject_rankings(id, kind, limit)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/students/engagement", methods=["GET", "OPTIONS"])
def subject_students_engagement(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_students_engagement(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/students/motivation", methods=["GET", "OPTIONS"])
def subject_students_motivation(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_students_motivation(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/students/performance", methods=["GET", "OPTIONS"])
def subject_students_performance(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_students_performance(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/students/cognitive", methods=["GET", "OPTIONS"])
def subject_students_cognitive(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_students_cognitive(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/students/pedagogic", methods=["GET", "OPTIONS"])
def subject_students_pedagogic(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_students_pedagogic(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:id>/students/give_up", methods=["GET", "OPTIONS"])
def subject_students_give_up(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_students_give_up(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/summary", methods=["GET", "OPTIONS"])
def subject_student_summary(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_summary(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/grades", methods=["GET", "OPTIONS"])
def subject_student_grades(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_grades(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/engagement", methods=["GET", "OPTIONS"])
def subject_student_engagement(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_engagement(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/motivation", methods=["GET", "OPTIONS"])
def subject_student_motivation(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_motivation(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/performance", methods=["GET", "OPTIONS"])
def subject_student_performance(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_performance(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/cognitive", methods=["GET", "OPTIONS"])
def subject_student_cognitive(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_cognitive(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/pedagogic", methods=["GET", "OPTIONS"])
def subject_student_pedagogic(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_pedagogic(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/give_up", methods=["GET", "OPTIONS"])
def subject_student_give_up(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_give_up(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/subject/<int:subject_id>/student/<int:student_id>/indicators", methods=["GET", "OPTIONS"])
def subject_student_indicators(subject_id, student_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_subject_student_indicators(subject_id, student_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/general/subjects/indicators", methods=["GET", "OPTIONS"])
def general_subjects_indicators():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_general_subjects_indicators()
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/subjects/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/general/indicators", methods=["GET", "OPTIONS"])
def general_indicators():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_general_indicators()
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/general/summary", methods=["GET", "OPTIONS"])
def general_summary():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_general_summary()
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/summary"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@student_bp.route("/analysis/general/rankings", methods=["GET", "OPTIONS"])
def general_rankings():
    if request.method == "OPTIONS":
        return "", 200
    kind, limit, error_response, status_code = parse_ranking_query_params()
    if error_response is not None:
        return error_response, status_code

    try:
        data = build_general_rankings(kind, limit)
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/rankings"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
