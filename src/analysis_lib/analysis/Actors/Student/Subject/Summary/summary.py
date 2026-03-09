import pandas as pd
import numpy as np
from .....indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table
class Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def subject_analysis(self, subject_id, version, connector):
        df_subject_info = self.mapper.fetch_subject_info(connector, subject_id, version)
        df_total_enrollment = self.mapper.fetch_total_enrollment(connector, subject_id, version)
        
        performance = Performance(self.mapper)
        df_perf = performance.course_analysis(subject_id, version, connector, True)

        if not df_perf.empty and "grade_final" in df_perf.columns:
            avg_grade_all = float(df_perf["grade_final"].mean(skipna=True))
        else:
            avg_grade_all = 0.0

        approval_rate = 0.0
        if not df_perf.empty:
            mask_valid = df_perf['situacao'].isin(["Aprovado", "Reprovado", "RI"])
            total_valid = int(mask_valid.sum())

            if total_valid > 0:
                approved_count = int(
                    (df_perf['situacao'] == "Aprovado").where(mask_valid, False).sum()
                )
                approval_rate = float(approved_count) / float(total_valid)

        subject_info = df_subject_info.iloc[0].to_dict() if not df_subject_info.empty else {}
        total_enrollment = df_total_enrollment.iloc[0].to_dict() if not df_total_enrollment.empty else {}

        return {
            "subject": {
                "id": int(subject_info.get("subject_id")) if subject_info.get("subject_id") is not None else None,
                "name": subject_info.get("name"),
                "abbrev": subject_info.get("abrev"),
                "date": subject_info.get("date"),
            },
            "metrics": {
                "total_enrolled": int(total_enrollment.get("total_enrolled") or 0),
                "avg_grade_all": avg_grade_all,
                "approval_rate": approval_rate * 100, 
            },
        }
