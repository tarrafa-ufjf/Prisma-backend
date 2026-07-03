from __future__ import annotations

import logging
import os
from urllib.parse import quote_plus

from services.moodle_config_service import get_saved_moodle_config

log = logging.getLogger(__name__)


def build_db_uri() -> str:
    configured_uri = os.getenv("NL2SQL_DB_URI")
    if configured_uri:
        return configured_uri

    try:
        config = get_saved_moodle_config()
    except Exception as exc:
        log.warning(f"Falha ao ler configuracao Moodle salva para NL2SQL: {exc}")
        config = None

    if config is None:
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_DATABASE")
    else:
        host = config.get("host")
        port = config.get("port")
        user = config.get("user")
        password = config.get("password")
        database = config.get("database")

    missing = [
        name
        for name, value in {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
        }.items()
        if value in (None, "")
    ]
    if missing:
        print("missing:", missing)
        raise RuntimeError(
            "configuracao Moodle ausente para NL2SQL: "
            + ", ".join(sorted(missing))
        )

    return (
         f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
    )