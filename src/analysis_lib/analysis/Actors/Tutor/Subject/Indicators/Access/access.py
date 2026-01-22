import pandas as pd
from ......indicator import Indicator
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select, func

class Access(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def get_label_access(self, subject_id, tutor_id, version, institution_id):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table("local_indicators_tutors", metadata, autoload_with=engine)


        with engine.connect() as conn:
            query = (
                select(
                    t.c.institution_id,
                    t.c.subject_id,
                    t.c.tutor_id,
                    t.c.label_access,
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
    
    def tutors_analysis(self, subject_id, tutor_id, version, connector, route, institution_id: int = 1):
        if route == 'indicators':
            df_access = self.get_label_access(subject_id, tutor_id, version, institution_id)
            return df_access
        if route == 'access':
            df_access = self.get_access_metrics(subject_id, version, institution_id, tutor_id)
            return df_access

    def get_access_metrics(self, subject_id, version, institution_id: int = 1, tutor_id=None):
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
                    t.c.n_login_subject,
                    t.c.n_login_weekly,
                    t.c.n_login_label,
                    t.c.n_login_weekly_label,
                    t.c.label_access,
                    t.c.maximum_inactivity_days,
                    t.c.maximum_inactivity_days_label,
                )
                .where(t.c.institution_id == institution_id)
                .where(t.c.subject_id == int(subject_id))
            )

            if tutor_id is not None:
                query = query.where(t.c.tutor_id == int(tutor_id))

            if version is not None and hasattr(t.c, "version"):
                query = query.where(t.c.version == str(version))

            if tutor_id is not None:
                row = conn.execute(query).mappings().first()
                if not row:
                    return None
                return {k: (None if pd.isna(v) else v) for k, v in row.items()}

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
