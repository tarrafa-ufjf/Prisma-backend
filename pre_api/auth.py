import os

from flask import g, jsonify, request
import requests


AUTH_EXEMPT_PATHS = {"/"}
AUTH_REQUEST_TIMEOUT = 5


class AuthConfigError(Exception):
    pass


class AuthError(Exception):
    def __init__(self, message):
        self.message = message


class AuthServiceError(Exception):
    pass


def requires_auth():
    if request.method == "OPTIONS":
        return False
    return request.path not in AUTH_EXEMPT_PATHS


def authenticate_request():
    if not requires_auth():
        return None

    try:
        claims = verify_request_token()
    except AuthConfigError:
        return jsonify({"error": "authentication is not configured"}), 500
    except AuthServiceError:
        return jsonify({"error": "authentication service unavailable"}), 503
    except AuthError as exc:
        return jsonify({"error": exc.message}), 401

    g.auth_claims = claims
    g.current_user = {
        "id": claims.get("sub"),
        "email": claims.get("email"),
    }
    return None


def verify_request_token():
    authorization = request.headers.get("Authorization", "")
    token = extract_bearer_token(authorization)
    return get_supabase_user(token)


def extract_bearer_token(authorization):
    if not authorization:
        raise AuthError("missing bearer token")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AuthError("invalid authorization header")

    return parts[1]


def get_supabase_user(token):
    config = get_supabase_auth_config()
    try:
        response = requests.get(
            config["user_url"],
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": config["api_key"],
            },
            timeout=AUTH_REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise AuthServiceError() from exc

    if response.status_code in (401, 403):
        raise AuthError("invalid or expired token")
    if not response.ok:
        raise AuthServiceError()

    try:
        user = response.json()
    except ValueError as exc:
        raise AuthServiceError() from exc

    if not user.get("id"):
        raise AuthError("invalid or expired token")

    return {
        "sub": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "user": user,
    }


def get_supabase_auth_config():
    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    api_key = (
        os.getenv("SUPABASE_API_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or ""
    ).strip()

    if not supabase_url or not api_key:
        raise AuthConfigError()

    return {
        "api_key": api_key,
        "user_url": f"{supabase_url}/auth/v1/user",
    }
