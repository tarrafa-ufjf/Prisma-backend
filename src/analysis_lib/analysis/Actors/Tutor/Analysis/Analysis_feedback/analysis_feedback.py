import pandas as pd
import numpy as np
import math
from .....indicator import Indicator
import os

class Analysis_Feedback(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def tutors_analysis(self, subject_id, student_id, version, connector):
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
        
    def run_discretization(self, subject_id, df):
        metrics = {
            "n_corrections": "Total de correções",
            "n_corrections_with_feedback": "Correções com feedback",
            "percentage_feedback": "Percentual de feedback",
            "n_textual_feedback": "Feedback textual",
            "n_feedback_pdf": "Feedback em PDF",
        }

        for col in metrics.keys():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col, _ in metrics.items():
            if col not in df.columns:
                continue

            s = df[col].dropna()
            if s.empty:
                df[f"{col}_label"] = np.nan
                continue

            lim_inf = s.min()
            q1 = s.quantile(0.25)
            q3 = s.quantile(0.75)
            lim_sup = s.max()

            df[f"{col}_label"] = df[col].apply(
                lambda x: self.discretize_value_quartis(x, lim_inf, q1, q3, lim_sup)
            )

        class_cols = [f"{col}_label" for col in metrics.keys() if f"{col}_label" in df.columns]
        for c in class_cols:
            df[f"{c}_num"] = df[c].apply(self.label_to_numeric)

        df["media_classificacao_num"] = df[[f"{c}_num" for c in class_cols]].mean(axis=1)
        df["label_feedback"] = df["media_classificacao_num"].apply(self.numeric_to_label)

        return df

    def subject_analysis(self, subject_id, version, connector, start_at, end_at):
        if start_at is None or end_at is None:
            return pd.DataFrame(columns=["tutor_id","n_corrections","n_corrections_with_feedback","percentage_feedback","n_textual_feedback","n_feedback_pdf",
                                            "n_corrections_label", "n_corrections_with_feedback_label", "percentage_feedback_label",
                                            "n_textual_feedback_label", "n_feedback_pdf_label", "label_feedback"])

        start_date = pd.to_datetime(start_at).date()
        end_date = pd.to_datetime(end_at).date()

        df_feedback_tutors = self.mapper.fetch_tutors_feedback_subject(connector, version, subject_id, start_date, end_date)

        for col in ["n_corrections", "n_corrections_with_feedback", "n_textual_feedback", "n_feedback_pdf"]:
            df_feedback_tutors[col] = df_feedback_tutors[col].fillna(0).astype(int)

        df_feedback_tutors["percentage_feedback"] = df_feedback_tutors["percentage_feedback"].fillna(0)

        df_feedback_tutors_labeled = self.run_discretization(subject_id, df_feedback_tutors)

        return df_feedback_tutors_labeled[["tutor_id","n_corrections","n_corrections_with_feedback","percentage_feedback","n_textual_feedback","n_feedback_pdf",
                            "n_corrections_label", "n_corrections_with_feedback_label", "percentage_feedback_label",
                            "n_textual_feedback_label", "n_feedback_pdf_label", "label_feedback"]].copy()