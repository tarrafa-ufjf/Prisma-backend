from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text

from services.nl2sql.db import build_indicators_db_uri
from services.nl2sql.sql_processing import is_safe_sql, validate_sql
from services.nl2sql.tool import referenced_forbidden_tables


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def execute_sql_to_json(sql: str) -> list[dict[str, Any]]:
    safe, safe_reason = is_safe_sql(sql)
    valid, valid_reason = validate_sql(sql)
    if not safe or not valid:
        raise RuntimeError(
            "SQL vencedor nao pode ser executado: "
            f"safety={safe_reason}; validation={valid_reason}"
        )
    forbidden_references = referenced_forbidden_tables(sql)
    if forbidden_references:
        tables = ", ".join(sorted(forbidden_references))
        raise RuntimeError(f"SQL vencedor consulta tabelas proibidas: {tables}")

    engine = create_engine(build_indicators_db_uri())
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).mappings().all()
            return [_json_safe(dict(row)) for row in rows]
    finally:
        engine.dispose()
