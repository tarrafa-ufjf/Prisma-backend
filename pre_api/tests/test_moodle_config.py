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
os.environ["MOODLE_CONFIG_ENCRYPTION_KEY"] = "test-moodle-config-encryption-key"

import app as app_module
from auth import create_local_user, ensure_roles
from database import DatabaseAdmin, db
from src.analysis_lib.config_crypto import ENCRYPTED_VALUE_PREFIX


class MoodleConfigTest(unittest.TestCase):
    def setUp(self):
        self.app_module = app_module
        self.app = app_module.app
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.configs_table = DatabaseAdmin().get_configs_table()
            self.configs_table.drop(db.engine, checkfirst=True)
            self.configs_table.create(db.engine, checkfirst=True)
            DatabaseAdmin._engine = db.engine
            ensure_roles()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            self.configs_table.drop(db.engine, checkfirst=True)
            db.drop_all()
            DatabaseAdmin._engine = None

    def create_user(self, email="user@example.com", password="secret123", roles=None):
        with self.app.app_context():
            user = create_local_user(email, password, role_names=roles)
            return user.id

    def login(self, email="user@example.com", password="secret123"):
        return self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )

    def login_admin(self):
        self.create_user(email="admin@example.com", roles=["admin"])
        self.login(email="admin@example.com")

    def save_config(self, version="3.1"):
        DatabaseAdmin().insert_version_in_database(
            1,
            version,
            {
                "host": "moodle-db",
                "port": 3306,
                "database": "moodle",
                "user": "moodle_user",
                "password": "secret",
            },
        )

    def valid_payload(self):
        return {
            "host": "moodle-db",
            "port": 3306,
            "database": "moodle",
            "user": "moodle_user",
            "password": "secret",
        }

    def test_non_admin_cannot_access_moodle_config(self):
        self.create_user()
        self.login()

        response = self.client.get("/admin/moodle-config")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "admin role required"})

    def test_admin_get_moodle_config_without_config_returns_404(self):
        self.login_admin()

        response = self.client.get("/admin/moodle-config")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "moodle config not found"})

    def test_admin_get_moodle_config_never_exposes_password(self):
        self.login_admin()
        self.save_config()

        response = self.client.get("/admin/moodle-config")

        self.assertEqual(response.status_code, 200)
        config = response.get_json()["config"]
        self.assertNotIn("password", config)
        self.assertEqual(
            config,
            {
                "host": "moodle-db",
                "port": 3306,
                "database": "moodle",
                "user": "moodle_user",
                "version": "3.1",
                "has_password": True,
            },
        )

    def test_admin_put_moodle_config_validates_required_fields(self):
        self.login_admin()

        response = self.client.put("/admin/moodle-config", json={"host": "moodle-db"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("missing required fields", response.get_json()["error"])

    def test_admin_put_moodle_config_invalid_connection_does_not_save(self):
        self.login_admin()

        with patch(
            "services.moodle_config_service.detect_moodle_version",
            side_effect=RuntimeError("connection refused"),
        ):
            response = self.client.put("/admin/moodle-config", json=self.valid_payload())

        self.assertEqual(response.status_code, 400)
        self.assertIn("could not connect", response.get_json()["error"])
        self.assertIsNone(DatabaseAdmin().get_db_config_from_database(1))

    def test_admin_put_moodle_config_saves_without_exposing_password(self):
        self.login_admin()

        with patch("services.moodle_config_service.detect_moodle_version", return_value="3.1"):
            response = self.client.put("/admin/moodle-config", json=self.valid_payload())

        self.assertEqual(response.status_code, 200)
        config = response.get_json()["config"]
        self.assertNotIn("password", config)
        self.assertEqual(config["version"], "3.1")
        self.assertTrue(config["has_password"])
        self.assertEqual(DatabaseAdmin().get_db_config_from_database(1)["password"], "secret")
        with self.app.app_context():
            with db.engine.connect() as conn:
                raw_password = conn.execute(self.configs_table.select()).mappings().first()["password"]
        self.assertNotEqual(raw_password, "secret")
        self.assertTrue(raw_password.startswith(ENCRYPTED_VALUE_PREFIX))

    def test_saved_plaintext_moodle_config_remains_readable(self):
        with self.app.app_context():
            with db.engine.begin() as conn:
                conn.execute(
                    self.configs_table.insert().values(
                        institution_id=1,
                        version="3.1",
                        host="moodle-db",
                        port=3306,
                        database="moodle",
                        user="moodle_user",
                        password="legacy-secret",
                    )
                )

        config = DatabaseAdmin().get_db_config_from_database(1)

        self.assertEqual(config["password"], "legacy-secret")

    def test_admin_can_test_moodle_config_without_saving(self):
        self.login_admin()

        with patch("services.moodle_config_service.detect_moodle_version", return_value="3.1"):
            response = self.client.post("/admin/moodle-config/test", json=self.valid_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True, "version": "3.1"})
        self.assertIsNone(DatabaseAdmin().get_db_config_from_database(1))

    def test_analysis_without_saved_config_returns_400(self):
        self.create_user()
        self.login()

        response = self.client.put("/analysis", json={"channel": "diario"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "moodle config not found"})

    def test_analysis_uses_saved_config_instead_of_payload_config(self):
        self.create_user()
        self.login()
        self.save_config(version="3.1")

        with patch("app.Processor") as processor_cls:
            processor = processor_cls.return_value
            processor.get_version.return_value = "3.1"

            response = self.client.put(
                "/analysis",
                json={
                    "channel": "semanal",
                    "host": "ignored-host",
                    "port": 9999,
                    "database": "ignored",
                    "user": "ignored",
                    "password": "ignored",
                },
            )

        self.assertEqual(response.status_code, 200)
        saved_config = DatabaseAdmin().get_db_config_from_database(1)
        processor.set_subjects_analysis.assert_called_once_with(
            db_config=saved_config,
            channel="semanal",
        )

    def test_scheduler_uses_saved_config(self):
        self.save_config(version="3.1")

        with patch("app.Processor") as processor_cls:
            processor = processor_cls.return_value
            processor.get_version.return_value = "3.1"

            self.app_module.run_scheduled_analysis(channel="mensal")

        saved_config = DatabaseAdmin().get_db_config_from_database(1)
        processor.set_subjects_analysis.assert_called_once_with(
            db_config=saved_config,
            channel="mensal",
        )


if __name__ == "__main__":
    unittest.main()
