import pandas as pd
import numpy as np
import time
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class Tutor_General_Subjects_Indicators:
    def __init__(self, mapper):
        self.mapper = mapper
        self.db_admin = DatabaseAdmin()

    def tutors_general_subjects_indicators(self, version, connector, institution_id=1):
        df_flags = self._fetch_flags_general(institution_id)
        df_subjects_info = self.mapper.fetch_subjects_summary_tutors(connector, version)
        
        for col in ["total_students", "total_tutors", "students_per_tutor"]:
            if col in df_subjects_info.columns:
                df_subjects_info[col] = pd.to_numeric(df_subjects_info[col], errors="coerce")

        subjects_info = {
            int(row["subject_id"]): {
                "name": row.get("name"),
                "abbrev": row.get("abbrev"),
                "teachers": row.get("teachers"),
                "total_students": int(row["total_students"] or 0) if pd.notna(row["total_students"]) else 0,
                "total_tutors": int(row["total_tutors"] or 0) if pd.notna(row["total_tutors"]) else 0,
                "students_per_tutor": float(row["students_per_tutor"]) if pd.notna(row["students_per_tutor"]) else None,
            }
            for _, row in df_subjects_info.iterrows()
        }

        subjects = []
        for row in df_flags:
            subject_id = int(row["subject_id"])
            info = subjects_info.get(subject_id, {
                "name": None,
                "abbrev": None,
                "teachers": None,
                "total_students": 0,
                "total_tutors": 0,
                "students_per_tutor": None,
            })

            subjects.append({
                "id": subject_id,
                "name": info["name"],
                "abbrev": info["abbrev"],
                "teachers": info["teachers"],

                "total_students": info["total_students"],
                "total_tutors": info["total_tutors"],
                "students_per_tutor": info["students_per_tutor"],

                "label_global_forum": row["label_global_forum"],
                "label_global_access": row["label_global_access"],
                "label_global_feedback": row["label_global_feedback"],
            })

        return {"subjects": subjects}
    
    def _fetch_flags_general(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        global_indicators_tutors = Table("global_indicators_tutors", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    global_indicators_tutors.c.subject_id,
                    global_indicators_tutors.c.label_global_forum,
                    global_indicators_tutors.c.label_global_access,
                    global_indicators_tutors.c.label_global_feedback,
                )
                .where(global_indicators_tutors.c.institution_id == institution_id)
            )

            rows = conn.execute(query).mappings().all()

        return rows