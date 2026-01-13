import pandas as pd
import numpy as np
from .....indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def subject_analysis(self, subject_id, version, connector):
        df_subject_info = self.mapper.fetch_subject_info_tutors(connector, version, subject_id)

        subject_info = df_subject_info.iloc[0].to_dict() if not df_subject_info.empty else {}

        return {
            "subject": {
                "id": int(subject_info.get("subject_id")) if subject_info.get("subject_id") is not None else None,
                "total_tutors": subject_info.get("total_tutors"),
                "students_per_tutor": subject_info.get("students_per_tutor"),
                "average_logs_per_day_per_tutor": subject_info.get("average_logs_per_day_per_tutor"),
            }
        }
