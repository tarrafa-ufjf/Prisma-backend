import pandas as pd
from typing import List, Dict, Any
from ..indicator import Indicator
from ..Desempenho.performance import Performance 

class Rankings(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
 
    def _ensure_numeric(self, df: pd.DataFrame, cols: List[str]): # Garante que colunas usadas na ordenação/filtragem sejam numéricas
        df = df.copy()
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            else:
                df[c] = 0
        return df

    def _to_ranking_rows(self, df: pd.DataFrame, limit: int):
        rows: List[Dict[str, Any]] = []
        for i, row in df.head(limit).reset_index(drop=True).iterrows():
            name = str(row.get("firstname") or row.get("name") or row.get("fullname") or "")
            user_id = int(row.get("user_id", 0))
            mnn = float(row.get("media_nota_normalizada", 0.0))
            # Se vier normalizada (0..1), multiplica por 100; se já vier 0..100, mantém
            final_grade = round(mnn * 100 if mnn <= 1.0 else mnn, 2)
            percentual = round(float(row.get("media_percentual", 0.0)), 2)
            rows.append({
                "pos": i + 1,
                "user_id": user_id,
                "name": name,
                "final_grade": final_grade,
                "percentual": percentual
            })
        return rows

    def subject_analysis(self, subject_id: int, version, connector, kind: str = "best-performance", limit: int = 10):
        """
        Monta rankings por disciplina (subject).
        kind: 'best-performance' | 'at-risk'
        """
        perf = Performance(self.mapper)
        df = perf.grades_students_analysis(version, connector, subject_id)

        if df is None or len(df) == 0:
            return {"id": subject_id, "type": kind, "ranking": []}

        df = df.copy()
        df["percentual"] = pd.to_numeric(df.get("percentual", 0), errors="coerce").fillna(0.0)
        df["nota_final"] = pd.to_numeric(df.get("nota_final", 0), errors="coerce").fillna(0.0)
        df["grademax"]   = pd.to_numeric(df.get("grademax", 0), errors="coerce").fillna(0.0)
        df["situacao"]   = df.get("situacao", "").astype(str)
        df["firstname"]  = df.get("firstname", "").astype(str)
        df["user_id"]    = pd.to_numeric(df.get("user_id", 0), errors="coerce").fillna(0).astype(int)

        if kind == "best-performance":
            status_score = {"Aprovado": 0, "Reprovado": 1, "RI": 2}
            df["_score"] = df["situacao"].map(status_score).fillna(3).astype(int)
            df_sorted = df.sort_values(
                by=["_score", "percentual", "nota_final", "firstname"],
                ascending=[True, False, False, True],
                kind="mergesort",
            )
        elif kind == "at-risk":
            risk_order = {"RI": 0, "Reprovado": 1, "Aprovado": 2}
            mask = (df["situacao"].isin(["RI", "Reprovado"])) | (df["percentual"] < 69.0)
            df_risk = df[mask].copy()
            if df_risk.empty:
                return {"id": subject_id, "type": kind, "ranking": []}
            df_risk["_score"] = df_risk["situacao"].map(risk_order).fillna(3).astype(int)
            df_sorted = df_risk.sort_values(
                by=["_score", "percentual", "nota_final", "firstname"],
                ascending=[True, True, True, True],
                kind="mergesort",
            )
        else:
            raise ValueError("invalid 'type'")

        top = df_sorted.head(limit)
        ranking = [
            {
                "user_id": int(r.user_id),
                "student": str(r.firstname),
                "percentual": float(r.percentual),
                "nota_final": float(r.nota_final),
                "grademax": float(r.grademax),
                "situacao": str(r.situacao),
            }
            for _, r in top.iterrows()
        ]

        return {"id": subject_id, "type": kind, "ranking": ranking}