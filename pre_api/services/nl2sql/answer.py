from __future__ import annotations

import json
from typing import Any

from crewai import Agent, Crew, LLM, Task

from services.nl2sql.prompts import INDICATORS_RULES


def generate_final_answer(
    user_question: str,
    winner_sql: str,
    final_json: list[dict[str, Any]],
    llm: LLM,
    original_question: str | None = None,
) -> str:
    final_prompt = build_final_answer_prompt(
        user_question=user_question,
        winner_sql=winner_sql,
        final_json=final_json,
        original_question=original_question,
    )

    agent = Agent(
        role="Data Analyst",
        goal="Responder perguntas sobre indicadores educacionais usando resultados SQL já executados",
        backstory=INDICATORS_RULES,
        llm=llm,
        verbose=True,
    )

    task = Task(
        description=final_prompt,
        expected_output="Resposta curta e direta no mesmo idioma da pergunta original do usuário",
        agent=agent,
    )

    return str(
        Crew(
            agents=[agent],
            tasks=[task],
        ).kickoff()
    )


def build_final_answer_prompt(
    user_question: str,
    winner_sql: str,
    final_json: list[dict[str, Any]],
    original_question: str | None = None,
) -> str:
    response_language_question = original_question or user_question
    return f"""
    Pergunta original do usuário, usada para definir o idioma da resposta:
    {response_language_question}

    Pergunta usada internamente para gerar o SQL:
    {user_question}

    SQL vencedor selecionado por adjudicação técnica:
    ```sql
    {winner_sql}
    ```

    Resultado real do SQL, já executado pelo backend:
    ```json
    {json.dumps(final_json, ensure_ascii=False)}
    ```

    Responda apenas com uma explicação curta e direta no mesmo idioma da pergunta original do usuário.
    Não responda em português apenas porque as instruções internas ou o schema estão em português.
    Se a pergunta original estiver em inglês, responda em inglês. Se estiver em espanhol, responda em espanhol.
    Para qualquer outro idioma, use esse mesmo idioma original.
    Use exclusivamente os dados do JSON acima. Se o JSON estiver vazio, informe que nada foi encontrado.
    """
