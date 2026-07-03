from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from crewai import Agent, Crew, LLM, Task
from crewai_tools import NL2SQLTool

from services.nl2sql.config import MAX_WORKERS, N_EXECUTIONS

log = logging.getLogger(__name__)


def extract_sql(text: str) -> str:
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match2 = re.search(r"((?:SELECT|WITH)\s+.+)", text, re.DOTALL | re.IGNORECASE)
    if match2:
        return match2.group(1).strip()
    return text.strip()


def _format_chat_history(messages: list[dict[str, Any]]) -> str:
    """Formata o histórico de mensagens para os agentes entenderem o contexto."""
    if not messages or len(messages) <= 1:
        return "Nenhum histórico anterior."
        
    formatted_turns = []
    # Pegamos tudo menos a última mensagem (que é a pergunta atual)
    for msg in messages[:-1]:
        role = "Usuário" if msg.get("role") == "user" else "Assistente"
        content = msg.get("content", "")
        formatted_turns.append(f"{role}: {content}")
        
    return "\n".join(formatted_turns)


# 1. ADICIONADO O PARÂMETRO 'chat_history'
def run_single_nl2sql(
    prompt: str, 
    chat_history: str, 
    nl2sql: NL2SQLTool, 
    llm: LLM, 
    run_id: str
) -> str:
    nl2sql.cache_function = lambda *args, **kwargs: False   
    agent = Agent(
        role="Data Analyst",
        goal="Analisar o schema do banco de dados PostgreSQL e converter linguagem natural em SQL preciso levando em conta o contexto da conversa",
        backstory=(
            "Você é um analista de dados sênior especialista em PostgreSQL. Sua principal regra é: "
            "NUNCA adivinhe nomes de tabelas ou colunas e NUNCA use comandos de outros dialetos como 'SHOW TABLES'. "
            "Você deve usar a ferramenta fornecida para inspecionar o banco de dados. Como o banco é PostgreSQL, "
            "se precisar listar as tabelas manualmente, você sabe que deve consultar o 'information_schema.tables'."
        ),
        tools=[nl2sql],
        llm=llm,
        verbose=True
    )

    # 2. INJETADO O HISTÓRICO DA CONVERSA NA TASK DESCRIPTION
    task_description = f"""
    Histórico da conversa anterior (Contexto):
    {chat_history}
    
    Pergunta ATUAL do usuário: {prompt}
    
    Contexto: O banco de dados é PostgreSQL.
    
    Atenção: Use o Histórico da Conversa para entender termos ambíguos. 
    **MUITO IMPORTANTE:** Se a pergunta atual for um funil/continuação (ex: "desses alunos, quais têm as maiores notas?"), você NÃO PODE consultar os resultados anteriores diretamente. Você DEVE gerar uma NOVA QUERY COMPLETA para o banco de dados que combine as regras/filtros da pergunta anterior COM os filtros da pergunta atual.
    
    Passos obrigatórios e sequenciais que você DEVE seguir:
    1. Identifique as tabelas potenciais usando a ferramenta.
    2. Execute uma query de amostragem (ex: SELECT * FROM tabela LIMIT 3; ou SELECT DISTINCT coluna FROM tabela;) para inspecionar os dados REAIS, formatos, e ver como os textos/filtros estão escritos no banco de dados.
    3. Com base nos dados REAIS que você visualizou na amostragem, ajuste os filtros da cláusula WHERE para condizer exatamente com o banco (atente-se a maiúsculas/minúsculas e termos exatos).
    4. Construa a query final e retorne APENAS o código SQL puro dentro de ```sql ... ```.
    """

    task = Task(
        description=task_description,
        expected_output="Apenas o código SQL puro para PostgreSQL envolto em ```sql ... ```, gerado após a validação do banco.",
        agent=agent,
        verbose=True,
    )

    crew = Crew(
        agents=[agent], 
        tasks=[task], 
        verbose=True,
    )
    result = str(crew.kickoff())
    sql = extract_sql(result)
    log.info(f"[{run_id}] SQL gerado:\n{sql}\n")

    return sql


# 3. ALTERADO PARA RECEBER AS 'messages' DO LANGGRAPH
def generate_candidate_sqls(
    user_question: str,
    messages: list[dict[str, Any]],
    nl2sql: NL2SQLTool,
    llm: LLM,
    n_executions: int = N_EXECUTIONS,
) -> list[str]:
    
    # Formata o histórico uma única vez antes de disparar as threads
    chat_history = _format_chat_history(messages)

    sqls: list[str] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Usando dicionário explícito para evitar erros de desempacotamento por posição
        futures = {}
        for i in range(n_executions):
            run_id = f"R{i+1:02d}"
            
            # Submete explicitamente nomeando os parâmetros ou garantindo a ordem exata
            future = executor.submit(
                run_single_nl2sql,
                prompt=user_question,
                chat_history=chat_history,
                nl2sql=nl2sql,
                llm=llm,
                run_id=run_id
            )
            futures[future] = run_id

        for future in as_completed(futures):
            run_id = futures[future]
            try:
                sql = future.result()
                if sql:
                    sqls.append(sql)
            except Exception as exc:
                print(exc)
                log.error(f"[{run_id}] Erro na execução: {exc}")

    log.info(f"Self-consistency: {len(sqls)}/{n_executions} SQLs coletados")
    return sqls