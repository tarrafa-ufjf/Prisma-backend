import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from auth import require_admin_user
from database import DatabaseAdmin
from services.moodle_config_service import (
    MoodleConfigError,
    get_saved_moodle_config,
    save_moodle_config,
    serialize_moodle_config,
    test_moodle_config,
)


admin_bp = Blueprint("admin_routes", __name__, url_prefix="/admin")


def _datetime_to_iso(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _as_aware_datetime(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _scheduler_is_running(heartbeat_at, now, timeout_seconds):
    if heartbeat_at is None:
        return False
    heartbeat_at = _as_aware_datetime(heartbeat_at)
    return now - heartbeat_at <= timedelta(seconds=timeout_seconds)


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
        version, _config = test_moodle_config(payload)
    except MoodleConfigError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"ok": True, "version": version}), 200


@admin_bp.route("/scheduler/status", methods=["GET", "OPTIONS"])
def get_scheduler_status():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    timeout_seconds = int(os.getenv("SCHEDULER_HEARTBEAT_TIMEOUT_SECONDS", 60))
    rows = [dict(row) for row in DatabaseAdmin().get_scheduler_status_rows()]
    now = datetime.now(timezone.utc)
    last_heartbeat_at = max(
        (
            _as_aware_datetime(row.get("heartbeat_at"))
            for row in rows
            if row.get("heartbeat_at") is not None
        ),
        default=None,
    )
    running = _scheduler_is_running(last_heartbeat_at, now, timeout_seconds)

    jobs = [
        {
            "id": row["job_id"],
            "channel": row["channel"],
            "next_run_at": _datetime_to_iso(row.get("next_run_at")),
            "last_status": row.get("last_status"),
            "last_started_at": _datetime_to_iso(row.get("last_started_at")),
            "last_finished_at": _datetime_to_iso(row.get("last_finished_at")),
            "last_error": row.get("last_error") or None,
        }
        for row in rows
    ]

    return jsonify(
        {
            "running": running,
            "last_heartbeat_at": _datetime_to_iso(last_heartbeat_at),
            "heartbeat_timeout_seconds": timeout_seconds,
            "jobs": jobs,
        }
    ), 200
