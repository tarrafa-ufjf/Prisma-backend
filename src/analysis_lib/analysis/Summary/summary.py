import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def course_analysis(self, course_id, version, connector):
        df_course_info = self.mapper.fetch_course_info(connector, course_id, version)
        df_course_metrics = self.mapper.fetch_course_metrics(connector, course_id, version)

        course_info = df_course_info.iloc[0].to_dict() if not df_course_info.empty else {}
        course_metrics = df_course_metrics.iloc[0].to_dict() if not df_course_metrics.empty else {}

        aux = {
            "course": {
                "id": int(course_info.get("course_id")) if course_info.get("course_id") is not None else None,
                "name": course_info.get("name"),
                "abbrev": course_info.get("abrev"),
                "date": course_info.get("date"),
            },
            "metrics": {
                "total_enrolled": int(course_metrics.get("total_enrolled") or 0),
                "avg_grade_all": float(course_metrics.get("avg_grade_all")) if course_metrics.get("avg_grade_all") is not None else None,
                "taxa_aprovacao": float(course_metrics.get("taxa_aprovacao")) if course_metrics.get("taxa_aprovacao") is not None else None,
            },
        }

        print("CHEGOU!")
        print(aux)

        return aux
