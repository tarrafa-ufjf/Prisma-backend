import pandas as pd
import numpy as np
import time
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func
from ..Subject.Indicators.Performance.performance import Performance

class General_subjects_indicators:
    def __init__(self, mapper):
        self.mapper = mapper
        self.db_admin = DatabaseAdmin()

    def general_subjects_indicators(self, version, connector, institution_id=1):
        df_flags = self._fetch_flags_general(institution_id)
        df_subjects_summary= self.mapper.fetch_subjects_summary(connector, version)

        subjects_info = {
            int(row["subject_id"]): {
                "name": row["name"],
                "abrev": row["abrev"],
                "teachers": row["teachers"],
                "total_enrolled": int(row["total_enrolled"] or 0),
            }
            for _, row in df_subjects_summary.iterrows()
        }

        performance = Performance(self.mapper)
        subjects = []
        for row in df_flags:
            subject_id = int(row["subject_id"])

            df_perf = performance.status_students_analysis(version, connector, subject_id)

            if df_perf.empty:
                situations = [
                    {"qtd": 0, "situacao": "Aprovado"},
                    {"qtd": 0, "situacao": "Reprovado"},
                    {"qtd": 0, "situacao": "RI"},
                ]
            else:
                r = df_perf.loc[:, ["Aprovado", "Reprovado", "RI"]].iloc[0].astype(int)
                situations = [
                    {"qtd": int(r["Aprovado"]),  "situacao": "Aprovado"},
                    {"qtd": int(r["Reprovado"]), "situacao": "Reprovado"},
                    {"qtd": int(r["RI"]),        "situacao": "RI"},
                ]

            info = subjects_info.get(subject_id, {"name": None, "abrev": None, "teachers": None, "total_enrolled": 0})

            subjects.append({
                "id": subject_id,
                "name": info["name"],
                "abbrev": info["abrev"],
                "teachers": info["teachers"],
                "total_enrolled": info["total_enrolled"],

                "label_engagement": row["label_engagement"],
                "label_motivation": row["label_motivation"],
                "label_performance": row["label_performance"],
                "label_cognitive": row["label_cognitive"],
                "label_relation_teacher_student": row["label_relation_teacher_student"],
                "label_give_up": row["label_give_up"],

                "situations": situations,
                "mean_subject": row["mean_grade_performance"],
            })

        return {"subjects": subjects}
    
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
                    global_indicators_student.c.mean_grade_performance
                )
                .where(global_indicators_student.c.institution_id == institution_id)
            )

            rows = conn.execute(query).mappings().all()

        return rows