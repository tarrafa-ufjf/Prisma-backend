from flask import Blueprint, request, jsonify
from flask_login import current_user

from services.chatbot.build_chatbot_response import build_chatbot_response
from services.chatbot.memory import (
    ChatbotMemoryError,
    list_user_conversations,
    require_user_conversation,
    serialize_conversation,
    serialize_conversation_with_messages,
)

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json(silent=True) or {}
    question = data.get("question")
    conversation_id, error = _parse_optional_positive_int(data.get("conversation_id"))
    if error:
        return jsonify({"error": error}), 400

    result = build_chatbot_response(
        question,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )

    return jsonify(result)


@chatbot_bp.route("/chatbot/conversations", methods=["GET"])
def list_chatbot_conversations():
    conversations = list_user_conversations(current_user.id)
    return jsonify(
        {
            "conversations": [
                serialize_conversation(conversation)
                for conversation in conversations
            ]
        }
    ), 200


@chatbot_bp.route("/chatbot/conversations/<int:conversation_id>", methods=["GET"])
def get_chatbot_conversation(conversation_id):
    try:
        conversation = require_user_conversation(current_user.id, conversation_id)
    except ChatbotMemoryError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify(
        {"conversation": serialize_conversation_with_messages(conversation)}
    ), 200


def _parse_optional_positive_int(value):
    if value in (None, ""):
        return None, None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, "conversation_id must be a positive integer"
    if parsed < 1:
        return None, "conversation_id must be a positive integer"
    return parsed, None
