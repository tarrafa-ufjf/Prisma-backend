import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Info_Graphs(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def info_graphs(self, subject_id, version, connector):
        df_pct_usage_resource = self.mapper.get_pct_usage_resource(connector, subject_id, version)
        # df_student_status_counts = self.mapper.get_student_status_counts(connector, subject_id, version)

        usage_by_module = df_pct_usage_resource.to_dict(orient="records") if not df_pct_usage_resource.empty else []
        
        return {
            "subject": {
                "id": subject_id,
                "usage_by_module": usage_by_module
            }
        }