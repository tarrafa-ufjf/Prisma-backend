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

        out["total_response_forum"] = (
            out["num_response_fast_forum"].fillna(0).astype(int)
            + out["num_response_normal_forum"].fillna(0).astype(int)
            + out["num_response_late_forum"].fillna(0).astype(int)
        )
        out["volume"] = np.log1p(out["total_response_forum"].clip(lower=0))

        out["mean_weekly_course_views_window"] = pd.to_numeric(
            out["mean_weekly_course_views_window"], errors="coerce"
        ).fillna(0.0)

        out["score_access"] = pd.to_numeric(out["score_access"], errors="coerce").fillna(0.0)

        group_cols = ["institution_id", "version", "subject_id"]

        out["login_norm"] = out.groupby(group_cols)["mean_weekly_course_views_window"].transform(minmax_group)
        out["forum_quality_norm"] = out.groupby(group_cols)["score_access"].transform(minmax_group)
        out["volume_norm"] = out.groupby(group_cols)["volume"].transform(minmax_group)

        out["ranking_score"] = (0.45 * out["login_norm"] + 0.35 * out["forum_quality_norm"] + 0.20 * out["volume_norm"])

        # rank dentro da disciplina
        out["rank_in_subject"] = (out.groupby(group_cols)["ranking_score"].rank(method="dense", ascending=False).astype(int))

        cols = ["institution_id", "version", "subject_id", "tutor_id", "rank_in_subject", "ranking_score"]
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
                t.c.score_access,
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
        df_names = self.mapper.fetch_tutors_names(connector, version, subject_id)
        
        ranked_out = ranked.merge(df_names, on="tutor_id", how="left")
        
        if kind == "best-performance":
            return ranked_out[["subject_id", "tutor_id", "full_name"]].head(limit)

        if kind == "at-risk":
            return ranked_out[["subject_id", "tutor_id", "full_name"]].sort_values("ranking_score", ascending=True).head(limit)

        return ranked_out.head(limit)
    
    def general_analysis(self, version, connector, institution_id: int = 1, kind: str = "best-performance", limit: int = 10):
        """
        Ranking geral de tutores na instituição.
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
                    t.c.score_access,
                    t.c.num_response_fast_forum,
                    t.c.num_response_normal_forum,
                    t.c.num_response_late_forum,
                    t.c.label_access,
                    t.c.label_forums_response,
                )
                .where(t.c.institution_id == int(institution_id))
            )

            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        if not rows:
            return {"id": institution_id, "type": kind, "ranking": []}

        df = pd.DataFrame(rows)

        # 1) calcula ranking por (subject_id, tutor_id)
        ranked = self.build_tutors_ranking(df)  
        
        if ranked is None or ranked.empty:
            return {"id": institution_id, "type": kind, "ranking": []}

        # 2) agrega por tutor (global)
        agg = (
            ranked.groupby("tutor_id", as_index=False)
            .agg(
                ranking_score=("ranking_score", "mean"),
                n_subjects=("subject_id", "nunique"),
                subjects=("subject_id", lambda s: list(pd.unique(s))),
            )
        )

        ascending = (kind == "at-risk")
        agg = agg.sort_values("ranking_score", ascending=ascending, na_position="last").head(limit)

        # 3) busca nomes dos tutores 
        tutor_ids = set(agg["tutor_id"].astype(int).tolist())
        subject_ids = ranked.loc[ranked["tutor_id"].astype(int).isin(tutor_ids), "subject_id"].dropna().unique().tolist()

        df_names_list = []
        for sid in subject_ids:
            df_n = self.mapper.fetch_tutors_names(connector, version, int(sid))
            if df_n is None:
                continue
            if not isinstance(df_n, pd.DataFrame):
                df_n = pd.DataFrame(df_n)
            if not df_n.empty:
                df_names_list.append(df_n[["tutor_id", "full_name"]])

        if df_names_list:
            df_names = pd.concat(df_names_list, ignore_index=True)
            df_names["tutor_id"] = df_names["tutor_id"].astype(int)
            df_names = df_names.dropna(subset=["tutor_id"]).drop_duplicates(subset=["tutor_id"], keep="first")
            agg["tutor_id"] = agg["tutor_id"].astype(int)
            agg = agg.merge(df_names, on="tutor_id", how="left")
        else:
            agg["full_name"] = None

        ranking = [
            {
                "tutor_id": int(r.tutor_id),
                "full_name": str(r.full_name) if r.full_name is not None else None,
                "ranking_score": float(r.ranking_score) if r.ranking_score is not None else None,
                "n_subjects": int(r.n_subjects) if r.n_subjects is not None else 0,
                "subjects": [int(x) for x in (r.subjects or [])],
            }
            for r in agg.itertuples(index=False)
        ]

        return {"id": institution_id, "type": kind, "ranking": ranking}