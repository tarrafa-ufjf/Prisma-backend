from __future__ import annotations

import logging
import time
from typing import Any, TypedDict

from crewai import LLM
from crewai_tools import NL2SQLTool
from langgraph.graph import END, START, StateGraph

from services.nl2sql.answer import generate_final_answer
from services.nl2sql.candidates import generate_candidate_sqls
from services.nl2sql.config import API_KEY, MODEL, N_EXECUTIONS, SAMPLE_ROWS_IN_TABLE_INFO
from services.nl2sql.db import build_moodle_db_uri
from services.nl2sql.execution import execute_sql_to_json
from services.nl2sql.judge import AdjudicationResult, adjudicate_winner_sql
from services.nl2sql.sql_processing import group_equivalent_sqls, process_sql
from services.nl2sql.visualization import generate_vega_spec

log = logging.getLogger(__name__)


class PipelineState(TypedDict):
    user_question: str
    llm: Any
    nl2sql: Any
    candidate_sqls: list[str]
    processed_sqls: list[dict[str, Any]]
    valid_sqls: list[str]
    groups: dict[int, list[str]]
    adjudication: AdjudicationResult
    winner_sql: str
    final_json: list[dict[str, Any]]
    vega_spec: dict[str, Any] | None
    final_answer: str
    confidence: float


def _log_step(name: str) -> None:
    log.info(f"[Pipeline] {name}")


def _make_step(name: str, fn):
    def wrapped(state: PipelineState) -> PipelineState:

        _log_step(name)

        inicio = time.time()

        resultado = fn(state)

        print(
            f"[TEMPO] {name}: {time.time() - inicio:.2f}s"
        )

        return resultado

    return wrapped


def build_pipeline():
    def _generate_candidates(state: PipelineState) -> PipelineState:
        sqls = generate_candidate_sqls(
            state["user_question"],
            state["nl2sql"],
            state["llm"],
            N_EXECUTIONS,
        )
        return {**state, "candidate_sqls": sqls}

    def _sqlglot_process(state: PipelineState) -> PipelineState:
        processed_sqls = [process_sql(sql) for sql in state["candidate_sqls"]]
        valid_sqls = [
            result["normalized"]
            for result in processed_sqls
            if result["safe"] and result["valid"]
        ]
        if not valid_sqls:
            raise RuntimeError(
                "Nenhum SQL passou pelo SQLGlot safety/validation gate. "
                "Verifique a conexão com o banco e a API."
            )
        return {**state, "processed_sqls": processed_sqls, "valid_sqls": valid_sqls}

    def _group_sqls(state: PipelineState) -> PipelineState:
        return {**state, "groups": group_equivalent_sqls(state["valid_sqls"])}

    def _adjudicate(state: PipelineState) -> PipelineState:
        adjudication = adjudicate_winner_sql(
            state["groups"],
            state["user_question"],
            state["llm"],
        )
        return {
            **state,
            "adjudication": adjudication,
            "winner_sql": adjudication["winner_sql"],
            "confidence": adjudication["confidence_signal"],
        }

    def _execute_sql(state: PipelineState) -> PipelineState:
        return {**state, "final_json": execute_sql_to_json(state["winner_sql"])}

    def _generate_vega(state: PipelineState) -> PipelineState:
        vega_spec = generate_vega_spec(
            state["user_question"],
            state["final_json"],
            state["llm"],
        )
        return {**state, "vega_spec": vega_spec}

    def _generate_answer(state: PipelineState) -> PipelineState:
        final_answer = generate_final_answer(
            state["user_question"],
            state["winner_sql"],
            state["final_json"],
            state["llm"],
        )
        return {**state, "final_answer": final_answer}

    graph = StateGraph(PipelineState)
    graph.add_node("generate_candidates", _make_step("1/7 - Self-consistency candidates", _generate_candidates))
    graph.add_node("sqlglot_process", _make_step("2/7 - SQLGlot processing", _sqlglot_process))
    graph.add_node("group_sqls", _make_step("3/7 - AST grouping", _group_sqls))
    graph.add_node("adjudicate", _make_step("4/7 - LLM judge adjudication", _adjudicate))
    graph.add_node("execute_sql", _make_step("5/7 - Execute SQL", _execute_sql))
    graph.add_node("generate_vega", _make_step("6/7 - Generate Vega-Lite", _generate_vega))
    graph.add_node("generate_answer", _make_step("7/7 - Generate answer", _generate_answer))

    graph.add_edge(START, "generate_candidates")
    graph.add_edge("generate_candidates", "sqlglot_process")
    graph.add_edge("sqlglot_process", "group_sqls")
    graph.add_edge("group_sqls", "adjudicate")
    graph.add_edge("adjudicate", "execute_sql")
    graph.add_edge("execute_sql", "generate_vega")
    graph.add_edge("generate_vega", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


def _build_initial_state(user_question: str) -> PipelineState:
    llm = LLM(model=MODEL, api_key=API_KEY, temperature=0.3)
    nl2sql = NL2SQLTool(
        db_uri=build_moodle_db_uri(),
        sample_rows_in_table_info=SAMPLE_ROWS_IN_TABLE_INFO,
        allow_dml=False,
    )

    return {
        "user_question": user_question,
        "llm": llm,
        "nl2sql": nl2sql,
        "candidate_sqls": [],
        "processed_sqls": [],
        "valid_sqls": [],
        "groups": {},
        "adjudication": {},  # type: ignore[typeddict-item]
        "winner_sql": "",
        "final_json": [],
        "vega_spec": None,
        "final_answer": "",
        "confidence": 0.0,
    }


def run_nl2sql_pipeline(user_question: str) -> dict[str, Any]:
    if not user_question or not user_question.strip():
        raise ValueError("question is required")
    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is required")

    pipeline = build_pipeline()
    state = pipeline.invoke(_build_initial_state(user_question))

    return {
        "final_answer": state["final_answer"],
        "final_json": state["final_json"],
        "vega": state["vega_spec"],
        "sql": state["winner_sql"],
        "confidence": state["confidence"],
        "candidate_sqls": state["candidate_sqls"],
        "adjudication": state["adjudication"],
    }
