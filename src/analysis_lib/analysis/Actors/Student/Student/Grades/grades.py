import pandas as pd
import numpy as np
from ....indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table
    
class Student_Grades(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def subject_analysis(self, subject_id, student_id, version, connector):
        df = self.mapper.fetch_student_grades(subject_id, student_id, connector, version)

        if df.empty:
            return {
                "student_grades": {
                    "id": None, "name": None,
                    "final": {"max": None, "grade": None},
                    "activities": []
                }
            }

        df_final = df[df["item_type"] == "course"].copy()
        final = {
            "max": float(df_final["grade_max"].iloc[0]) if not df_final.empty else None,
            "grade": float(df_final["grade_real"].iloc[0]) if not df_final.empty else None,
        }

        df_acts = df[df["item_type"] == "mod"].copy()
        activities = [
            {
                "activity_name": (row["activity_name"] or "").strip(),
                "grade_max": float(row["grade_max"]) if row["grade_max"] is not None else None,
                "grade_real": float(row["grade_real"]) if row["grade_real"] is not None else None,
            }
            for _, row in df_acts.iterrows()
        ]

        return {
            "student_grades": {
                "id": int(df["id"].iloc[0]),
                "name": df["name"].iloc[0],
                "final": final,
                "activities": activities
            }
        }

