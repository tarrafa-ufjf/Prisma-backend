from __future__ import annotations

import re
from typing import Any, ClassVar

import sqlglot
from crewai_tools import NL2SQLTool
from sqlglot import exp


FORBIDDEN_TABLES: frozenset[str] = frozenset(
    {"configs", "user", "role", "roles_users", "role_users"}
)


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip().strip('"').strip("`").lower()


def referenced_forbidden_tables(sql_query: str) -> set[str]:
    references: set[str] = set()
    try:
        statements = sqlglot.parse(sql_query, dialect="postgres")
    except sqlglot.errors.ParseError:
        statements = []

    for statement in statements:
        if statement is None:
            continue
        for table in statement.find_all(exp.Table):
            name = _normalize_identifier(table.name)
            if name in FORBIDDEN_TABLES:
                references.add(name)

    if references:
        return references

    pattern = r"\b(?:from|join|update|into|table)\s+\"?([a-zA-Z_][\w]*)\"?"
    for match in re.finditer(pattern, sql_query, flags=re.IGNORECASE):
        name = _normalize_identifier(match.group(1))
        if name in FORBIDDEN_TABLES:
            references.add(name)

    return references


class IndicatorsNL2SQLTool(NL2SQLTool):
    forbidden_tables: ClassVar[frozenset[str]] = FORBIDDEN_TABLES

    def _fetch_available_tables(self) -> list[dict[str, Any]] | str:
        placeholders = ", ".join(f"'{table}'" for table in sorted(self.forbidden_tables))
        return self.execute_sql(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' "
            f"AND table_name NOT IN ({placeholders}) "
            "ORDER BY table_name;"
        )

    def _fetch_all_available_columns(
        self, table_name: str
    ) -> list[dict[str, Any]] | str:
        normalized_table_name = _normalize_identifier(table_name)
        if normalized_table_name in self.forbidden_tables:
            return []

        return self.execute_sql(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :table_name "
            "ORDER BY ordinal_position",
            params={"table_name": normalized_table_name},
        )

    def execute_sql(
        self,
        sql_query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]] | str:
        forbidden_references = referenced_forbidden_tables(sql_query)
        if forbidden_references:
            tables = ", ".join(sorted(forbidden_references))
            raise ValueError(f"consulta bloqueada para tabelas proibidas: {tables}")

        return super().execute_sql(sql_query, params=params)
