import logging

from database import Database, DatabaseAdmin
from src.analysis_lib.analysis.analyzer import Analyzer


INSTITUTION_ID = 1
REQUIRED_CONFIG_FIELDS = ("host", "port", "database", "user")
MOODLE_CONNECTION_ERROR_MESSAGE = "could not connect to moodle database"
logger = logging.getLogger(__name__)


class MoodleConfigError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code


def serialize_moodle_config(config):
    if config is None:
        return None

    return {
        "host": config.get("host"),
        "port": config.get("port"),
        "database": config.get("database"),
        "user": config.get("user"),
        "version": config.get("version"),
        "has_password": bool(config.get("password")),
    }


def get_saved_moodle_config(institution_id=INSTITUTION_ID):
    return DatabaseAdmin().get_db_config_from_database(institution_id)


def require_saved_moodle_config(institution_id=INSTITUTION_ID):
    config = get_saved_moodle_config(institution_id)
    if config is None:
        raise MoodleConfigError("moodle config not found", 400)
    return config


def build_config_from_payload(payload):
    payload = payload or {}
    config = {}
    missing = []

    for field in REQUIRED_CONFIG_FIELDS:
        value = payload.get(field)
        if isinstance(value, str):
            value = value.strip()
        if value in (None, ""):
            missing.append(field)
        else:
            config[field] = value

    raw_port = config.get("port")
    if raw_port not in (None, ""):
        try:
            config["port"] = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise MoodleConfigError("port must be an integer") from exc

        if config["port"] < 1 or config["port"] > 65535:
            raise MoodleConfigError("port must be between 1 and 65535")

    password = payload.get("password")
    if isinstance(password, str):
        password = password.strip()

    if password:
        config["password"] = password
    else:
        missing.append("password")

    if missing:
        raise MoodleConfigError(f"missing required fields: {', '.join(sorted(set(missing)))}")

    return config


def detect_moodle_version(config):
    connector = None
    try:
        connector = Database().get_connection_with_config(config)
        return Analyzer().get_moodle_version(connector)
    finally:
        if connector is not None:
            connector.close()


def test_moodle_config(payload):
    config = build_config_from_payload(payload)
    try:
        version = detect_moodle_version(config)
    except Exception as exc:
        logger.exception("could not connect to moodle database")
        raise MoodleConfigError(MOODLE_CONNECTION_ERROR_MESSAGE) from exc

    return version, config


def save_moodle_config(payload, institution_id=INSTITUTION_ID):
    db_admin = DatabaseAdmin()
    version, config = test_moodle_config(payload)
    db_admin.insert_version_in_database(institution_id, version, config)
    saved_config = db_admin.get_db_config_from_database(institution_id)
    return saved_config
