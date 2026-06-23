from __future__ import annotations

import json
from typing import Any

from crewai import Agent, Crew, LLM, Task

from services.nl2sql.prompts import MOODLE_RULES


def generate_final_answer(
    user_question: str,
    winner_sql: str,
    final_json: list[dict[str, Any]],
    llm: LLM,
) -> str:
    final_prompt = f"""
    Pergunta original do usuário: {user_question}

    SQL vencedor selecionado por adjudicação técnica:
    ```sql
    {winner_sql}
    ```

    Resultado real do SQL, já executado pelo backend:
    ```json
    {json.dumps(final_json, ensure_ascii=False)}
    ```

    Responda apenas com uma explicação curta e direta no mesmo idioma da pergunta.
    Use exclusivamente os dados do JSON acima. Se o JSON estiver vazio, informe que nada foi encontrado.
    """

    agent = Agent(
        role="Data Analyst",
        goal="Responder perguntas sobre o banco Moodle usando resultados SQL já executados",
        backstory=MOODLE_RULES,
        llm=llm,
        verbose=True,
    )

    task = Task(
        description=final_prompt,
        expected_output="Resposta curta e direta no mesmo idioma da pergunta",
        agent=agent,
    )

    return str(
        Crew(
            agents=[agent],
            tasks=[task],
        ).kickoff()
    )