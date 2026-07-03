from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def env_flag(name: str, default: str = "") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


N_EXECUTIONS = int(os.getenv("NL2SQL_N_EXECUTIONS", "5"))
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/openai/gpt-oss-120b")
API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "",
)
SQL_DIALECT = os.getenv("NL2SQL_DIALECT", "mysql")
MAX_WORKERS = int(os.getenv("NL2SQL_MAX_WORKERS", str(N_EXECUTIONS)))
SAMPLE_ROWS_IN_TABLE_INFO = int(os.getenv("NL2SQL_SAMPLE_ROWS", "3"))

GENERATE_VEGA = env_flag("NL2SQL_GENERATE_VEGA", "true")
VEGA_MAX_ROWS = int(os.getenv("NL2SQL_VEGA_MAX_ROWS", "100"))
VEGA_LITE_SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json"
