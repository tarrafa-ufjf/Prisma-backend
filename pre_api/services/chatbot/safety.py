from __future__ import annotations

import re


FORBIDDEN_CHATBOT_TABLES = {"configs", "user", "role", "roles_users", "role_users"}

SENSITIVE_AUTH_REFUSAL = (
    "Não posso consultar dados de login, credenciais, senhas, emails de acesso "
    "ou usuários do sistema. Posso ajudar com perguntas sobre os indicadores "
    "educacionais disponíveis."
)


def get_chatbot_policy_refusal(question: str) -> str | None:
    normalized = _normalize(question)
    if not normalized:
        return None

    if _mentions_forbidden_table(normalized):
        return SENSITIVE_AUTH_REFUSAL

    if _asks_for_credentials_or_secrets(normalized):
        return SENSITIVE_AUTH_REFUSAL

    if _asks_for_system_login_email(normalized):
        return SENSITIVE_AUTH_REFUSAL

    return None


def _normalize(value: str) -> str:
    return " ".join((value or "").lower().split())


def _mentions_forbidden_table(value: str) -> bool:
    return any(
        re.search(rf"\b{re.escape(table)}\b", value)
        for table in FORBIDDEN_CHATBOT_TABLES
    )


def _asks_for_credentials_or_secrets(value: str) -> bool:
    sensitive_terms = (
        "senha",
        "password",
        "credencial",
        "credenciais",
        "credential",
        "credentials",
        "token",
        "secret",
        "segredo",
    )
    return any(term in value for term in sensitive_terms)


def _asks_for_system_login_email(value: str) -> bool:
    has_email = "email" in value or "e-mail" in value
    has_login_context = any(
        term in value
        for term in (
            "login",
            "logar",
            "acessar",
            "acesso",
            "sistema",
            "entrar",
            "sign in",
            "access",
            "account",
        )
    )
    return has_email and has_login_context
