from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user
from flask_security.utils import verify_password

from auth import (
    AuthError,
    create_local_user,
    deactivate_local_user,
    list_local_users,
    require_admin_user,
    serialize_user,
    user_datastore,
)


auth_bp = Blueprint("auth_routes", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200

    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    remember_me = payload.get("remember_me", False)

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = user_datastore.find_user(email=email)
    if user is None or not user.active or not verify_password(password, user.password):
        return jsonify({"error": "invalid email or password"}), 401

    login_user(user, remember=remember_me)
    return jsonify({"user": serialize_user(user)}), 200


@auth_bp.route("/logout", methods=["POST", "OPTIONS"])
def logout():
    if request.method == "OPTIONS":
        return "", 200

    logout_user()
    return "", 204


@auth_bp.route("/me", methods=["GET", "OPTIONS"])
def me():
    if request.method == "OPTIONS":
        return "", 200

    if not current_user.is_authenticated:
        return jsonify({"error": "authentication required"}), 401
    return jsonify({"user": serialize_user(current_user)}), 200


@auth_bp.route("/users", methods=["POST", "OPTIONS"])
def create_user():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    payload = request.get_json(silent=True) or {}
    try:
        user = create_local_user(
            payload.get("email"),
            payload.get("password"),
            role_names=payload.get("roles") or payload.get("role"),
            active=payload.get("active", True),
        )
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify({"user": serialize_user(user)}), 201


@auth_bp.route("/users", methods=["GET", "OPTIONS"])
def list_users():
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    page, per_page, validation_error = parse_pagination_params()
    if validation_error:
        return jsonify({"error": validation_error}), 400

    return jsonify(list_local_users(page=page, per_page=per_page)), 200


@auth_bp.route("/users/<int:user_id>", methods=["DELETE", "OPTIONS"])
def delete_user(user_id):
    if request.method == "OPTIONS":
        return "", 200

    admin_error_response = require_admin_user()
    if admin_error_response is not None:
        return admin_error_response

    try:
        deactivate_local_user(user_id)
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return "", 204


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
