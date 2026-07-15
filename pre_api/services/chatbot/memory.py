from __future__ import annotations

from typing import Any

from sqlalchemy import desc
from sqlalchemy.sql import func

from database import db
from models import ChatbotConversation, ChatbotMessage


MAX_RESULT_ROWS_TO_STORE = 20


class ChatbotMemoryError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def _title_from_question(question: str) -> str:
    normalized = " ".join((question or "").split())
    if len(normalized) <= 80:
        return normalized
    return normalized[:77].rstrip() + "..."


def get_or_create_conversation(
    user_id: int,
    conversation_id: int | None,
    question: str,
) -> ChatbotConversation:
    if conversation_id is None:
        conversation = ChatbotConversation(
            user_id=user_id,
            title=_title_from_question(question),
        )
        db.session.add(conversation)
        db.session.flush()
        return conversation

    conversation = db.session.get(ChatbotConversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise ChatbotMemoryError("conversation not found", 404)
    return conversation


def list_user_conversations(user_id: int) -> list[ChatbotConversation]:
    return (
        ChatbotConversation.query.filter_by(user_id=user_id)
        .order_by(desc(ChatbotConversation.updated_at), desc(ChatbotConversation.id))
        .all()
    )


def require_user_conversation(
    user_id: int,
    conversation_id: int,
) -> ChatbotConversation:
    conversation = db.session.get(ChatbotConversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise ChatbotMemoryError("conversation not found", 404)
    return conversation


def delete_user_conversation(user_id: int, conversation_id: int) -> None:
    conversation = require_user_conversation(user_id, conversation_id)
    db.session.delete(conversation)
    db.session.commit()


def get_recent_messages(
    conversation_id: int,
    limit: int = 6,
) -> list[ChatbotMessage]:
    messages = (
        ChatbotMessage.query.filter_by(conversation_id=conversation_id)
        .order_by(desc(ChatbotMessage.created_at), desc(ChatbotMessage.id))
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


def get_conversation_messages(conversation_id: int) -> list[ChatbotMessage]:
    return (
        ChatbotMessage.query.filter_by(conversation_id=conversation_id)
        .order_by(ChatbotMessage.created_at, ChatbotMessage.id)
        .all()
    )


def add_user_message(
    conversation_id: int,
    question: str,
    rewritten_question: str | None,
) -> ChatbotMessage:
    message = ChatbotMessage(
        conversation_id=conversation_id,
        role="user",
        content=question,
        rewritten_question=rewritten_question,
    )
    db.session.add(message)
    return message


def add_assistant_message(
    conversation_id: int,
    answer: str | None,
    sql: str | None,
    result_json: list[dict[str, Any]] | None,
    metadata: dict[str, Any] | None = None,
    vega: dict[str, Any] | None = None,
) -> ChatbotMessage:
    message = ChatbotMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=answer or "",
        sql=sql,
        result_json=_compact_result_json(result_json),
        metadata_json=metadata or {},
    )
    db.session.add(message)
    conversation = db.session.get(ChatbotConversation, conversation_id)
    if conversation is not None:
        conversation.vega_json = vega
        conversation.updated_at = func.now()
    return message


def _compact_result_json(
    result_json: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if result_json is None:
        return None
    rows = result_json[:MAX_RESULT_ROWS_TO_STORE]
    return {
        "row_count": len(result_json),
        "rows": rows,
        "truncated": len(result_json) > MAX_RESULT_ROWS_TO_STORE,
    }


def format_messages_for_rewrite(messages: list[ChatbotMessage]) -> str:
    if not messages:
        return ""

    lines: list[str] = []
    for message in messages:
        if message.role == "user":
            lines.append(f"Usuário: {message.content}")
            if message.rewritten_question and message.rewritten_question != message.content:
                lines.append(f"Pergunta reescrita: {message.rewritten_question}")
        elif message.role == "assistant":
            if message.sql:
                lines.append(f"SQL anterior: {message.sql}")
            if message.content:
                lines.append(f"Assistente: {message.content}")

    return "\n".join(lines)


def serialize_conversation(
    conversation: ChatbotConversation,
    include_vega: bool = False,
) -> dict[str, Any]:
    payload = {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": _isoformat(conversation.created_at),
        "updated_at": _isoformat(conversation.updated_at),
    }
    if include_vega:
        payload["vega"] = conversation.vega_json
    return payload


def serialize_message(message: ChatbotMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "rewritten_question": message.rewritten_question,
        "sql": message.sql,
        "result_json": message.result_json,
        "metadata": message.metadata_json,
        "created_at": _isoformat(message.created_at),
    }


def serialize_conversation_with_messages(
    conversation: ChatbotConversation,
) -> dict[str, Any]:
    return {
        **serialize_conversation(conversation, include_vega=True),
        "messages": [
            serialize_message(message)
            for message in get_conversation_messages(conversation.id)
        ],
    }


def _isoformat(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()
