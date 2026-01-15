import pandas as pd
from ......indicator import Indicator
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class Access(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def student_analysis(self, subject_id, student_id, version, connector):
        return None

    def get_access_metrics(self, subject_id, version, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    t.c.institution_id,
                    t.c.subject_id,
                    t.c.tutor_id,
                    t.c.n_login,
                    t.c.label_access,
                    t.c.mean_weekly_course_views_window,
                )
                .where(t.c.institution_id == institution_id)
                .where(t.c.subject_id == int(subject_id))
            )

            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            rows = conn.execute(query).mappings().all()

        return pd.DataFrame(rows)

    def subject_analysis(self, subject_id, version, connector):
        df_access = self.get_access_metrics(subject_id, version)

        if df_access is None:
            df_access = pd.DataFrame()

        df_names = self.mapper.fetch_tutors_names(connector, version, subject_id)

        if df_names is None:
            df_names = pd.DataFrame()
        elif not isinstance(df_names, pd.DataFrame):
            df_names = pd.DataFrame(df_names)

        if df_access.empty:
            return df_access

        out = df_access.merge(df_names, on="tutor_id", how="left")
        return out
