from __future__ import annotations

import json
import logging
import re
from collections import Counter
from typing import TypedDict

from crewai import Agent, Crew, LLM, Task

from services.nl2sql.prompts import JUDGE_DIMENSIONS

log = logging.getLogger(__name__)


class AdjudicationResult(TypedDict):
    winner_sql: str
    winner_index: int
    scores: dict[str, dict[str, int]]
    reasoning: str
    group_sizes: dict[int, int]
    confidence_signal: float


def _build_judge_prompt(user_question: str, representatives: list[str], group_sizes: list[int]) -> str:
    candidates_block = "\n\n".join(
        f"[CANDIDATO {i}] (gerado {group_sizes[i]}x de {sum(group_sizes)} execuções)\n{sql}"
        for i, sql in enumerate(representatives)
    )
    dimensions_desc = "\n".join(
        f"  - {dim.replace('_', ' ').upper()}: 0–10"
        for dim in JUDGE_DIMENSIONS
    )

    return f"""
        Você é um juiz técnico especializado em SQL e no schema Moodle.

        PERGUNTA ORIGINAL DO USUÁRIO:
        {user_question}

        CANDIDATOS SQL (com frequência de aparição como sinal auxiliar):
        {candidates_block}

        SUA TAREFA:
        Avalie cada candidato nas seguintes dimensões (0-10 cada):
        {dimensions_desc}

        CRITÉRIO DE DECISÃO:
        A frequência de aparição é apenas um sinal auxiliar de confiança — NÃO é o critério
        de decisão. Escolha o SQL tecnicamente mais correto e completo, mesmo que seja
        o menos frequente. Justifique explicitamente por que o vencedor supera os demais.

        Retorne APENAS um JSON válido (sem markdown, sem preamble) com esta estrutura exata:
        {{
        "scores": {{
            "0": {{"intencao_usuario": 8, "aderencia_schema": 9, "precisao_semantica": 7, "seguranca": 10, "completude": 8, "robustez": 7, "ausencia_ambiguidades": 9}},
            "1": {{ ... }},
            ...
        }},
        "winner_index": 0,
        "reasoning": "Explicação técnica detalhada da escolha, comparando os candidatos dimensão a dimensão."
        }}
    """


def adjudicate_winner_sql(groups: dict[int, list[str]], user_question: str, llm: LLM) -> AdjudicationResult:
    if not groups:
        raise ValueError("Nenhum grupo disponível para adjudicação.")

    total_votes = sum(len(g) for g in groups.values())
    representatives: list[str] = []
    group_sizes: list[int] = []

    for sqls in groups.values():
        rep = Counter(sqls).most_common(1)[0][0]
        representatives.append(rep)
        group_sizes.append(len(sqls))

    if len(representatives) == 1:
        log.info("[Judge] Apenas 1 grupo AST — adjudicação trivial.")
        winner_sql = representatives[0]
        winner_group_size = group_sizes[0]
        return AdjudicationResult(
            winner_sql=winner_sql,
            winner_index=0,
            scores={},
            reasoning="Único grupo AST — sem disputa entre candidatos.",
            group_sizes={0: winner_group_size},
            confidence_signal=round(winner_group_size / total_votes * 100, 1),
        )

    judge_prompt = _build_judge_prompt(user_question, representatives, group_sizes)
    agent = Agent(
        role="SQL Technical Judge",
        goal="Selecionar o SQL tecnicamente mais correto e completo para a pergunta do usuário",
        backstory=(
            "Você é um árbitro técnico sênior, especialista em SQL e qualidade de queries. Sua decisão é baseada exclusivamente em critérios técnicos e semânticos. "
            "Você analisa cada candidato de forma independente e justifica sua escolha com rigor."
        ),
        llm=llm,
        verbose=False
    )
    task = Task(
        description=judge_prompt,
        expected_output="JSON com scores por dimensão, winner_index e reasoning técnico detalhado",
        agent=agent,
    )
    result = str(Crew(agents=[agent], tasks=[task]).kickoff())

    try:
        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if not json_match:
            raise ValueError("Nenhum JSON encontrado na resposta do juiz.")

        data = json.loads(json_match.group())
        winner_index = int(data["winner_index"])
        if not (0 <= winner_index < len(representatives)):
            raise ValueError(f"winner_index={winner_index} fora do range válido.")

        winner_sql = representatives[winner_index]
        winner_size = group_sizes[winner_index]
        log.info(
            f"[Judge] Vencedor: candidato {winner_index} "
            f"({winner_size} votos / {total_votes} total) | "
            f"Grupos avaliados: {len(representatives)}"
        )

        return AdjudicationResult(
            winner_sql=winner_sql,
            winner_index=winner_index,
            scores={str(k): v for k, v in data.get("scores", {}).items()},
            reasoning=data.get("reasoning", ""),
            group_sizes={i: s for i, s in enumerate(group_sizes)},
            confidence_signal=round(winner_size / total_votes * 100, 1),
        )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        log.warning(
            f"[Judge] Falha ao parsear resposta do juiz ({exc}). "
            "Fallback: grupo mais frequente."
        )
        fallback_idx = max(range(len(group_sizes)), key=lambda i: group_sizes[i])
        fallback_size = group_sizes[fallback_idx]
        return AdjudicationResult(
            winner_sql=representatives[fallback_idx],
            winner_index=fallback_idx,
            scores={},
            reasoning=f"[FALLBACK] Juiz LLM falhou ({exc}). Usando grupo mais frequente.",
            group_sizes={i: s for i, s in enumerate(group_sizes)},
            confidence_signal=round(fallback_size / total_votes * 100, 1),
        )
