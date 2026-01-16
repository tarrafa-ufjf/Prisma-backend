import pandas as pd
from ......indicator import Indicator
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class Response_Forums(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()
    
    def student_analysis(self, subject_id, tutor_id, version, connector, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)


        with engine.connect() as conn:
            query = (
                select(
                    t.c.institution_id,
                    t.c.subject_id,
                    t.c.tutor_id,
                    t.c.label_forums_response,
                )
                .where(t.c.institution_id == institution_id)
                .where(t.c.subject_id == int(subject_id))
                .where(t.c.tutor_id == int(tutor_id))
            )

            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            row = conn.execute(query).mappings().first()
            if not row:
                return None

            row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
            return row
        
    def get_response_foruns_metrics(self, subject_id, version, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    t.c.institution_id,
                    t.c.subject_id,
                    t.c.tutor_id,
                    t.c.median_forums_response_hours,
                    t.c.mean_forums_response_hours,
                    t.c.label_forums_response,
                    t.c.num_response_fast_forum,
                    t.c.num_response_late_forum,
                    t.c.num_response_normal_forum,
                )
                .where(t.c.institution_id == institution_id)
                .where(t.c.subject_id == int(subject_id))
            )

            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        return pd.DataFrame(rows)

    def subject_analysis(self, subject_id, version, connector):
        df_response_foruns = self.get_response_foruns_metrics(subject_id, version)

        if df_response_foruns is None:
            df_response_foruns = pd.DataFrame()

        df_names = self.mapper.fetch_tutors_names(connector, version, subject_id)

        if df_names is None:
            df_names = pd.DataFrame()
        elif not isinstance(df_names, pd.DataFrame):
            df_names = pd.DataFrame(df_names)

        if df_response_foruns.empty:
            return df_response_foruns

        out = df_response_foruns.merge(df_names, on="tutor_id", how="left")
        return out
