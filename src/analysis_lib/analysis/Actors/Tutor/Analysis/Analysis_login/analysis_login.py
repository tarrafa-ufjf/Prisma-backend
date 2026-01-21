import pandas as pd
import numpy as np
import math
from .....indicator import Indicator

class Analysis_Login(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def tutors_analysis(self, subject_id, tutor_id, version, connector):
        print("Chegou tutor")
        return None
    
    def discretize_value_quartis(self, x, lim_inf, q1, q3, lim_sup):
        if pd.isna(x):
            return np.nan
        if x <= lim_inf:
            return "Muito baixo"
        elif x <= q1:
            return "Baixo"
        elif x <= q3:
            return "Médio"
        elif x <= lim_sup:
            return "Alto"
        else:
            return "Muito alto"

    def label_to_numeric(self, label):
        mapping = {
            "Muito baixo": 0,
            "Baixo": 1,
            "Médio": 2,
            "Alto": 3,
            "Muito alto": 4
        }
        return mapping.get(label, np.nan)

    def numeric_to_label(self, num):
        if pd.isna(num):
            return np.nan
        elif num < 0.5:
            return "Muito baixo"
        elif num < 1.5:
            return "Baixo"
        elif num < 2.5:
            return "Médio"
        elif num < 3.5:
            return "Alto"
        else:
            return "Muito alto"
    
    def run_discretization(self, df):       
        metrics = {
            "n_login": "Total de logins",
            "n_login_subject": "Total de acessos ao curso",
            "n_login_weekly": "Logins semanais",
            "maximum_inactivity_days": "Máx. inatividade (dias)"        
        }

        for col in metrics.keys():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col, label in metrics.items():
            if col in df.columns:
                lim_inf = df[col].min()
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                lim_sup = df[col].max()

                df[f"{col}_label"] = df[col].apply(
                    lambda x: self.discretize_value_quartis(x, lim_inf, q1, q3, lim_sup)
                )

        class_cols = [f"{col}_label" for col in metrics.keys() if f"{col}_label" in df.columns]

        for c in class_cols:
            df[f"{c}_num"] = df[c].apply(self.label_to_numeric)

        df["media_label_num"] = df[[f"{c}_num" for c in class_cols]].mean(axis=1)
        
        df["label_access"] = df["media_label_num"].apply(self.numeric_to_label)
        
        return df
    
    def _max_inactivity_days_for_tutor(self, active_days, start_date, end_date):
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()

        window_len = (end_date - start_date).days + 1

        if not active_days:
            return window_len  

        days = sorted({pd.to_datetime(d).date() for d in active_days})

        start_gap = (days[0] - start_date).days
        end_gap = (end_date - days[-1]).days

        max_internal = 0
        for i in range(1, len(days)):
            gap = (days[i] - days[i - 1]).days - 1  
            if gap > max_internal:
                max_internal = gap

        return max(0, start_gap, end_gap, max_internal)

    def subject_analysis(self, subject_id, version, connector, start_at, end_at):
        if start_at is None or end_at is None:
            return pd.DataFrame(columns=["tutor_id", "n_login", "n_login_subject", "n_login_weekly", "n_login_label", 
                                            "n_login_weekly_label", "label_access", "maximum_inactivity_days", "maximum_inactivity_days_label"])

        start_date = pd.to_datetime(start_at).date()
        end_date = pd.to_datetime(end_at).date()

        df_course_views = self.mapper.fetch_tutors_login_subject(connector, version, subject_id, start_date, end_date)

        for col in ["first_login", "last_login", "first_course_access", "last_course_access"]:
            df_course_views[col] = pd.to_datetime(df_course_views[col])
        
        df_access_days = self.mapper.fetch_tutors_access_days(connector, version, subject_id, start_date, end_date)
        
        if df_access_days is None or df_access_days.empty:
            access_days_by_tutor = {}
        else:
            df_access_days["access_day"] = pd.to_datetime(df_access_days["access_day"], errors="coerce").dt.date
            access_days_by_tutor = (
                df_access_days.dropna(subset=["tutor_id", "access_day"])
                            .groupby("tutor_id")["access_day"]
                            .apply(list)
                            .to_dict()
            )

        metrics = []

        for _, row in df_course_views.iterrows():

            tutor_id = row["tutor_id"]
            
            active_days = access_days_by_tutor.get(tutor_id, [])
            max_inact = self._max_inactivity_days_for_tutor(active_days, start_date, end_date)

            n_login = row["n_login"]
            
            if pd.notna(row["first_login"]) and pd.notna(row["last_login"]):
                duracao = (row["last_login"] - row["first_login"]).days + 1

                semanas = max(duracao / 7.0, 1.0)   
                semanas = round(semanas, 2)

                n_login = float(row["n_login"]) if pd.notna(row["n_login"]) else 0.0
                n_login_weekly = n_login / semanas
            else:
                n_login_weekly = 0.0

            metrics.append({
                "tutor_id": tutor_id,
                "n_login": n_login,
                "n_login_subject": row["n_login_subject"],
                "n_login_weekly": round(n_login_weekly, 2) if n_login_weekly else 0,
                "maximum_inactivity_days": int(max_inact),
            })

        df_metrics = pd.DataFrame(metrics)
        
        expected_cols = [
            "tutor_id",
            "n_login",
            "n_login_subject",
            "n_login_weekly",
            "n_login_label",
            "n_login_weekly_label",
            "maximum_inactivity_days",
            "maximum_inactivity_days_label",
            "label_access",
        ]

        if df_metrics.empty:
            return pd.DataFrame(columns=expected_cols)
                
        df_metrics = self.run_discretization(df_metrics)

        return df_metrics[["tutor_id", "n_login", "n_login_subject", "n_login_weekly", "n_login_label", 
                            "n_login_weekly_label", "label_access", "maximum_inactivity_days", "maximum_inactivity_days_label"]].copy()