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

        def bucket5_from_series(s: pd.Series):
            s = s.dropna()
            if s.empty:
                return lambda x: np.nan

            p20, p40, p60, p80 = [float(v) for v in s.quantile([0.2, 0.4, 0.6, 0.8])]
            if p20 == p80:
                return lambda x: np.nan if pd.isna(x) else "Médio"

            labels = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]

            def bucket(x):
                if pd.isna(x):
                    return np.nan
                if x <= p20: return labels[0]
                if x <= p40: return labels[1]
                if x <= p60: return labels[2]
                if x <= p80: return labels[3]
                return labels[4]

            return bucket

        for col in metrics.keys():
            if col not in df.columns:
                continue

            bucket = bucket5_from_series(df[col])
            df[f"{col}_label"] = df[col].apply(bucket)

        class_cols = [f"{col}_label" for col in metrics.keys() if f"{col}_label" in df.columns]
        for c in class_cols:
            df[f"{c}_num"] = df[c].apply(self.label_to_numeric)

        df["media_classificacao_num"] = df[[f"{c}_num" for c in class_cols]].mean(axis=1)

        labels = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]
        try:
            df["label_feedback"] = pd.qcut(
                df["media_classificacao_num"], q=5, labels=labels, duplicates="drop"
            ).astype(object)
        except ValueError:
            df["label_feedback"] = df["media_classificacao_num"].apply(self.numeric_to_label)

        return df

    def subject_analysis(self, subject_id, version, connector, start_at, end_at, tutor_ids):
        if start_at is None or end_at is None:
            return pd.DataFrame(columns=["tutor_id","n_corrections","n_corrections_with_feedback","percentage_feedback","n_textual_feedback","n_feedback_pdf",
                                            "n_corrections_label", "n_corrections_with_feedback_label", "percentage_feedback_label",
                                            "n_textual_feedback_label", "n_feedback_pdf_label", "label_feedback"])

        start_date = pd.to_datetime(start_at).date()
        end_date = pd.to_datetime(end_at).date()

        df_feedback_tutors = self.mapper.fetch_tutors_feedback_subject(connector, version, subject_id, start_date, end_date, tutor_ids)

        for col in ["n_corrections", "n_corrections_with_feedback", "n_textual_feedback", "n_feedback_pdf"]:
            for col in ["n_corrections", "n_corrections_with_feedback", "n_textual_feedback", "n_feedback_pdf"]:
                df_feedback_tutors[col] = pd.to_numeric(df_feedback_tutors[col], errors="coerce").fillna(0).astype(int)

            df_feedback_tutors["percentage_feedback"] = pd.to_numeric(df_feedback_tutors["percentage_feedback"], errors="coerce")
            df_feedback_tutors.loc[df_feedback_tutors["n_corrections"] == 0, "percentage_feedback"] = np.nan
            

        df_feedback_tutors["percentage_feedback"] = df_feedback_tutors["percentage_feedback"].fillna(0)

        df_feedback_tutors_labeled = self.run_discretization(subject_id, df_feedback_tutors)

        return df_feedback_tutors_labeled[["tutor_id","n_corrections","n_corrections_with_feedback","percentage_feedback","n_textual_feedback","n_feedback_pdf",
                            "n_corrections_label", "n_corrections_with_feedback_label", "percentage_feedback_label",
                            "n_textual_feedback_label", "n_feedback_pdf_label", "label_feedback"]].copy()