from flask import Blueprint, jsonify, request

from auth import require_admin_user
from services.moodle_config_service import (
    MoodleConfigError,
    get_saved_moodle_config,
    save_moodle_config,
    serialize_moodle_config,
    test_moodle_config,
)


admin_bp = Blueprint("admin_routes", __name__, url_prefix="/admin")


@admin_bp.route("/moodle-config", methods=["GET", "OPTIONS"])
def get_moodle_config():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    config = get_saved_moodle_config()
    if config is None:
        return jsonify({"error": "moodle config not found"}), 404

    return jsonify({"config": serialize_moodle_config(config)}), 200


@admin_bp.route("/moodle-config", methods=["PUT", "OPTIONS"])
def put_moodle_config():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    payload = request.get_json(silent=True) or {}
    try:
        config = save_moodle_config(payload)
    except MoodleConfigError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"config": serialize_moodle_config(config)}), 200


@admin_bp.route("/moodle-config/test", methods=["POST", "OPTIONS"])
def test_moodle_config_route():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    payload = request.get_json(silent=True) or {}
    try:
        version, _config = test_moodle_config(payload, existing_config=get_saved_moodle_config())
    except MoodleConfigError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"ok": True, "version": version}), 200
