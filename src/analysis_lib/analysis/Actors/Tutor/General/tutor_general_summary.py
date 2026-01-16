import pandas as pd
import numpy as np
import time
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class General_summary:
    def __init__(self, mapper):
        self.mapper = mapper
        self.db_admin = DatabaseAdmin()

    def general_summary(self, version, connector, institution_id: int = 1):
        df = self.mapper.fetch_institution_info_tutors(connector, version)  

        info = df.iloc[0].to_dict() if not df.empty else {}

        return {
            "total_tutors": float(info.get("total_tutors") or 0),
            "mean_tutors_per_degree_program": float(info.get("mean_tutors_per_degree_program") or 0),
            "mean_tutors_per_subject": float(info.get("mean_tutors_per_subject") or 0),
        }