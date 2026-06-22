import logging
import os
from typing import Dict, Any

from services.nl2sql_pipeline import run_nl2sql_pipeline

log = logging.getLogger(__name__)


def _debug_response_enabled() -> bool:
    return os.getenv("CHATBOT_DEBUG_RESPONSE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def build_chatbot_response(user_question: str) -> Dict[str, Any]:

    try:
        log.info(f"Pergunta recebida: {user_question}")

        result = run_nl2sql_pipeline(user_question)

        response: Dict[str, Any] = {
            "success": True,
            "question": user_question,
            "answer": result.get("final_answer"),
            "json": result.get("final_json"),
            "vega": result.get("vega"),
        }

        if _debug_response_enabled():
            response["debug"] = {
                "vega": result.get("vega"),
                "sql": result.get("sql"),
                "confidence": result.get("confidence"),
                "candidate_sqls": result.get("candidate_sqls"),
                "adjudication": result.get("adjudication"),
            }

        return response

    except Exception as e:
        log.error(f"Erro no chatbot: {e}")

        return {
            "success": False,
            "error": str(e),
        }
