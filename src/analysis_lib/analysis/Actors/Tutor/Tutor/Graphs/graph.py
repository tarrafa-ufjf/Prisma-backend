import pandas as pd
import numpy as np
from sqlalchemy import MetaData, Table, select

from .....indicator import Indicator
from database import DatabaseAdmin


class Graph(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def subject_analysis(self, subject_id, tutor_id, version, connector, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)

        with engine.connect() as conn:
            exists_q = (
                select(t.c.tutor_id)
                .where(t.c.institution_id == int(institution_id))
                .where(t.c.subject_id == int(subject_id))
                .where(t.c.tutor_id == int(tutor_id))
            )
            if version is not None and hasattr(t.c, "version"):
                exists_q = exists_q.where(t.c.version == str(version))

            tutor_row = conn.execute(exists_q).first()
            if tutor_row is None:
                return {"error": "tutor_not_found"}

            query = (
                select(
                    t.c.tutor_id,
                    t.c.score,
                    t.c.mean_forums_response_hours,
                )
                .where(t.c.institution_id == int(institution_id))
                .where(t.c.subject_id == int(subject_id))
            )
            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        df = pd.DataFrame(rows)
        if df.empty:
            return {
                "interactions": {"points": [], "mean": None, "median": None},
                "response_time_hours": {"points": [], "mean": None, "median": None},
            }

        def build_metric(df_in: pd.DataFrame, col: str, clamp_0_100: bool):
            d = df_in[["tutor_id", col]].copy()
            d[col] = pd.to_numeric(d[col], errors="coerce")
            d = d.dropna(subset=[col])
            if d.empty:
                return {"points": [], "mean": None, "median": None}

            if clamp_0_100:
                d[col] = d[col].clip(0, 100)

            values = d[col].to_numpy(dtype=float)
            mean = float(np.mean(values))
            median = float(np.median(values))

            points = [
                {
                    "tutor_id": int(r["tutor_id"]),
                    "value": float(r[col]),
                    "is_current": int(r["tutor_id"]) == int(tutor_id),
                }
                for _, r in d.iterrows()
            ]
            return {"points": points, "mean": mean, "median": median}

        interactions = build_metric(df, "score", clamp_0_100=True)

        response_time = build_metric(df, "mean_forums_response_hours", clamp_0_100=False)

        return {
            "interactions": interactions,
            "response_time_hours": response_time,
        }