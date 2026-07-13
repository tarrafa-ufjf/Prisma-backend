import logging
import os
from typing import Dict, Any

from database import db
from services.chatbot.memory import (
    ChatbotMemoryError,
    add_assistant_message,
    add_user_message,
    format_messages_for_rewrite,
    get_or_create_conversation,
    get_recent_messages,
)
from services.chatbot.rewrite import rewrite_question_with_memory
from services.nl2sql_pipeline import run_nl2sql_pipeline

log = logging.getLogger(__name__)


def _debug_response_enabled() -> bool:
    return os.getenv("CHATBOT_DEBUG_RESPONSE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def build_chatbot_response(
    user_question: str,
    user_id: int | None = None,
    conversation_id: int | None = None,
) -> Dict[str, Any]:

    try:
        if not user_question or not user_question.strip():
            return {
                "success": False,
                "error": "question is required",
            }

        log.info(f"Pergunta recebida: {user_question}")

        conversation = None
        rewritten_question = user_question
        if user_id is not None:
            conversation = get_or_create_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                question=user_question,
            )
            recent_messages = get_recent_messages(conversation.id)
            conversation_context = format_messages_for_rewrite(recent_messages)
            rewritten_question = rewrite_question_with_memory(
                user_question,
                conversation_context,
            )
            add_user_message(
                conversation_id=conversation.id,
                question=user_question,
                rewritten_question=rewritten_question,
            )
            db.session.flush()

        result = run_nl2sql_pipeline(rewritten_question)

        response: Dict[str, Any] = {
            "success": True,
            "conversation_id": conversation.id if conversation is not None else conversation_id,
            "question": user_question,
            "rewritten_question": rewritten_question,
            "answer": result.get("final_answer"),
            "json": result.get("final_json"),
            "vega": result.get("vega"),
        }

        if conversation is not None:
            add_assistant_message(
                conversation_id=conversation.id,
                answer=result.get("final_answer"),
                sql=result.get("sql"),
                result_json=result.get("final_json"),
                metadata={
                    "confidence": result.get("confidence"),
                    "adjudication": result.get("adjudication"),
                },
            )
            db.session.commit()

        if _debug_response_enabled():
            response["debug"] = {
                "vega": result.get("vega"),
                "sql": result.get("sql"),
                "confidence": result.get("confidence"),
                "candidate_sqls": result.get("candidate_sqls"),
                "adjudication": result.get("adjudication"),
            }

        return response

    except ChatbotMemoryError as e:
        db.session.rollback()
        return {
            "success": False,
            "error": e.message,
        }
    except Exception as e:
        db.session.rollback()
        log.error(f"Erro no chatbot: {e}")

        return {
            "success": False,
            "error": str(e),
        }
