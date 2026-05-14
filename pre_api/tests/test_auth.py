import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PRE_API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PRE_API_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PRE_API_DIR) not in sys.path:
    sys.path.insert(0, str(PRE_API_DIR))

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SECURITY_PASSWORD_SALT"] = "test-password-salt"
os.environ["AUTH_AUTO_CREATE_TABLES"] = "true"

import app as app_module
from auth import create_local_user, ensure_roles
from database import db


class AuthSessionTest(unittest.TestCase):
    def setUp(self):
        self.app_module = app_module
        self.app = app_module.app
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            ensure_roles()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def create_user(self, email="user@example.com", password="secret123", roles=None):
        with self.app.app_context():
            user = create_local_user(email, password, role_names=roles)
            return user.id

    def login(self, email="user@example.com", password="secret123"):
        return self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )

    def test_protected_api_without_session_returns_401(self):
        response = self.client.get("/subjects")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "authentication required"})

    def test_login_succeeds_and_sets_session_cookie(self):
        self.create_user()

        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertIn("session=", response.headers.get("Set-Cookie", ""))
        self.assertEqual(response.get_json()["user"]["email"], "user@example.com")

    def test_login_rejects_invalid_password(self):
        self.create_user()

        response = self.login(password="wrong")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "invalid email or password"})

    def test_me_returns_current_user_when_logged_in(self):
        self.create_user()
        self.login()

        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["email"], "user@example.com")

    def test_logout_invalidates_session(self):
        self.create_user()
        self.login()

        logout_response = self.client.post("/auth/logout")
        me_response = self.client.get("/auth/me")

        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(me_response.status_code, 401)
        self.assertEqual(me_response.get_json(), {"error": "authentication required"})

    def test_valid_session_allows_protected_request(self):
        self.create_user()
        self.login()

        with patch("routes.student_routes.build_all_subjects", return_value=[{"id": 1}]):
            response = self.client.get("/subjects")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"data": [{"id": 1}]})

    def test_options_request_bypasses_auth(self):
        response = self.client.open("/subjects", method="OPTIONS")

        self.assertEqual(response.status_code, 200)

    def test_root_route_remains_public(self):
        response = self.client.get("/")

        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()

    def test_non_admin_cannot_create_user(self):
        self.create_user()
        self.login()

        response = self.client.post(
            "/auth/users",
            json={"email": "new@example.com", "password": "secret123"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "admin role required"})

    def test_admin_can_create_user(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        self.login(email="admin@example.com")

        response = self.client.post(
            "/auth/users",
            json={
                "email": "new@example.com",
                "password": "secret123",
                "roles": ["user"],
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json()["user"],
            {
                "id": 2,
                "email": "new@example.com",
                "active": True,
                "roles": ["user"],
            },
        )

    def test_admin_can_list_users(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        active_user_id = self.create_user(email="user@example.com")
        inactive_user_id = self.create_user(email="inactive@example.com")
        self.login(email="admin@example.com")
        self.client.delete(f"/auth/users/{inactive_user_id}")

        response = self.client.get("/auth/users?page=1&per_page=10")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual([user["email"] for user in payload["users"]], ["admin@example.com", "user@example.com"])
        self.assertEqual([user["id"] for user in payload["users"]], [1, active_user_id])

    def test_list_users_validates_pagination(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        self.login(email="admin@example.com")

        response = self.client.get("/auth/users?page=0")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "page must be a positive integer"})

    def test_admin_can_update_user(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        target_id = self.create_user(email="user@example.com")
        self.login(email="admin@example.com")

        response = self.client.patch(
            f"/auth/users/{target_id}",
            json={
                "email": "updated@example.com",
                "roles": ["admin"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["user"],
            {
                "id": target_id,
                "email": "updated@example.com",
                "active": True,
                "roles": ["admin"],
            },
        )

        self.client.post("/auth/logout")
        old_login_response = self.login(email="updated@example.com", password="secret123")

        self.assertEqual(old_login_response.status_code, 200)

    def test_update_user_rejects_unsupported_fields(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        target_id = self.create_user(email="user@example.com")
        self.login(email="admin@example.com")

        response = self.client.patch(
            f"/auth/users/{target_id}",
            json={"active": False, "password": "newsecret123"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "unsupported fields: active, password"})

    def test_update_user_only_accepts_patch(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        target_id = self.create_user(email="user@example.com")
        self.login(email="admin@example.com")

        response = self.client.put(
            f"/auth/users/{target_id}",
            json={"email": "updated@example.com"},
        )

        self.assertEqual(response.status_code, 405)

    def test_update_user_requires_admin(self):
        target_id = self.create_user(email="target@example.com")
        self.create_user(email="user@example.com")
        self.login(email="user@example.com")

        response = self.client.patch(
            f"/auth/users/{target_id}",
            json={"email": "updated@example.com"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "admin role required"})

    def test_update_user_returns_404_for_missing_user(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        self.login(email="admin@example.com")

        response = self.client.patch(
            "/auth/users/999",
            json={"email": "updated@example.com"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "user not found"})

    def test_admin_can_deactivate_user(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        target_id = self.create_user(email="user@example.com")
        self.login(email="admin@example.com")

        response = self.client.delete(f"/auth/users/{target_id}")

        self.assertEqual(response.status_code, 204)
        users_response = self.client.get("/auth/users")
        users = {user["email"]: user for user in users_response.get_json()["users"]}
        self.assertNotIn("user@example.com", users)

    def test_delete_user_requires_admin(self):
        target_id = self.create_user(email="target@example.com")
        self.create_user(email="user@example.com")
        self.login(email="user@example.com")

        response = self.client.delete(f"/auth/users/{target_id}")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "admin role required"})


if __name__ == "__main__":
    unittest.main()
