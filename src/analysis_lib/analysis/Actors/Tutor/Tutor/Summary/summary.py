import pandas as pd
import numpy as np
from .....indicator import Indicator

class Tutor_Summary(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def subject_analysis(self, subject_id, tutor_id, version, connector):
        df = self.mapper.fetch_tutor_summary(subject_id, tutor_id, connector, version)

        if df is None or df.empty:
            return {"tutor_summary": {}}

        row = df.iloc[0].to_dict()

        def pick(*keys, default=None):
            """Pega o primeiro valor não-nulo (e não-NaN) dentre as chaves."""
            for k in keys:
                if k in row:
                    v = row.get(k)
                    if v is None:
                        continue
                    if isinstance(v, float) and np.isnan(v):
                        continue
                    return v
            return default

        tutor_id_val = pick("tutor_id", "id")
        tutor_name = pick("full_name", "name")
        tutor_email = pick("email")
        tutor_city = pick("city")  
        first_access_moodle = pick("first_access_moodle", "tutor_since")
        last_access_subject = pick("last_access_subject", "last_access")
        tutor_groups = pick("tutor_groups", "tutor_group")  
        degree_program = pick("degree_program")

        return {
            "tutor_summary": {
                "id": int(tutor_id_val) if tutor_id_val is not None else None,
                "name": tutor_name,
                "email": tutor_email,
                "city": tutor_city,
                "first_access_moodle": first_access_moodle,
                "last_access_subject": last_access_subject,
                "tutor_groups": tutor_groups,
                "degree_program": degree_program,
            }
        }