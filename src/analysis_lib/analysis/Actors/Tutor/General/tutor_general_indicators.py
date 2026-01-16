import pandas as pd
import numpy as np
import time
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class General_indicators:
    def __init__(self, mapper):
        self.mapper = mapper
        self.db_admin = DatabaseAdmin()

    def general_indicators(self, version, connector, institution_id: int = 1):
        rows = self._fetch_flags_general(institution_id)

        if not rows:
            return {
                "forum_response": {"good_percentage": 0},
                "access": {"good_percentage": 0},
            }

        df = pd.DataFrame(rows)
        total_subjects = len(df)

        good_labels = ("alto", "muito_alto")

        def compute_good(col_name: str):
            series = df[col_name].fillna("").astype(str).str.strip().str.lower()
            good_count = int(series.isin(good_labels).sum())
            if total_subjects == 0:
                pct = 0
            else:
                pct = int(round(100 * good_count / total_subjects))
            return {
                "good_percentage": pct
            }

        return {
            "forum_response": compute_good("label_forum_response"),
            "access": compute_good("label_access"),
        }

    def _fetch_flags_general(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        global_indicators_tutors = Table("global_indicators_tutors", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    global_indicators_tutors.c.subject_id,
                    global_indicators_tutors.c.label_forum_response,
                    global_indicators_tutors.c.label_access,
                )
                .where(global_indicators_tutors.c.institution_id == institution_id)
            )

            rows = conn.execute(query).mappings().all()

        return rows
