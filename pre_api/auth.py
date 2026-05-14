import os

from flask import g, jsonify, request
from flask_login import current_user
from flask_security import SQLAlchemyUserDatastore, Security
from flask_security.utils import hash_password
from sqlalchemy.exc import IntegrityError

from database import db
from models import Role, User


AUTH_EXEMPT_PATHS = {"/", "/auth/login"}
DEFAULT_USER_ROLE = "user"
ADMIN_ROLE = "admin"
UNSET = object()

security = Security()
user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class AuthError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code


def init_auth(app):
    security.init_app(app, user_datastore)


def initialize_auth_storage(app):
    with app.app_context():
        db.create_all()
        ensure_roles()
        seed_admin_from_env()
        db.session.commit()


def ensure_roles():
    for role_name in (ADMIN_ROLE, DEFAULT_USER_ROLE):
        if user_datastore.find_role(role_name) is None:
            user_datastore.create_role(name=role_name)


def seed_admin_from_env():
    email = (os.getenv("AUTH_ADMIN_EMAIL") or "").strip()
    password = os.getenv("AUTH_ADMIN_PASSWORD") or ""
    if not email or not password or user_datastore.find_user(email=email):
        return

    user_datastore.create_user(
        email=email,
        password=hash_password(password),
        active=True,
        roles=[ADMIN_ROLE],
    )


def requires_auth():
    if request.method == "OPTIONS":
        return False
    return request.path not in AUTH_EXEMPT_PATHS


def authenticate_request():
    if not requires_auth():
        return None

    if not current_user.is_authenticated:
        return jsonify({"error": "authentication required"}), 401

    g.current_user = serialize_user(current_user)
    g.auth_claims = {
        "sub": str(current_user.id),
        "email": current_user.email,
        "roles": get_user_role_names(current_user),
    }
    return None


def serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "active": bool(user.active),
        "roles": get_user_role_names(user),
    }


def get_user_role_names(user):
    return sorted(role.name for role in getattr(user, "roles", []) if role.name)


def is_admin_user(user):
    return ADMIN_ROLE in get_user_role_names(user)


def require_admin_user():
    if not current_user.is_authenticated:
        return jsonify({"error": "authentication required"}), 401
    if not is_admin_user(current_user):
        return jsonify({"error": "admin role required"}), 403
    return None


def create_local_user(email, password, role_names=None, active=True):
    resolved_email = (email or "").strip()
    if not resolved_email:
        raise AuthError("email is required")
    if not password:
        raise AuthError("password is required")

    roles = normalize_role_names(role_names)
    ensure_roles_exist(roles)

    try:
        user = user_datastore.create_user(
            email=resolved_email,
            password=hash_password(password),
            active=bool(active),
            roles=roles,
        )
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise AuthError("email already exists", 409) from exc

    return user


def list_local_users(page=None, per_page=None):
    query = User.query.filter(User.active.is_(True)).order_by(User.id)
    if page is not None or per_page is not None:
        resolved_page = page or 1
        resolved_per_page = per_page or 25
        pagination = query.paginate(
            page=resolved_page,
            per_page=resolved_per_page,
            error_out=False,
        )
        return {
            "users": [serialize_user(user) for user in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }

    return {"users": [serialize_user(user) for user in query.all()]}


def deactivate_local_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise AuthError("user not found", 404)

    user.active = False
    db.session.commit()
    return user


def update_local_user(
    user_id,
    email=UNSET,
    role_names=UNSET,
):
    user = db.session.get(User, user_id)
    if user is None:
        raise AuthError("user not found", 404)

    if all(value is UNSET for value in (email, role_names)):
        raise AuthError("no editable fields provided")

    if email is not UNSET:
        resolved_email = (email or "").strip()
        if not resolved_email:
            raise AuthError("email is required")
        user.email = resolved_email

    if role_names is not UNSET:
        roles = normalize_role_names(role_names)
        ensure_roles_exist(roles)
        user.roles = [user_datastore.find_role(role_name) for role_name in roles]

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise AuthError("email already exists", 409) from exc

    return user


def normalize_role_names(role_names):
    if role_names is None:
        return [DEFAULT_USER_ROLE]
    if isinstance(role_names, str):
        role_names = [role_names]

    roles = []
    for role_name in role_names:
        normalized = (role_name or "").strip().lower()
        if normalized:
            roles.append(normalized)

    return sorted(set(roles)) or [DEFAULT_USER_ROLE]


def ensure_roles_exist(role_names):
    for role_name in role_names:
        if user_datastore.find_role(role_name) is None:
            user_datastore.create_role(name=role_name)
