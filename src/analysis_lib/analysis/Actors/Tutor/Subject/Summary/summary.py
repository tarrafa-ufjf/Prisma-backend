import pandas as pd
import numpy as np
from .....indicator import Indicator
from sqlalchemy import MetaData, Table, select, and_
from database import DatabaseAdmin

class Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def fetch_subject_window(self, institution_id: int, subject_id: int):
        engine = self.db_admin.get_connector()
        metadata = MetaData()

        subjects_status = Table("subjects_status", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    subjects_status.c.start_date,
                    subjects_status.c.end_date,
                    subjects_status.c.status,
                )
                .where(
                    and_(
                        subjects_status.c.institution_id == institution_id,
                        subjects_status.c.subject_id == subject_id,
                        subjects_status.c.status == "D",
                    )
                )
                .limit(1)
            )

            row = conn.execute(query).mappings().first()

        return row
    
    def subject_analysis(self, subject_id, version, connector):
        row = self.fetch_subject_window(institution_id=1, subject_id=subject_id)

        if not row or row["start_date"] is None or row["end_date"] is None:
            return {
                "subject": {
                    "id": subject_id,
                    "error": "start_date/end_date não definida ainda subjects_status, esperar o processamento"
                }
            }

        start_date = row["start_date"]
        end_date = row["end_date"]
        
        df_subject_info = self.mapper.fetch_subject_info_tutors(connector, version, subject_id, start_date, end_date)

        subject_info = df_subject_info.iloc[0].to_dict() if not df_subject_info.empty else {}

        return {
            "subject": {
                "id": int(subject_info.get("subject_id")) if subject_info.get("subject_id") is not None else None,
                "total_tutors": subject_info.get("total_tutors"),
                "students_per_tutor": subject_info.get("students_per_tutor"),
                "average_logs_per_day_per_tutor": subject_info.get("average_logs_per_day_per_tutor"),
            }
        }
