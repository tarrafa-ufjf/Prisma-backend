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
        df = self.mapper.fetch_institution_info(connector, version)  

        info = df.iloc[0].to_dict() if not df.empty else {}

        return {
            "total_users": int(info.get("total_users") or 0),
            "total_courses_offered": int(info.get("total_courses_offered") or 0),
            "total_subjects": int(info.get("total_subjects") or 0),
        }