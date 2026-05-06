import os
import requests
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


class AuthMiddlewareTest(unittest.TestCase):
    def setUp(self):
        os.environ["SUPABASE_URL"] = "https://example.supabase.co"
        os.environ["SUPABASE_API_KEY"] = "test-api-key"

        import app as app_module

        self.app_module = app_module
        self.client = app_module.app.test_client()

    def tearDown(self):
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_API_KEY", None)

    def test_protected_api_without_token_returns_401(self):
        response = self.client.get("/subjects")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "missing bearer token"})

    def test_malformed_authorization_header_returns_401(self):
        response = self.client.get("/subjects", headers={"Authorization": "Token abc"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "invalid authorization header"})

    def test_options_request_bypasses_auth(self):
        response = self.client.open("/subjects", method="OPTIONS")

        self.assertEqual(response.status_code, 200)

    def test_root_route_remains_public(self):
        response = self.client.get("/")

        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()

    def test_valid_token_verified_by_supabase_allows_request(self):
        user = {"sub": "user-123", "email": "user@example.com"}

        with patch("auth.get_supabase_user", return_value=user):
            with patch("routes.student_routes.build_all_subjects", return_value=[{"id": 1}]):
                response = self.client.get("/subjects", headers={"Authorization": "Bearer valid.jwt"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"data": [{"id": 1}]})

    def test_invalid_token_rejected_by_supabase_returns_401(self):
        class Response:
            status_code = 401
            ok = False

        with patch("auth.requests.get", return_value=Response()):
            response = self.client.get("/subjects", headers={"Authorization": "Bearer invalid.jwt"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "invalid or expired token"})

    def test_supabase_auth_unavailable_fails_closed(self):
        with patch("auth.requests.get", side_effect=requests.RequestException("boom")):
            response = self.client.get("/subjects", headers={"Authorization": "Bearer valid.jwt"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"error": "authentication service unavailable"})

    def test_missing_supabase_env_fails_closed(self):
        os.environ.pop("SUPABASE_URL", None)

        response = self.client.get("/subjects", headers={"Authorization": "Bearer token"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "authentication is not configured"})


if __name__ == "__main__":
    unittest.main()
