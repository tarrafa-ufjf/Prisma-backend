import pandas as pd
import numpy as np
from ..indicator import Indicator
from ..Desempenho.performance import Performance

class Info_Graphs(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def _build_situations(self, df: pd.DataFrame):
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
        df_pct_usage_resource = self.mapper.get_pct_usage_resource(connector, subject_id, version)
        usage_by_module = df_pct_usage_resource.to_dict(orient="records") if not df_pct_usage_resource.empty else []

        performance = Performance(self.mapper)
        df_perf = performance.discretized_performance(subject_id, version, connector)
        situations = self._build_situations(df_perf)

        return {
            "subject": {
                "id": subject_id,
                "usage_by_module": usage_by_module,
                "situations": situations
            }
        }