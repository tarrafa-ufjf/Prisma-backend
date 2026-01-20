import pandas as pd
import numpy as np
import math
from ....indicator import Indicator

class Analysis_login(Indicator):
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
            "n_access_subject": "Total de acessos ao curso",
            "n_login_weekly": "Logins semanais"        
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

    def subject_analysis(self, subject_id, version, connector, start_at, end_at):
        if start_at is None or end_at is None:
            return pd.DataFrame(columns=["tutor_id", "n_login", "n_access_subject", "n_login_weekly", "n_login_label", 
                                            "n_login_weekly_label", "label_access"])

        start_date = pd.to_datetime(start_at).date()
        end_date = pd.to_datetime(end_at).date()

        df_course_views = self.mapper.fetch_tutors_login_subject(connector, version, subject_id, start_date, end_date)

        for col in ["first_login", "last_login", "first_course_access", "last_course_access"]:
            df_course_views[col] = pd.to_datetime(df_course_views[col])

        metrics = []

        for _, row in df_course_views.iterrows():

            tutor_id = row["tutor_id"]

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
                "n_access_subject": row["n_access_subject"],
                "n_login_weekly": round(n_login_weekly, 2) if n_login_weekly else 0,
            })

        df_metrics = pd.DataFrame(metrics)
                
        df_metrics = self.run_discretization(df_metrics)

        return df_metrics[["tutor_id", "n_login", "n_access_subject", "n_login_weekly", "n_login_label", 
                            "n_login_weekly_label", "label_access"]].copy()