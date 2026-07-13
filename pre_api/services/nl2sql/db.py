from __future__ import annotations

import os
from urllib.parse import quote_plus


def build_indicators_db_uri() -> str:
    configured_uri = os.getenv("NL2SQL_DB_URI")
    if configured_uri:
        return configured_uri

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_DATABASE")

    missing = [
        name
        for name, value in {
            "DB_HOST": host,
            "DB_PORT": port,
            "DB_USER": user,
            "DB_PASSWORD": password,
            "DB_DATABASE": database,
        }.items()
        if value in (None, "")
    ]
    if missing:
        raise RuntimeError(
            "configuracao do banco de indicadores ausente para NL2SQL: "
            + ", ".join(sorted(missing))
        )

    return (
        f"postgresql+psycopg://{quote_plus(str(user))}:{quote_plus(str(password))}"
        f"@{host}:{int(port)}/{quote_plus(str(database))}"
    )
