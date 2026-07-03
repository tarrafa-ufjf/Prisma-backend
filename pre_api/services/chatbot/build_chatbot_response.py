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


def _clean_crew_output(data: Any) -> Any:
    """
    Limpa qualquer objeto do CrewAI transformando-o em tipos nativos do Python 
    (para evitar erros de serialização no msgpack).
    """
    if data is None:
        return None
    
    # Se for um output do CrewAI que gerou um JSON estruturado
    if hasattr(data, 'json_dict') and data.json_dict:
        return data.json_dict
        
    # Se tiver a string bruta do output
    if hasattr(data, 'raw'):
        return data.raw
        
    # Se já for um tipo nativo básico, retorna como está
    if isinstance(data, (str, int, float, bool, list, dict)):
        return data
        
    # Último recurso: força para string para evitar vazamento de objetos
    return str(data)


def build_chatbot_response(user_question: str) -> Dict[str, Any]:

    try:
        log.info(f"Pergunta recebida: {user_question}")

        result = run_nl2sql_pipeline(user_question)

        # Aplicamos a função de limpeza em TODOS os retornos
        response: Dict[str, Any] = {
            "success": True,
            "question": user_question,
            "answer": _clean_crew_output(result.get("final_answer")),
            "json": _clean_crew_output(result.get("final_json")),
            "vega": _clean_crew_output(result.get("vega")),
        }

        if _debug_response_enabled():
            response["debug"] = {
                "vega": _clean_crew_output(result.get("vega")),
                "sql": _clean_crew_output(result.get("sql")),
                "confidence": _clean_crew_output(result.get("confidence")),
                "candidate_sqls": _clean_crew_output(result.get("candidate_sqls")),
                "adjudication": _clean_crew_output(result.get("adjudication")),
            }

        return response

    except Exception as e:
        log.error(f"Erro no chatbot: {e}")

        return {
            "success": False,
            "error": str(e),
        }