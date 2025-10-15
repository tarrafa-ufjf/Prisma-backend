import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def subject_analysis(self, subject_id, version, connector):
        df_subject_info = self.mapper.fetch_subject_info(connector, subject_id, version)
        df_subject_metrics = self.mapper.fetch_subject_metrics(connector, subject_id, version)

        subject_info = df_subject_info.iloc[0].to_dict() if not df_subject_info.empty else {}
        subject_metrics = df_subject_metrics.iloc[0].to_dict() if not df_subject_metrics.empty else {}

        return {
            "subject": {
                "id": int(subject_info.get("subject_id")) if subject_info.get("subject_id") is not None else None,
                "name": subject_info.get("name"),
                "abbrev": subject_info.get("abrev"),
                "date": subject_info.get("date"),
            },
            "metrics": {
                "total_enrolled": int(subject_metrics.get("total_enrolled") or 0),
                "avg_grade_all": float(subject_metrics.get("avg_grade_all")) if subject_metrics.get("avg_grade_all") is not None else None,
                "taxa_aprovacao": float(subject_metrics.get("taxa_aprovacao")) if subject_metrics.get("taxa_aprovacao") is not None else None,
            },
        }
