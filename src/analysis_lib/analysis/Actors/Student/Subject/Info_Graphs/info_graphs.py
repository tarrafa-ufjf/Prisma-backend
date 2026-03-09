import pandas as pd
import numpy as np
from .....indicator import Indicator
from ..Indicators.Performance.performance import Performance

class Info_Graphs(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def _build_situations(self, df):
        if df is None or df.empty:
            return [
                {"situacao": "Reprovado", "qtd": 0},
                {"situacao": "RI",        "qtd": 0},
                {"situacao": "Aprovado",  "qtd": 0},
            ]

        col_candidates = {
            "Aprovado":  ["qtd_aprovado", "aprovado", "count_aprovado"],
            "Reprovado": ["qtd_reprovado", "reprovado", "count_reprovado"],
            "RI":        ["qtd_ri", "ri", "count_ri"],
        }

        def sum_col(cnames):
            for c in cnames:
                if c in df.columns:
                    return int(pd.to_numeric(df[c], errors="coerce").fillna(0).sum())
            if "status" in df.columns:
                label = cnames[0].split("_")[-1]  # pega "aprovado"/"reprovado"/"ri"
                return int((df["status"].astype(str).str.lower() == label.lower()).sum())
            return 0

        return [
            {"situacao": "Reprovado", "qtd": sum_col(col_candidates["Reprovado"])},
            {"situacao": "RI",        "qtd": sum_col(col_candidates["RI"])},
            {"situacao": "Aprovado",  "qtd": sum_col(col_candidates["Aprovado"])},
        ]

    def info_graphs(self, subject_id, version, connector):
        df_pct_usage_resource = pd.DataFrame(self.mapper.get_pct_usage_resource(connector, subject_id, version))
        usage_by_module = [] if df_pct_usage_resource.empty else df_pct_usage_resource.to_dict(orient="records")

        performance = Performance(self.mapper)
        df_perf = performance.status_students_analysis(version, connector, subject_id)

        if df_perf.empty:
            situations = [
                {"qtd": 0, "situacao": "Aprovado"},
                {"qtd": 0, "situacao": "Reprovado"},
                {"qtd": 0, "situacao": "RI"},
            ]
        else:
            row = df_perf.loc[:, ["Aprovado", "Reprovado", "RI"]].iloc[0].astype(int)
            situations = [
                {"qtd": int(row["Aprovado"]),  "situacao": "Aprovado"},
                {"qtd": int(row["Reprovado"]), "situacao": "Reprovado"},
                {"qtd": int(row["RI"]),        "situacao": "RI"},
            ]

        return {
            "subject": {
                "id": subject_id,
                "usage_by_module": usage_by_module,
                "situations": situations
            }
        }