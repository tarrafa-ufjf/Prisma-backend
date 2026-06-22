from __future__ import annotations

import json
import logging
import re
from typing import Any

from crewai import Agent, Crew, LLM, Task

from services.nl2sql.config import GENERATE_VEGA, VEGA_LITE_SCHEMA, VEGA_MAX_ROWS

log = logging.getLogger(__name__)


def _extract_json_object_or_null(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.lower() == "null":
        return None

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError as exc:
        log.warning(f"[Vega] Falha ao parsear JSON do Vega-Lite: {exc}")
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed


def _looks_chartable(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    if len(rows) == 1 and len(rows[0]) <= 1:
        return False
    return True


def generate_vega_spec(user_question: str, final_json: list[dict[str, Any]], llm: LLM) -> dict[str, Any] | None:
    if not GENERATE_VEGA:
        return None
    if not _looks_chartable(final_json):
        return None

    chart_rows = final_json[:VEGA_MAX_ROWS]
    vega_prompt = f"""
    Gere uma especificacao Vega-Lite v6 em JSON puro para visualizar o resultado abaixo.

    Pergunta original do usuario:
    {user_question}

    Dados retornados pelo SQL:
    {json.dumps(chart_rows, ensure_ascii=False)}

    Regras obrigatorias:
    - Retorne apenas JSON valido, sem markdown e sem texto adicional.
    - Use Vega-Lite, nao Vega puro.
    - Inclua "$schema": "{VEGA_LITE_SCHEMA}".
    - Inclua os dados inline em "data": {{"values": [...]}}.
    - Escolha mark e encoding adequados aos campos e a intencao da pergunta.
    - Use tipos quantitativos para numeros, temporais para datas e nominais para categorias.
    - Se os dados nao forem adequados para grafico, retorne apenas null.
    """

    agent = Agent(
        role="Data Visualization Specialist",
        goal="Gerar especificacoes Vega-Lite corretas a partir de resultados SQL em JSON",
        backstory=(
            "Você é especialista em visualização de dados. Sua tarefa é transformar dados "
            "tabulares em uma especificação Vega-Lite simples, válida e diretamente renderizável."
        ),
        llm=llm,
        verbose=False,
    )
    task = Task(
        description=vega_prompt,
        expected_output="JSON Vega-Lite valido ou null",
        agent=agent,
    )
    result = str(Crew(agents=[agent], tasks=[task]).kickoff())
    vega_spec = _extract_json_object_or_null(result)
    if vega_spec is None:
        return None

    vega_spec["$schema"] = VEGA_LITE_SCHEMA
    vega_spec["data"] = {"values": chart_rows}
    return vega_spec
