from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import sqlglot
import sqlglot.errors
from sqlglot import exp
from sqlglot.optimizer import qualify

from services.nl2sql.config import SQL_DIALECT

log = logging.getLogger(__name__)

_BLOCKED_STATEMENT_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Delete,
    exp.Update,
    exp.Drop,
    exp.Alter,
    exp.Insert,
    exp.Create,
)


def is_safe_sql(sql: str, dialect: str = SQL_DIALECT) -> tuple[bool, str]:
    try:
        statements = sqlglot.parse(sql, dialect=dialect)
        for stmt in statements:
            if stmt is None:
                continue
            for blocked in _BLOCKED_STATEMENT_TYPES:
                if isinstance(stmt, blocked):
                    reason = f"Statement bloqueado: {type(stmt).__name__}"
                    log.warning(f"[SQLGlot/Safety] {reason} — SQL: {sql[:80]}")
                    return False, reason
        return True, "OK"
    except sqlglot.errors.ParseError as exc:
        return False, f"ParseError no safety check: {exc}"


def validate_sql(sql: str, dialect: str = SQL_DIALECT) -> tuple[bool, str]:
    try:
        stmts = sqlglot.parse(
            sql,
            dialect=dialect,
            error_level=sqlglot.ErrorLevel.RAISE,
        )
        if not stmts or all(s is None for s in stmts):
            return False, "Parse retornou resultado vazio"
        return True, "Válido"
    except sqlglot.errors.ParseError as exc:
        return False, str(exc)


def normalize_sql(sql: str, dialect: str = SQL_DIALECT) -> str:
    try:
        return sqlglot.transpile(sql, read=dialect, write=dialect, pretty=False)[0]
    except Exception as exc:
        log.debug(f"[SQLGlot/Normalize] Falha na normalização, usando original: {exc}")
        return sql


def sql_fingerprint(sql: str, dialect: str = SQL_DIALECT) -> str | None:
    try:
        ast = sqlglot.parse_one(sql, dialect=dialect)
        try:
            ast = qualify.qualify(ast)
        except Exception:
            pass
        for node in ast.walk():
            if isinstance(node, (exp.Literal, exp.Anonymous)):
                node.set("this", "?")
        return ast.sql(dialect=dialect)
    except Exception:
        return None


def process_sql(sql: str, dialect: str = SQL_DIALECT) -> dict[str, Any]:
    result: dict[str, Any] = {
        "original": sql,
        "safe": False,
        "valid": False,
        "normalized": sql,
        "fingerprint": None,
        "safe_reason": "",
        "valid_reason": "",
    }

    safe, safe_reason = is_safe_sql(sql, dialect)
    result["safe"] = safe
    result["safe_reason"] = safe_reason
    if not safe:
        return result

    valid, valid_reason = validate_sql(sql, dialect)
    result["valid"] = valid
    result["valid_reason"] = valid_reason
    if not valid:
        return result

    result["normalized"] = normalize_sql(sql, dialect)
    result["fingerprint"] = sql_fingerprint(result["normalized"], dialect)
    return result


def group_equivalent_sqls_ast(candidate_sqls: list[str], dialect: str = SQL_DIALECT) -> dict[int, list[str]]:
    fingerprint_map: dict[str, list[str]] = defaultdict(list)
    unparseable: list[str] = []

    for sql in candidate_sqls:
        fp = sql_fingerprint(sql, dialect)
        if fp is not None:
            fingerprint_map[fp].append(sql)
        else:
            unparseable.append(sql)

    groups: dict[int, list[str]] = {
        i: sqls for i, sqls in enumerate(fingerprint_map.values())
    }
    offset = len(groups)
    for j, sql in enumerate(unparseable):
        groups[offset + j] = [sql]

    log.info(
        f"[SQLGlot/AST-Group] {len(groups)} grupos de {len(candidate_sqls)} candidatos "
        f"({len(unparseable)} inparsáveis)"
    )
    return groups


def group_equivalent_sqls(candidate_sqls: list[str]) -> dict[int, list[str]]:
    if not candidate_sqls:
        return {}
    return group_equivalent_sqls_ast(candidate_sqls)
