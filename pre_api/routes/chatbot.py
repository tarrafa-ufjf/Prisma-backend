from flask import Blueprint, request, jsonify
from services.chatbot.build_chatbot_response import build_chatbot_response

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    question = data.get("question")

    result = build_chatbot_response(question)

    return jsonify(result)