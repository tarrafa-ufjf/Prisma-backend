import pandas as pd
import numpy as np
from ....indicator import Indicator
import time

class Subjects(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def _epoch_to_period(self, ts) -> str | None:
        if ts is None or pd.isna(ts):
            return None
        try:
            t = time.gmtime(int(ts))
        except Exception:
            return None
        return f"{t.tm_year}.{t.tm_mon}"


    def get_subjects(self, version, connector):
        all_subjects = self.mapper.get_all_subjects(connector, version)
        return self._format_subjects(all_subjects)

    def _format_subjects(self, all_subjects):
        all_subjects["period"] = all_subjects["startdate"].apply(self._epoch_to_period)

        records = all_subjects[["id", "fullname", "shortname", "period"]].to_dict(orient="records") if not all_subjects.empty else []

        return {"subjects": records}

    def get_daily_active_subjects(self, version, connector):
        all_subjects = self.mapper.get_daily_active_subjects(connector, version)

        return self._format_subjects(all_subjects)

    def get_week_active_subjects(self, version, connector):
        all_subjects = self.mapper.get_week_active_subjects(connector, version)

        return self._format_subjects(all_subjects)

    def get_month_active_subjects(self, version, connector):
        all_subjects = self.mapper.get_month_active_subjects(connector, version)

        return self._format_subjects(all_subjects)
