import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def class_analysis(self, class_id, version, connector):
        df_class_info = self.mapper.fetch_class_info(connector, class_id, version)
        df_class_metrics = self.mapper.fetch_class_metrics(connector, class_id, version)

        class_info = df_class_info.iloc[0].to_dict() if not df_class_info.empty else {}
        class_metrics = df_class_metrics.iloc[0].to_dict() if not df_class_metrics.empty else {}

        aux = {
            "class": {
                "id": int(class_info.get("class_id")) if class_info.get("class_id") is not None else None,
                "name": class_info.get("name"),
                "abbrev": class_info.get("abrev"),
                "date": class_info.get("date"),
            },
            "metrics": {
                "total_enrolled": int(class_metrics.get("total_enrolled") or 0),
                "avg_grade_all": float(class_metrics.get("avg_grade_all")) if class_metrics.get("avg_grade_all") is not None else None,
                "taxa_aprovacao": float(class_metrics.get("taxa_aprovacao")) if class_metrics.get("taxa_aprovacao") is not None else None,
            },
        }

        print("CHEGOU!")
        print(aux)

        return aux
