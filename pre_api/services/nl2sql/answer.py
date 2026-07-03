from __future__ import annotations

import json
from typing import Any

from crewai import Agent, Crew, LLM, Task


def _format_chat_history(messages: list[dict[str, Any]]) -> str:
    """Formata o histórico de mensagens para dar contexto ao gerador da resposta final."""
    if not messages or len(messages) <= 1:
        return "Nenhum histórico anterior."
        
    formatted_turns = []
    # Pegamos tudo menos a última mensagem (que é a pergunta atual)
    for msg in messages[:-1]:
        role = "Usuário" if msg.get("role") == "user" else "Assistente"
        content = msg.get("content", "")
        formatted_turns.append(f"{role}: {content}")
        
    return "\n".join(formatted_turns)


def generate_final_answer(
    user_question: str,
    messages: list[dict[str, Any]],  # 1. ADICIONADO O PARÂMETRO 'messages'
    winner_sql: str,
    final_json: list[dict[str, Any]],
    llm: LLM,
) -> str:
    
    # Formata o histórico recebido do LangGraph
    chat_history = _format_chat_history(messages)

    # 2. INJETADO O HISTÓRICO NO PROMPT PARA O AGENTE TER FLUIDEZ NA RESPOSTA
    final_prompt = f"""
    Histórico da conversa anterior (Contexto):
    {chat_history}

    Pergunta ATUAL do usuário: {user_question}

    SQL vencedor selecionado por adjudicação técnica:
    ```sql
    {winner_sql}
    ```

    Resultado real do SQL, já executado pelo backend:
    ```json
    {json.dumps(final_json, ensure_ascii=False)}
    ```

    Instruções de resposta:
    1. Responda com uma explicação curta e direta no mesmo idioma da pergunta.
    2. Use exclusivamente os dados do JSON acima. Se o JSON estiver vazio, informe educadamente que nada foi encontrado.
    3. Mantenha a fluidez da conversa: use o 'Histórico da conversa anterior' para entender referências (ex: se o usuário perguntou 'E qual a média deles?', você já sabe ao que 'deles' se refere e pode responder de forma natural).
    """

    agent = Agent(
        role="Data Analyst",
        goal="Responder perguntas sobre o banco usando resultados SQL já executados e mantendo o contexto da conversa",
        backstory="Você é um analista de dados que responde perguntas de negócio de forma fluida, clara e conversacional, baseando-se apenas nos resultados JSON reais fornecidos.",
        llm=llm,
        verbose=True
    )

    task = Task(
        description=final_prompt,
        expected_output="Resposta curta, direta e fluida no mesmo idioma da pergunta",
        agent=agent,
    )

    return str(
        Crew(
            agents=[agent],
            tasks=[task],
        ).kickoff()
    )