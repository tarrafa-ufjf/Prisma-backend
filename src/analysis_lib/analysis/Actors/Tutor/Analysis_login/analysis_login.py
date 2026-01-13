import pandas as pd
import numpy as np
import math
from ....indicator import Indicator

class Analysis_login(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def tutors_analysis(self, subject_id, student_id, version, connector):
        print("Chegou student")
        return None
    
    def _discretize_by_quantiles(self, s, labels=("Ruim", "Médio", "Bom", "Ótimo")):
        s = pd.to_numeric(s, errors="coerce").fillna(0)

        # Caso especial: todos iguais
        if s.nunique() <= 1:
            return pd.Series([labels[1]] * len(s), index=s.index)

        try:
            out = pd.qcut(s.rank(method="average"), q=4, labels=labels, duplicates="drop")
            return out.astype(str).replace("nan", labels[1])

        except ValueError:
            n_unique = s.nunique()
            q = min(4, n_unique) 
            try:
                out = pd.qcut(s.rank(method="average"), q=q, labels=labels[:q], duplicates="drop")
                return out.astype(str).replace("nan", labels[1])
            except Exception:
                # Último recurso: percentis manuais
                p25, p50, p75 = np.percentile(s, [25, 50, 75])
                def f(x):
                    if x <= p25: return labels[0]
                    if x <= p50: return labels[1]
                    if x <= p75: return labels[2]
                    return labels[3]
                return s.apply(f)

    def _compute_window_metrics(self, df_events: pd.DataFrame, ts_col: str, start_at: pd.Timestamp, end_at: pd.Timestamp):
        base_cols = ["tutor_id", "total", "weekly"]

        if df_events.empty or start_at is None or end_at is None:
            return pd.DataFrame(columns=base_cols)

        df = df_events.copy()
        df["_day"] = df[ts_col].dt.normalize()
        mask = (df["_day"] >= start_at) & (df["_day"] <= end_at)
        dfw = df.loc[mask].copy()

        if dfw.empty:
            return pd.DataFrame(columns=base_cols)

        window_days = int((end_at - start_at).days) + 1
        window_weeks = max(window_days / 7.0, 1.0)

        out = (dfw.groupby("tutor_id").agg(total=("tutor_id", "size")).reset_index())
        out["weekly"] = out["total"] / window_weeks

        return out[base_cols]

    def subject_analysis(self, subject_id, version, connector, start_at, end_at):
        if start_at is None or end_at is None:
            empty = pd.DataFrame(columns=["tutor_id","n_login","label_access","mean_weekly_course_views_window"])
            return empty, None, None

        start_date = pd.to_datetime(start_at).date()
        end_date = pd.to_datetime(end_at).date()

        df_course_views = self.mapper.fetch_tutors_login_subject(connector, version, subject_id, start_date, end_date)

        if "course_view_at" not in df_course_views.columns and "data_acesso_curso" in df_course_views.columns:
            df_course_views["course_view_at"] = pd.to_datetime(df_course_views["data_acesso_curso"], errors="coerce")
        else:
            df_course_views["course_view_at"] = pd.to_datetime(df_course_views["course_view_at"], errors="coerce")

        df_course_views = df_course_views.dropna(subset=["course_view_at"])

        tutor_ids = df_course_views["tutor_id"].dropna().astype(int).unique().tolist()
        df_metrics = pd.DataFrame({"tutor_id": tutor_ids})

        start_ts = pd.to_datetime(start_at).normalize()
        end_ts = pd.to_datetime(end_at).normalize()

        df_view_win = self._compute_window_metrics(df_course_views, "course_view_at", start_ts, end_ts).rename(
            columns={"total": "n_login", "weekly": "mean_weekly_course_views_window"}
        )

        df_metrics = df_metrics.merge(df_view_win, on="tutor_id", how="left")
        df_metrics["n_login"] = df_metrics["n_login"].fillna(0).astype(int)
        df_metrics["mean_weekly_course_views_window"] = (
            pd.to_numeric(df_metrics["mean_weekly_course_views_window"], errors="coerce").fillna(0).round(3)
        )
        df_metrics["label_access"] = self._discretize_by_quantiles(df_metrics["mean_weekly_course_views_window"])

        return df_metrics[["tutor_id","n_login","label_access","mean_weekly_course_views_window"]].copy()