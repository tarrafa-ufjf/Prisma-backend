from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def env_flag(name: str, default: str = "") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def normalize_gemini_model(model: str) -> str:
    normalized = model.strip()
    if normalized.startswith("models/"):
        normalized = normalized.removeprefix("models/")
    if normalized.startswith("gemini/"):
        return normalized
    return f"gemini/{normalized}"


N_EXECUTIONS = int(os.getenv("NL2SQL_N_EXECUTIONS", "1"))
MODEL = normalize_gemini_model(
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
)
API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
)
SQL_DIALECT = os.getenv("NL2SQL_DIALECT", "postgres")
MAX_WORKERS = int(os.getenv("NL2SQL_MAX_WORKERS", str(N_EXECUTIONS)))
SAMPLE_ROWS_IN_TABLE_INFO = int(os.getenv("NL2SQL_SAMPLE_ROWS", "3"))

GENERATE_VEGA = env_flag("NL2SQL_GENERATE_VEGA", "true")
VEGA_MAX_ROWS = int(os.getenv("NL2SQL_VEGA_MAX_ROWS", "100"))
VEGA_LITE_SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json"
