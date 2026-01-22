import pandas as pd
import numpy as np
from sqlalchemy import MetaData, Table, select
from .....indicator import Indicator
from database import DatabaseAdmin


class Rankings(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    @staticmethod
    def _minmax_norm(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
        """
        Normaliza por min-max dentro de um grupo.
        - higher_is_better=True: maior vira melhor (0..1)
        - higher_is_better=False: menor vira melhor (0..1)
        """
        s = pd.to_numeric(series, errors="coerce")
        mn = s.min()
        mx = s.max()

        if pd.isna(mn) or pd.isna(mx) or mx == mn:
            return pd.Series(0.0, index=series.index)

        norm = (s - mn) / (mx - mn)
        if not higher_is_better:
            norm = 1.0 - norm

        return norm.fillna(0.0).astype(float)

    
    def build_local_ranking(self, df, group_cols=("institution_id", "version", "subject_id")):
        if df is None or df.empty:
            return pd.DataFrame()

        out = df.copy()
        
        out = out.drop_duplicates()

        if "tutor_id" not in out.columns:
            raise ValueError("Coluna 'tutor_id' não existe no DataFrame.")

        out = out.dropna(subset=["tutor_id"])
        out["tutor_id"] = pd.to_numeric(out["tutor_id"], errors="coerce").dropna().astype(int)

        for c in group_cols:
            if c not in out.columns:
                raise ValueError(f"Coluna obrigatória '{c}' não existe no DataFrame.")

        indicadores = []

        forum_cols_exist = any(col in out.columns for col in [
            "median_forums_response_hours",
            "mean_forums_response_hours",
            "total_response_forum",
            "num_response_fast_forum",
            "num_response_normal_forum",
            "num_response_late_forum",
        ])

        if forum_cols_exist:
            response_col = None
            if "median_forums_response_hours" in out.columns:
                response_col = "median_forums_response_hours"
            elif "mean_forums_response_hours" in out.columns:
                response_col = "mean_forums_response_hours"

            if "total_response_forum" in out.columns:
                out["total_response_forum"] = pd.to_numeric(out["total_response_forum"], errors="coerce").fillna(0).clip(lower=0)
            else:
                out["total_response_forum"] = (
                    pd.to_numeric(out.get("num_response_fast_forum", 0), errors="coerce").fillna(0)
                    + pd.to_numeric(out.get("num_response_normal_forum", 0), errors="coerce").fillna(0)
                    + pd.to_numeric(out.get("num_response_late_forum", 0), errors="coerce").fillna(0)
                ).clip(lower=0)

            out["forum_volume"] = np.log1p(out["total_response_forum"])

            out["forum_volume_norm"] = out.groupby(list(group_cols))["forum_volume"].transform(
                lambda s: self._minmax_norm(s, higher_is_better=True)
            )

            if response_col is not None:
                out[response_col] = pd.to_numeric(out[response_col], errors="coerce")
                out["forum_speed_norm"] = out.groupby(list(group_cols))[response_col].transform(
                    lambda s: self._minmax_norm(s, higher_is_better=False)  
                )
                out["forum_score"] = out[["forum_speed_norm", "forum_volume_norm"]].mean(axis=1)
            else:
                out["forum_score"] = out["forum_volume_norm"]

            indicadores.append("forum_score")

        access_cols_exist = any(col in out.columns for col in ["n_login_weekly", "score_access"])

        if access_cols_exist:
            if "n_login_weekly" in out.columns:
                out["n_login_weekly"] = pd.to_numeric(out["n_login_weekly"], errors="coerce").fillna(0).clip(lower=0)
                out["n_login_weekly_norm"] = out.groupby(list(group_cols))["n_login_weekly"].transform(
                    lambda s: self._minmax_norm(s, higher_is_better=True)
                )
            else:
                out["n_login_weekly_norm"] = np.nan

            if "score_access" in out.columns:
                out["score_access"] = pd.to_numeric(out["score_access"], errors="coerce")
                out["score_access_norm"] = out.groupby(list(group_cols))["score_access"].transform(
                    lambda s: self._minmax_norm(s, higher_is_better=True)
                )
            else:
                out["score_access_norm"] = np.nan

            out["access_score"] = out[["n_login_weekly_norm", "score_access_norm"]].mean(axis=1)
            indicadores.append("access_score")

        feedback_cols_exist = any(col in out.columns for col in ["percentage_feedback", "n_corrections_with_feedback"])

        if feedback_cols_exist:
            if "percentage_feedback" in out.columns:
                out["percentage_feedback"] = pd.to_numeric(out["percentage_feedback"], errors="coerce")
                out["percentage_feedback_norm"] = out.groupby(list(group_cols))["percentage_feedback"].transform(
                    lambda s: self._minmax_norm(s, higher_is_better=True)
                )
            else:
                out["percentage_feedback_norm"] = np.nan

            if "n_corrections_with_feedback" in out.columns:
                out["n_corrections_with_feedback"] = pd.to_numeric(out["n_corrections_with_feedback"], errors="coerce").fillna(0).clip(lower=0)
                out["n_corrections_with_feedback_norm"] = out.groupby(list(group_cols))["n_corrections_with_feedback"].transform(
                    lambda s: self._minmax_norm(s, higher_is_better=True)
                )
            else:
                out["n_corrections_with_feedback_norm"] = np.nan

            out["feedback_score"] = out[["percentage_feedback_norm", "n_corrections_with_feedback_norm"]].mean(axis=1)
            indicadores.append("feedback_score")

        if not indicadores:
            raise ValueError(
                "Não encontrei colunas suficientes para montar indicadores (forum/access/feedback) nesse DataFrame."
            )

        out["score_final"] = out[indicadores].mean(axis=1)

        out = out.sort_values(by="score_final", ascending=False)
        out.insert(0, "ranking", range(1, len(out) + 1))

        return out

    def subject_analysis(self, subject_id: int, version, connector, kind: str = "best-performance", limit: int = 10, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)

        wanted = [
            "institution_id", "version", "subject_id", "tutor_id",
            "median_forums_response_hours", "mean_forums_response_hours",
            "total_response_forum", "num_response_fast_forum", "num_response_normal_forum", "num_response_late_forum",
            "score_access", "n_login_weekly",
            "percentage_feedback", "n_corrections_with_feedback",
        ]
        cols = [getattr(t.c, c) for c in wanted if hasattr(t.c, c)]

        with engine.connect() as conn:
            query = (
                select(*cols)
                .where(t.c.institution_id == int(institution_id))
                .where(t.c.subject_id == int(subject_id))
            )
            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        ranked_df = self.build_local_ranking(df)

        df_names = self.mapper.fetch_tutors_names(connector, version, subject_id=subject_id)
        if isinstance(df_names, pd.DataFrame) and not df_names.empty:
            ranked_df = ranked_df.merge(df_names, on="tutor_id", how="left")

        if kind == "best-performance":
            return (ranked_df.sort_values("score_final", ascending=False).head(limit)[["full_name", "subject_id", "tutor_id"]])

        if kind == "at-risk":
            return (ranked_df.sort_values("score_final", ascending=True).head(limit)[["full_name", "subject_id", "tutor_id"]])

    def general_analysis(self, version, connector, institution_id: int = 1, kind: str = "best-performance", limit: int = 10):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)

        wanted = [
            "institution_id", "version", "subject_id", "tutor_id",
            "median_forums_response_hours", "mean_forums_response_hours",
            "total_response_forum", "num_response_fast_forum", "num_response_normal_forum", "num_response_late_forum",
            "score_access", "n_login_weekly",
            "percentage_feedback", "n_corrections_with_feedback",
        ]
        cols = [getattr(t.c, c) for c in wanted if hasattr(t.c, c)]

        with engine.connect() as conn:
            query = select(*cols).where(t.c.institution_id == int(institution_id))
            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        if not rows:
            return {"id": institution_id, "type": kind, "ranking": []}

        df = pd.DataFrame(rows)

        ranked_local = self.build_local_ranking(df)

        agg = (
            ranked_local.groupby("tutor_id", as_index=False)
            .agg(
                score_final=("score_final", "mean"),
                n_subjects=("subject_id", "nunique"),
                subjects=("subject_id", lambda s: list(pd.unique(s))),
            )
        )

        ascending = (kind == "at-risk")
        agg = agg.sort_values("score_final", ascending=ascending, na_position="last").head(limit)
        
        tutor_ids = agg["tutor_id"].dropna().astype(int).tolist()

        names_by_id = {}
        for tid in tutor_ids:
            df_name = self.fetch_tutors_names(connector, version, user_id=tid)  
            if not df_name.empty:
                names_by_id[tid] = df_name.iloc[0]["full_name"]
            else:
                names_by_id[tid] = None

        ranking = [
            {
                "tutor_id": int(r.tutor_id),
                "full_name": names_by_id.get(int(r.tutor_id)),
                "score_final": float(r.score_final) if r.score_final is not None else None,
                "n_subjects": int(r.n_subjects) if r.n_subjects is not None else 0,
                "subjects": [int(x) for x in (r.subjects or [])],
            }
            for r in agg.itertuples(index=False)
        ]

        return {"id": institution_id, "type": kind, "ranking": ranking}