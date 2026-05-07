from flask import Blueprint, g, jsonify, request

from auth import (
    AuthError,
    AuthServiceError,
    SupabaseAdminConfigError,
    SupabaseAdminError,
    create_supabase_auth_user,
    extract_bearer_token,
    get_current_profile,
    is_admin_profile,
)


auth_bp = Blueprint("auth_routes", __name__, url_prefix="/auth")


@auth_bp.route("/users", methods=["POST", "OPTIONS"])
def create_user():
    if request.method == "OPTIONS":
        return "", 200

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

