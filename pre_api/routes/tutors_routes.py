from flask import Blueprint, request, jsonify
import pandas as pd

from services.tutors.general.build_all_subjects_tutors import build_all_subjects_tutors
from services.tutors.subject.build_tutors_subject_summary import build_tutors_subject_summary
from services.tutors.subject.build_tutors_subject_interaction_channels import build_tutors_subject_interaction_channels
from services.tutors.subject.build_tutors_subject_rankings import build_tutors_subject_rankings
from services.tutors.subject.build_tutors_subject_indicators import build_tutors_subject_indicators
from services.tutors.subject.indicators.build_tutors_subject_access import build_tutors_subject_access
from services.tutors.subject.indicators.build_tutors_subject_feedback import build_tutors_subject_feedback
from services.tutors.subject.indicators.build_tutors_subject_response_forums import build_tutors_subject_response_forums
from services.tutors.tutor.build_tutors_subject_tutor_summary import build_tutors_subject_tutor_summary
from services.tutors.tutor.build_tutors_subject_tutor_indicators import build_tutors_subject_tutor_indicators
from services.tutors.tutor.build_tutors_subject_tutor_access import build_tutors_subject_tutor_access
from services.tutors.tutor.build_tutors_subject_tutor_response_forums import build_tutors_subject_tutor_response_forums
from services.tutors.tutor.build_tutors_subject_tutor_feedback import build_tutors_subject_tutor_feedback
from services.tutors.tutor.build_tutors_subject_tutor_graphs import build_tutors_subject_tutor_graphs
from services.tutors.general.build_tutors_general_indicators import build_tutors_general_indicators
from services.tutors.general.build_tutors_general_summary import build_tutors_general_summary
from services.tutors.general.build_tutors_general_rankings import build_tutors_general_rankings
from services.tutors.general.build_general_tutors_subjects_indicators import build_general_tutors_subjects_indicators

from .helpers import parse_ranking_query_params

tutors_bp = Blueprint("tutors_routes", __name__)


@tutors_bp.route("/subjects/tutors", methods=["GET", "OPTIONS"])
def get_all_subjects_tutors():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_all_subjects_tutors()
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:id>/summary", methods=["GET", "OPTIONS"])
def tutors_subject_summary(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_summary(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:id>/indicators", methods=["GET", "OPTIONS"])
def tutors_subject_indicators(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_indicators(id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:id>/interaction_channels", methods=["GET", "OPTIONS"])
def subject_tutors_subject_interaction_channels(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_interaction_channels(id)

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:id>/rankings", methods=["GET", "OPTIONS"])
def tutors_subject_rankings(id):
    if request.method == "OPTIONS":
        return "", 200
    kind, limit, error_response, status_code = parse_ranking_query_params()
    if error_response is not None:
        return error_response, status_code

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


@tutors_bp.route("/analysis/tutors/subject/<int:id>/response_forums", methods=["GET", "OPTIONS"])
def subject_tutors_subject_response_forums(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_response_forums(id)

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:id>/access", methods=["GET", "OPTIONS"])
def subject_tutors_subject_access(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_access(id)

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:id>/feedback", methods=["GET", "OPTIONS"])
def subject_tutors_subject_feedback(id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_feedback(id)

        if data is None:
            return jsonify({"data": {}, "error": f"there is no subject with id {id}"}), 404

        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/summary", methods=["GET", "OPTIONS"])
def subject_tutors_subject__tutor_summary(subject_id, tutor_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_tutor_summary(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/indicators", methods=["GET", "OPTIONS"])
def subject_tutors_subject_tutor_indicators(subject_id, tutor_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_tutor_indicators(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/access", methods=["GET", "OPTIONS"])
def subject_tutors_subject_tutor_access(subject_id, tutor_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_tutor_access(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/response_forums", methods=["GET", "OPTIONS"])
def subject_tutors_subject_tutor_response_forums(subject_id, tutor_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_tutor_response_forums(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/feedback", methods=["GET", "OPTIONS"])
def subject_tutors_subject_tutor_feedback(subject_id, tutor_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_tutor_feedback(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/subject/<int:subject_id>/tutor/<int:tutor_id>/graphs", methods=["GET", "OPTIONS"])
def subject_tutors_subject_tutor_graphs(subject_id, tutor_id):
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_subject_tutor_graphs(subject_id, tutor_id)
        if not data:
            return jsonify({"data": {}, "error": f"there is no subject with id {subject_id}"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/general/indicators", methods=["GET", "OPTIONS"])
def tutors_general_indicators():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_general_indicators()
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/general/summary", methods=["GET", "OPTIONS"])
def tutors_general_summary():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_tutors_general_summary()
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/summary"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/general/rankings", methods=["GET", "OPTIONS"])
def tutors_general_rankings():
    if request.method == "OPTIONS":
        return "", 200
    kind, limit, error_response, status_code = parse_ranking_query_params()
    if error_response is not None:
        return error_response, status_code

    try:
        data = build_tutors_general_rankings(kind, limit)
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/rankings"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500


@tutors_bp.route("/analysis/tutors/general/subjects/indicators", methods=["GET", "OPTIONS"])
def general_tutors_subjects_indicators():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = build_general_tutors_subjects_indicators()
        if not data:
            return jsonify({"data": {}, "error": "error /analysis/general/subjects/indicators"}), 404
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": f"internal error: {e}"}), 500
