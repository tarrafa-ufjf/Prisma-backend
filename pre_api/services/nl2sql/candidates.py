from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from crewai import Agent, Crew, LLM, Task
from crewai_tools import NL2SQLTool

from services.nl2sql.config import MAX_WORKERS, N_EXECUTIONS
from services.nl2sql.prompts import INDICATORS_RULES

log = logging.getLogger(__name__)


def extract_sql(text: str) -> str:
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match2 = re.search(r"((?:SELECT|WITH)\s+.+)", text, re.DOTALL | re.IGNORECASE)
    if match2:
        return match2.group(1).strip()
    return text.strip()


def run_single_nl2sql(prompt: str, nl2sql: NL2SQLTool, llm: LLM, run_id: str) -> str:
    agent = Agent(
        role="Data Analyst",
        goal="Converter linguagem natural em SQL PostgreSQL para o banco de indicadores",
        backstory=INDICATORS_RULES,
        tools=[nl2sql],
        llm=llm,
        verbose=False,
    )
    task = Task(
        description=prompt,
        expected_output="Apenas o SQL puro dentro de ```sql ... ```",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = str(crew.kickoff())
    sql = extract_sql(result)
    log.info(f"[{run_id}] SQL gerado:\n{sql}\n")
    return sql


def generate_candidate_sqls(
    user_question: str,
    nl2sql: NL2SQLTool,
    llm: LLM,
    n_executions: int = N_EXECUTIONS,
) -> list[str]:
    tasks_args = [
        (user_question, nl2sql, llm, f"R{i+1:02d}")
        for i in range(n_executions)
    ]

    sqls: list[str] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(run_single_nl2sql, *args): args[3]
            for args in tasks_args
        }
        for future in as_completed(futures):
            run_id = futures[future]
            try:
                sql = future.result()
                if sql:
                    sqls.append(sql)
            except Exception as exc:
                log.error(f"[{run_id}] Erro na execução: {exc}")

    log.info(f"Self-consistency: {len(sqls)}/{n_executions} SQLs coletados")
    return sqls
