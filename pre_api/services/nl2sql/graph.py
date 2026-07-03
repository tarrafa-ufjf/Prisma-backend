from __future__ import annotations

import logging
import time
from typing import Any, TypedDict, Annotated

from crewai import LLM
from crewai_tools import NL2SQLTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from services.nl2sql.answer import generate_final_answer
from services.nl2sql.candidates import generate_candidate_sqls
from services.nl2sql.config import API_KEY, MODEL, N_EXECUTIONS, SAMPLE_ROWS_IN_TABLE_INFO
from services.nl2sql.db import build_db_uri
from services.nl2sql.execution import execute_sql_to_json
from services.nl2sql.judge import AdjudicationResult, adjudicate_winner_sql
from services.nl2sql.sql_processing import group_equivalent_sqls, process_sql
from services.nl2sql.visualization import generate_vega_spec

log = logging.getLogger(__name__)


class PipelineState(TypedDict):
    user_question: str
    messages: Annotated[list, add_messages]  # Mantém o histórico de chats ativo
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


# 1. MEMÓRIA GLOBAL: Instanciada fora das funções para que persista na memória da aplicação
_global_memory = MemorySaver()


def _get_sqlglot_dialect(db_uri: str) -> str:
    """Limpa o prefixo do SQLAlchemy para o formato que o SQLGlot entende."""
    raw_dialect = db_uri.split(":")[0] if ":" in db_uri else "mysql"
    # Se tiver 'postgres' em qualquer lugar (ex: postgresql+psycopg), retorna 'postgres'
    if "postgres" in raw_dialect:
        return "postgres"
    if "mysql" in raw_dialect or "mariadb" in raw_dialect:
        return "mysql"
    if "sqlite" in raw_dialect:
        return "sqlite"
    return raw_dialect.split("+")[0]  # Remove driver se for outro banco


def generate_candidates_node(state: PipelineState, llm: LLM, nl2sql: NL2SQLTool) -> dict[str, Any]:
    t0 = time.perf_counter()
    # Recupera o histórico completo que o LangGraph injetou em state["messages"]
    sqls = generate_candidate_sqls(
        user_question=state["user_question"],
        messages=state["messages"],
        nl2sql=nl2sql,
        llm=llm
    )
    log.info(f"[Node: Candidates] Gerados {len(sqls)} SQLs em {time.perf_counter() - t0:.2f}s")
    return {"candidate_sqls": sqls}


def process_and_validate_node(state: PipelineState, nl2sql: NL2SQLTool) -> dict[str, Any]:
    t0 = time.perf_counter()
    processed: list[dict[str, Any]] = []
    valid: list[str] = []
    
    # Usa a nova função para extrair o dialeto limpo
    dialect = _get_sqlglot_dialect(nl2sql.db_uri)

    for sql in state["candidate_sqls"]:
        res = process_sql(sql, dialect=dialect)
        processed.append(res)
        if res["safe"] and res["valid"]:
            valid.append(res["normalized"])

    log.info(
        f"[Node: Validation] Processados {len(processed)} candidatos. "
        f"Válidos: {len(valid)} em {time.perf_counter() - t0:.2f}s"
    )
    return {"processed_sqls": processed, "valid_sqls": valid}


def group_sqls_node(state: PipelineState, nl2sql: NL2SQLTool) -> dict[str, Any]:
    t0 = time.perf_counter()
    # Usa a nova função para extrair o dialeto limpo
    dialect = _get_sqlglot_dialect(nl2sql.db_uri)
    
    groups = group_equivalent_sqls(state["valid_sqls"], dialect=dialect)
    log.info(f"[Node: Grouping] Formados {len(groups)} grupos equivalentes em {time.perf_counter() - t0:.2f}s")
    return {"groups": groups}


def adjudicate_node(state: PipelineState, llm: LLM) -> dict[str, Any]:
    t0 = time.perf_counter()
    if not state["groups"]:
        log.warning("[Node: Judge] Nenhum grupo de SQL válido disponível para adjudicação.")
        return {
            "winner_sql": "",
            "confidence": 0.0,
            "adjudication": {
                "winner_sql": "",
                "winner_index": -1,
                "scores": {},
                "reasoning": "Nenhum SQL válido gerado.",
                "group_sizes": {},
                "confidence_signal": 0.0,
            }
        }

    # --- A MUDANÇA FOI AQUI ---
    # Passamos o dicionário de 'groups' direto, pois o judge.py já espera por ele
    adj_res = adjudicate_winner_sql(
        groups=state["groups"],
        user_question=state["user_question"],
        llm=llm
    )
    
    log.info(f"[Node: Judge] Adjudicação concluída em {time.perf_counter() - t0:.2f}s. Confiança: {adj_res['confidence_signal']}%")
    return {
        "adjudication": adj_res,
        "winner_sql": adj_res["winner_sql"],
        "confidence": adj_res["confidence_signal"]
    }

def execute_sql_node(state: PipelineState) -> dict[str, Any]:
    t0 = time.perf_counter()
    sql = state["winner_sql"]
    if not sql:
        log.warning("[Node: Execution] Nenhum SQL vencedor para executar.")
        return {"final_json": []}

    try:
        data = execute_sql_to_json(sql)
        log.info(f"[Node: Execution] SQL executado com sucesso. Retornou {len(data)} linhas em {time.perf_counter() - t0:.2f}s")
        return {"final_json": data}
    except Exception as exc:
        log.error(f"[Node: Execution] Erro crítico ao executar SQL vencedor: {exc}")
        return {"final_json": []}


def generate_vega_node(state: PipelineState, llm: LLM) -> dict[str, Any]:
    t0 = time.perf_counter()
    spec = generate_vega_spec(
        user_question=state["user_question"],
        final_json=state["final_json"],
        llm=llm
    )
    log.info(f"[Node: Vega] Geração de especificação Vega-Lite concluída em {time.perf_counter() - t0:.2f}s")
    return {"vega_spec": spec}


def generate_answer_node(state: PipelineState, llm: LLM) -> dict[str, Any]:
    t0 = time.perf_counter()
    ans = generate_final_answer(
        user_question=state["user_question"],
        messages=state["messages"],
        winner_sql=state["winner_sql"],
        final_json=state["final_json"],
        llm=llm
    )
    log.info(f"[Node: Answer] Resposta final gerada em {time.perf_counter() - t0:.2f}s")
    
    # Retorna a resposta assistente em formato de mensagem para o LangGraph atualizar o histórico
    return {
        "final_answer": ans,
        "messages": [{"role": "assistant", "content": ans}]
    }


def build_pipeline(llm: LLM, nl2sql: NL2SQLTool):
    graph = StateGraph(PipelineState)

    # Registro dos nós com injeção de dependências
    graph.add_node("generate_candidates", lambda s: generate_candidates_node(s, llm, nl2sql))
    graph.add_node("process_and_validate", lambda s: process_and_validate_node(s, nl2sql))
    graph.add_node("group_sqls", lambda s: group_sqls_node(s, nl2sql))
    graph.add_node("adjudicate", lambda s: adjudicate_node(s, llm))
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("generate_vega", lambda s: generate_vega_node(s, llm))
    graph.add_node("generate_answer", lambda s: generate_answer_node(s, llm))

    # Construção do fluxo sequencial linear
    graph.add_edge(START, "generate_candidates")
    graph.add_edge("generate_candidates", "process_and_validate")
    graph.add_edge("process_and_validate", "group_sqls")
    graph.add_edge("group_sqls", "adjudicate")
    graph.add_edge("adjudicate", "execute_sql")
    graph.add_edge("execute_sql", "generate_vega")
    graph.add_edge("generate_vega", "generate_answer")
    graph.add_edge("generate_answer", END)

    # Compilação usando o checkpointer global persistente
    return graph.compile(checkpointer=_global_memory)


def run_nl2sql_pipeline(user_question: str, thread_id: str = "default_user") -> dict[str, Any]:
    if not user_question or not user_question.strip():
        raise ValueError("question is required")
    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is required")

    llm = LLM(model=MODEL, api_key=API_KEY, temperature=0.3)
    nl2sql = NL2SQLTool(
        db_uri=build_db_uri(),
        sample_rows_in_table_info=SAMPLE_ROWS_IN_TABLE_INFO,
        allow_dml=False,
    )

    pipeline = build_pipeline(llm, nl2sql)
    config = {"configurable": {"thread_id": thread_id}}
    
    # Lógica de atualização do estado: passamos apenas a nova pergunta.
    # O checkpointer lidará com a concatenação automática via "add_messages".
    inputs = {
        "user_question": user_question,
        "messages": [{"role": "user", "content": user_question}],
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
    
    state = pipeline.invoke(inputs, config=config)

    return {
        "final_answer": state["final_answer"],
        "final_json": state["final_json"],
        "vega_spec": state["vega_spec"],
        "confidence": state["confidence"],
    }