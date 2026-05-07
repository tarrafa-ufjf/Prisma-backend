from flask import Blueprint, g, jsonify, request

from auth import (
    AuthError,
    AuthServiceError,
    SupabaseAdminConfigError,
    SupabaseAdminError,
    create_supabase_auth_user,
    delete_supabase_auth_user,
    extract_bearer_token,
    get_current_profile,
    is_admin_profile,
    list_supabase_auth_users,
)


auth_bp = Blueprint("auth_routes", __name__, url_prefix="/auth")


@auth_bp.route("/sign-up", methods=["POST", "OPTIONS"])
def sign_up():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_profile()
    if admin_error_response is not None:
        return admin_error_response

    payload = request.get_json(silent=True) or {}
    user_data, validation_error = build_create_user_payload(payload)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        user = create_supabase_auth_user(user_data)
    except SupabaseAdminConfigError:
        return jsonify({"error": "supabase admin is not configured"}), 500
    except SupabaseAdminError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except AuthServiceError:
        return jsonify({"error": "supabase admin service unavailable"}), 503

    return jsonify({"user": user}), 201


@auth_bp.route("/users", methods=["GET", "OPTIONS"])
def list_users():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_profile()
    if admin_error_response is not None:
        return admin_error_response

    page, per_page, validation_error = parse_pagination_params()
    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        users = list_supabase_auth_users(page=page, per_page=per_page)
    except SupabaseAdminConfigError:
        return jsonify({"error": "supabase admin is not configured"}), 500
    except SupabaseAdminError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except AuthServiceError:
        return jsonify({"error": "supabase admin service unavailable"}), 503

    return jsonify(users), 200


@auth_bp.route("/users/<user_id>", methods=["DELETE", "OPTIONS"])
def delete_user(user_id):
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_profile()
    if admin_error_response is not None:
        return admin_error_response

    should_soft_delete = parse_bool_query_param("should_soft_delete")

    try:
        delete_supabase_auth_user(user_id, should_soft_delete=should_soft_delete)
    except SupabaseAdminConfigError:
        return jsonify({"error": "supabase admin is not configured"}), 500
    except SupabaseAdminError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except AuthServiceError:
        return jsonify({"error": "supabase admin service unavailable"}), 503

    return "", 204


def require_admin_profile():
    token = extract_bearer_token(request.headers.get("Authorization", ""))
    user_id = g.current_user.get("id")

    try:
        profile = get_current_profile(token, user_id)
    except AuthError as exc:
        return jsonify({"error": exc.message}), 401
    except AuthServiceError:
        return jsonify({"error": "authentication service unavailable"}), 503

    if not is_admin_profile(profile):
        return jsonify({"error": "admin role required"}), 403
    return None


def build_create_user_payload(payload):
    email = (payload.get("email") or "").strip()
    password = payload.get("password")

    if not email:
        return None, "email is required"
    if not password:
        return None, "password is required"

    user_data = {
        "email": email,
        "password": password,
    }

    for optional_key in (
        "phone",
        "email_confirm",
        "phone_confirm",
        "user_metadata",
        "app_metadata",
    ):
        if optional_key in payload:
            user_data[optional_key] = payload[optional_key]

    return user_data, None


def parse_pagination_params():
    page, page_error = parse_positive_int_query_param("page")
    if page_error:
        return None, None, page_error

    per_page, per_page_error = parse_positive_int_query_param("per_page")
    if per_page_error:
        return None, None, per_page_error

    return page, per_page, None


def parse_positive_int_query_param(name):
    raw_value = request.args.get(name)
    if raw_value in (None, ""):
        return None, None

    try:
        value = int(raw_value)
    except ValueError:
        return None, f"{name} must be a positive integer"

    if value < 1:
        return None, f"{name} must be a positive integer"
    return value, None


def parse_bool_query_param(name):
    raw_value = (request.args.get(name) or "").strip().lower()
    return raw_value in {"1", "true", "yes"}
