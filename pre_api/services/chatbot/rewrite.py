from __future__ import annotations

import logging

from crewai import Agent, Crew, LLM, Task

from services.nl2sql.config import API_KEY, MODEL
from services.nl2sql.prompts import INDICATORS_RULES

log = logging.getLogger(__name__)


def rewrite_question_with_memory(
    user_question: str,
    conversation_context: str,
) -> str:
    if not conversation_context.strip():
        return user_question
    if not API_KEY:
        return user_question

    prompt = f"""
    Reescreva a pergunta atual como uma pergunta independente para um sistema NL2SQL.

    CONTEXTO RECENTE DA CONVERSA:
    {conversation_context}

    PERGUNTA ATUAL:
    {user_question}

    REGRAS:
    - Retorne apenas a pergunta reescrita, sem markdown e sem explicação.
    - Preserve o idioma da pergunta atual.
    - Resolva referências como "isso", "eles", "por disciplina", "e os tutores?" usando o contexto.
    - Não invente filtros, nomes ou IDs que não estejam na pergunta atual ou no histórico.
    - Se a pergunta atual já for independente, retorne-a sem mudanças relevantes.
    - Mantenha termos compatíveis com o banco de indicadores.

    CONTEXTO DO BANCO:
    {INDICATORS_RULES}
    """

    try:
        llm = LLM(model=MODEL, api_key=API_KEY, temperature=0.0)
        agent = Agent(
            role="Conversation Context Rewriter",
            goal="Reescrever perguntas dependentes de contexto para perguntas independentes de NL2SQL",
            backstory=(
                "Você transforma perguntas curtas ou anafóricas em perguntas completas, "
                "preservando estritamente o que foi dito no histórico."
            ),
            llm=llm,
            verbose=False,
        )
        task = Task(
            description=prompt,
            expected_output="Apenas a pergunta independente reescrita",
            agent=agent,
        )
        rewritten = str(Crew(agents=[agent], tasks=[task]).kickoff()).strip()
        return _clean_rewritten_question(rewritten) or user_question
    except Exception as exc:
        log.warning(f"Falha ao reescrever pergunta com memória: {exc}")
        return user_question


def _clean_rewritten_question(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
    if (
        len(cleaned) >= 2
        and cleaned[0] in {'"', "'"}
        and cleaned[-1] == cleaned[0]
    ):
        cleaned = cleaned[1:-1].strip()
    return cleaned
