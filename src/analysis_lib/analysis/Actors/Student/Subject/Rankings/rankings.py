import pandas as pd
from typing import List, Dict, Any
from indicator import Indicator
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func
from ..Indicators.Performance.performance import Performance

class Rankings(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()
 
    def _ensure_numeric(self, df: pd.DataFrame, cols: List[str]): 
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
            name = str(row.get("full_name") or row.get("name") or row.get("fullname") or "")
            user_id = int(row.get("user_id", 0))
            mnn = float(row.get("media_nota_normalizada", 0.0))
            # Se vier normalizada (0..1), multiplica por 100; se já vier 0..100, mantém
            final_grade = round(mnn * 100 if mnn <= 1.0 else mnn, 2)
            grade_final = round(float(row.get("media_grade_final", 0.0)), 2)
            rows.append({
                "pos": i + 1,
                "user_id": user_id,
                "name": name,
                "final_grade": final_grade,
                "grade_final": grade_final
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
        df["grade_final"] = pd.to_numeric(df.get("grade_final", 0), errors="coerce").fillna(0.0)
        df["grademax"]   = pd.to_numeric(df.get("grademax", 0), errors="coerce").fillna(0.0)
        df["situacao"]   = df.get("situacao", "").astype(str)
        df["full_name"]  = df.get("full_name", "").astype(str)
        df["user_id"]    = pd.to_numeric(df.get("user_id", 0), errors="coerce").fillna(0).astype(int)

        if kind == "best-performance":
            status_score = {"Aprovado": 0, "Reprovado": 1, "RI": 2}
            df["_score"] = df["situacao"].map(status_score).fillna(3).astype(int)
            df_sorted = df.sort_values(
                by=["_score", "grade_final", "full_name"],
                ascending=[True, False, True],
                kind="mergesort",
            )
        elif kind == "at-risk":
            risk_order = {"RI": 0, "Reprovado": 1, "Aprovado": 2}
            mask = (df["situacao"].isin(["RI", "Reprovado"])) | (df["grade_final"] < 69.0)
            df_risk = df[mask].copy()
            if df_risk.empty:
                return {"id": subject_id, "type": kind, "ranking": []}
            df_risk["_score"] = df_risk["situacao"].map(risk_order).fillna(3).astype(int)
            df_sorted = df_risk.sort_values(
                by=["_score", "grade_final", "full_name"],
                ascending=[True, True, True],
                kind="mergesort",
            )
        else:
            raise ValueError("invalid 'type'")

        top = df_sorted.head(limit)
        ranking = [
            {
                "user_id": int(r.user_id),
                "student": str(r.full_name),
                "grade_final": float(r.grade_final),
                "grademax": float(r.grademax),
                "situacao": str(r.situacao),
            }
            for _, r in top.iterrows()
        ]

        return {"id": subject_id, "type": kind, "ranking": ranking}
    
    def general_analysis(self, version, connector, institution_id: int = 1, kind: str = "best-performance", limit: int = 10):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        global_indicators_student = Table("global_indicators_student", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    global_indicators_student.c.subject_id,
                    global_indicators_student.c.mean_grade_performance.label("grade_mean"),
                )
                .where(global_indicators_student.c.institution_id == institution_id)
                .where(global_indicators_student.c.mean_grade_performance.isnot(None))
            )
            rows = conn.execute(query).mappings().all()

        df_rank = pd.DataFrame(rows)
        if df_rank.empty:
            return {"id": institution_id, "type": kind, "ranking": []}

        ascending = (kind == "at-risk")
        df_rank = df_rank.sort_values("grade_mean", ascending=ascending, na_position="last").head(limit)

        df_subjects = self.mapper.get_all_subjects(connector, version)
        df_subjects["id"] = df_subjects["id"].astype(int)
        df_rank["subject_id"] = df_rank["subject_id"].astype(int)

        df_join = df_rank.merge(
            df_subjects[["id", "fullname", "shortname"]],
            left_on="subject_id",
            right_on="id",
            how="left"
        )

        ranking = [
            {
                "subject_id": int(r.subject_id),
                "name": str(r.fullname) if r.fullname is not None else None,
                "grade_mean": float(r.grade_mean),
            }
            for r in df_join.itertuples(index=False)
        ]

        return {"id": institution_id, "type": kind, "ranking": ranking}