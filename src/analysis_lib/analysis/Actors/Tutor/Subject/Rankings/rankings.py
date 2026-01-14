import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .....indicator import Indicator
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class Rankings(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    @staticmethod
    def build_tutors_ranking(df):
        def minmax_group(s):
            s = pd.to_numeric(s, errors="coerce").fillna(0.0)
            mn = s.min()
            mx = s.max()
            if pd.isna(mn) or pd.isna(mx) or mx == mn:
                return pd.Series(0.0, index=s.index)
            return (s - mn) / (mx - mn)
    
        out = df.copy()

        out["total_respostas_forum"] = (
            out["num_response_fast_forum"].fillna(0).astype(int)
            + out["num_response_normal_forum"].fillna(0).astype(int)
            + out["num_response_late_forum"].fillna(0).astype(int)
        )
        out["volume"] = np.log1p(out["total_respostas_forum"].clip(lower=0))

        out["mean_weekly_course_views_window"] = pd.to_numeric(
            out["mean_weekly_course_views_window"], errors="coerce"
        ).fillna(0.0)

        out["score"] = pd.to_numeric(out["score"], errors="coerce").fillna(0.0)

        group_cols = ["institution_id", "version", "subject_id"]

        out["login_norm"] = out.groupby(group_cols)["mean_weekly_course_views_window"].transform(minmax_group)
        out["forum_quality_norm"] = out.groupby(group_cols)["score"].transform(minmax_group)
        out["volume_norm"] = out.groupby(group_cols)["volume"].transform(minmax_group)

        out["ranking_score"] = (0.45 * out["login_norm"] + 0.35 * out["forum_quality_norm"] + 0.20 * out["volume_norm"])

        # rank dentro da disciplina
        out["rank_in_subject"] = (out.groupby(group_cols)["ranking_score"].rank(method="dense", ascending=False).astype(int))

        cols = [
            "institution_id", "version", "subject_id", "tutor_id",
            "rank_in_subject", "ranking_score",
            "login_norm", "forum_quality_norm", "volume_norm",
            "mean_weekly_course_views_window", "score", "total_respostas_forum",
            "label_access", "label_forums_response",
        ]
        for c in cols:
            if c not in out.columns:
                out[c] = pd.NA

        return out[cols].sort_values(
            ["institution_id", "version", "subject_id", "rank_in_subject", "tutor_id"]
        )
        
    def subject_analysis(self, subject_id: int, version, connector, kind: str = "best-performance", limit: int = 10, institution_id: int = 1):
        """
        Monta rankings por disciplina (subject).
        kind: 'best-performance' | 'at-risk'
        """
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                t.c.institution_id,
                t.c.version,
                t.c.subject_id,
                t.c.tutor_id,
                t.c.mean_weekly_course_views_window,
                t.c.score,
                t.c.num_response_fast_forum,
                t.c.num_response_normal_forum,
                t.c.num_response_late_forum,
                t.c.label_access,
                t.c.label_forums_response,       
                )
                .where(t.c.institution_id == institution_id)
                .where(t.c.subject_id == int(subject_id))
            )
            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        ranked = self.build_tutors_ranking(df)

        if kind == "best-performance":
            return ranked.head(limit)

        if kind == "at-risk":
            return ranked.sort_values("ranking_score", ascending=True).head(limit)

        return ranked.head(limit)