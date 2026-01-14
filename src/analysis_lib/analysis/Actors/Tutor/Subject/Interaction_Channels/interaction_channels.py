import pandas as pd
import numpy as np
from .....indicator import Indicator
from sqlalchemy import MetaData, Table, select, and_
from database import DatabaseAdmin

class Interaction_Channels(Indicator):
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
                    )
                )
                .limit(1)
            )

            row = conn.execute(query).mappings().first()

        return row

    def subject_analysis(self, subject_id, version, connector):
        row = self.fetch_subject_window(institution_id=1, subject_id=subject_id)

        if (not row):
            return {
                "subject": {
                    "id": int(subject_id),
                    "channels": [],
                    "message": "start_date/end_date não definida em subjects_status; aguarde o processamento",
                }
            }

        status = (row.get("status") or "").strip()
        start_date = row["start_date"]
        end_date = row["end_date"]

        if status != "D":
            return {
                "subject": {
                    "id": int(subject_id),
                    "channels": [],
                    "message": "ainda em processamento (status != D); aguarde",
                }
            }

        if start_date is None or end_date is None:
            return {
                "subject": {
                    "id": int(subject_id),
                    "channels": [],
                    "message": "processado (status=D), mas não há janela de fórum definida / sem atividade",
                }
            }
            
        df = self.mapper.fetch_forum_messages_counts(version, connector, subject_id, start_date, end_date)
        
        if df is None or df.empty:
            return {
                "subject": {
                    "id": int(subject_id),
                    "channels": [],
                    "message": "não há mensagens em fóruns no período",
                }
        }

        channels = df.where(pd.notna(df), None).to_dict(orient="records")

        return {
            "subject": {
                "id": int(subject_id),
                "channels": channels,
            }
        }