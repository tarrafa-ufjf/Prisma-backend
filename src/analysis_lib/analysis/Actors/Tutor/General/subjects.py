import pandas as pd
import numpy as np
from ....indicator import Indicator
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func, and_
import time

class Subjects(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def _epoch_to_period(self, ts) -> str | None:
        if ts is None or pd.isna(ts):
            return None
        try:
            t = time.gmtime(int(ts))
        except Exception:
            return None
        return f"{t.tm_year}.{t.tm_mon}"


    def get_subjects(self, version, connector, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        subjects_status = Table("subjects_status", metadata, autoload_with=engine)

        # Buscar subject_ids válidos (status 'D' e com start/end)
        with engine.connect() as conn:
            query = (
                select(
                    subjects_status.c.subject_id,
                    subjects_status.c.start_date,
                    subjects_status.c.end_date,
                )
                .where(
                    and_(
                        subjects_status.c.institution_id == institution_id,
                        subjects_status.c.status == "D",
                        subjects_status.c.start_date.isnot(None),
                        subjects_status.c.end_date.isnot(None),
                    )
                )
            )
            status_rows = conn.execute(query).mappings().all()

        df_status = pd.DataFrame(status_rows)
        if df_status.empty:
            return {"subjects": []}

        # Puxar todas as disciplinas do Moodle e calcular period
        all_subjects = self.mapper.get_all_subjects(connector, version)
        if all_subjects is None or all_subjects.empty:
            return {"subjects": []}

        all_subjects = all_subjects.copy()
        all_subjects["period"] = all_subjects["startdate"].apply(self._epoch_to_period)

        # Filtrar somente as disciplinas presentes em subject_status
        df_valid = df_status.merge(all_subjects, left_on="subject_id", right_on="id", how="inner")

        records = df_valid[["id", "fullname", "shortname", "period"]].to_dict(orient="records")
        return {"subjects": records}