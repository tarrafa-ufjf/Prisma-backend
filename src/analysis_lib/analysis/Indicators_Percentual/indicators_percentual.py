import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table, select
from database import DatabaseAdmin

class Indicators_Percentual(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()  

    def subject_analysis(self, subject_id):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        engajamento_global = Table("engajamento_global", metadata, autoload_with=engine)

        with engine.connect() as conn:
            q = (
                select(
                    engajamento_global.c.institution_id,
                    engajamento_global.c.subject_id,
                    engajamento_global.c.muito_baixo,
                    engajamento_global.c.baixo,
                    engajamento_global.c.medio,
                    engajamento_global.c.alto,
                    engajamento_global.c.muito_alto,
                )
                .where(engajamento_global.c.institution_id == 1)
                .where(engajamento_global.c.subject_id == int(subject_id))
            )
            rows = conn.execute(q).mappings().all()

        df = pd.DataFrame(rows)
        return {
            "subject": {
                "id": int(subject_id),
                "engagement": df.to_dict(orient="records")
            }
        }