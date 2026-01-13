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
                "engagement": {"good_percentage": 0, "good_subjects": 0, "total_subjects": 0},
                "motivation": {"good_percentage": 0, "good_subjects": 0, "total_subjects": 0},
                "performance": {"good_percentage": 0, "good_subjects": 0, "total_subjects": 0},
                "cognitive": {"good_percentage": 0, "good_subjects": 0, "total_subjects": 0},
                "relation_teacher_student": {"good_percentage": 0, "good_subjects": 0, "total_subjects": 0},
                "give_up": {"good_percentage": 0, "good_subjects": 0, "total_subjects": 0},
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
                "good_percentage": pct,          
                "good_subjects": good_count,    
                "total_subjects": total_subjects 
            }

        return {
            "engagement": compute_good("label_engagement"),
            "motivation": compute_good("label_motivation"),
            "performance": compute_good("label_performance"),
            "cognitive": compute_good("label_cognitive"),
            "relation_teacher_student": compute_good("label_relation_teacher_student"),
            "give_up": compute_good("label_give_up"), 
        }

    def _fetch_flags_general(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        global_indicators_student = Table("global_indicators_student", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    global_indicators_student.c.subject_id,
                    global_indicators_student.c.label_engagement,
                    global_indicators_student.c.label_motivation,
                    global_indicators_student.c.label_performance,
                    global_indicators_student.c.label_cognitive,
                    global_indicators_student.c.label_relation_teacher_student,
                    global_indicators_student.c.label_give_up,
                )
                .where(global_indicators_student.c.institution_id == institution_id)
            )

            rows = conn.execute(query).mappings().all()

        return rows
