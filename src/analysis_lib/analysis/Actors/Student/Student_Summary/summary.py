import pandas as pd
import numpy as np
from ....indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Student_Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def subject_analysis(self, subject_id, student_id, version, connector):
        df_student_summary_info = self.mapper.fetch_student_summary(subject_id, student_id, connector, version)
        
        student_summary_info = df_student_summary_info.iloc[0].to_dict() if not df_student_summary_info.empty else {}

        return {
            "student_summary": {
                "id": int(student_summary_info.get("id")) if student_summary_info.get("id") is not None else None,
                "name": student_summary_info.get("name"),
                "email": student_summary_info.get("email"),
                "city": student_summary_info.get("city"),
                "first_access_moodle": student_summary_info.get("first_access_moodle"),
                "last_access_subject": student_summary_info.get("last_access_subject"),
                "student_groups": student_summary_info.get("student_groups"),
                "degree_program": student_summary_info.get("degree_program"),
            }
        }

