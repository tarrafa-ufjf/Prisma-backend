import pandas as pd
import numpy as np
from .....indicator import Indicator

class Analysis_Forums_Response(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def tutors_analysis(self, subject_id, tutors_id, version, connector):
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
        
    def label_from_score(self, score_access):
        if pd.isna(score_access):
            return np.nan  

        if score_access < 1.5:
            return "Muito baixo"
        elif score_access < 2.0:
            return "Baixo"
        elif score_access < 2.5:
            return "Médio"
        elif score_access < 2.9:
            return "Alto"
        else:
            return "Muito alto"

    def label_to_numeric(self, label):
        mapping = {
            "Muito baixo": 0,
            "Baixo": 1,
            "Médio": 2,
            "Alto": 3,
            "Muito alto": 4,       
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
            "total_response_forum": "Qtd de respostas",
            "mean_forums_response_hours": "Tempo médio de resposta (h)",
            "median_forums_response_hours": "Tempo mediano de resposta (h)",
            "score_access": "Regra matemática que prioriza tutores rápidos"
        }

        for col in metrics.keys():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
        def bucket5_from_series(s: pd.Series, reverse: bool = False):
            s = s.dropna()
            if s.empty:
                return lambda x: np.nan

            p20, p40, p60, p80 = [float(v) for v in s.quantile([0.2, 0.4, 0.6, 0.8])]

            if p20 == p80:
                return lambda x: np.nan if pd.isna(x) else "Médio"

            labels_normal = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]
            labels_rev    = ["Muito alto", "Alto", "Médio", "Baixo", "Muito baixo"]
            labels = labels_rev if reverse else labels_normal

            def bucket(x):
                if pd.isna(x): return np.nan
                if x <= p20: return labels[0]
                if x <= p40: return labels[1]
                if x <= p60: return labels[2]
                if x <= p80: return labels[3]
                return labels[4]

            return bucket

        for col, _ in metrics.items():
            if col not in df.columns:
                continue

            if col == "score_access":
                df["score_access_label"] = df["score_access"].apply(self.label_from_score)
                continue
            
            if col in ["mean_forums_response_hours", "median_forums_response_hours"]:
                bucket = bucket5_from_series(df[col], reverse=True)  
            else:
                bucket = bucket5_from_series(df[col], reverse=False)

            df[f"{col}_label"] = df[col].apply(bucket)

        class_cols = [f"{col}_label" for col in metrics.keys() if f"{col}_label" in df.columns]
        for c in class_cols:
            df[f"{c}_num"] = df[c].apply(self.label_to_numeric)

        df["mean_label_num"] = df[[f"{c}_num" for c in class_cols]].mean(axis=1)

        labels = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]
        
        try:
            df["label_forums_response"] = pd.qcut(df["mean_label_num"], q=5, labels=labels, duplicates="drop").astype(object)
        except ValueError:
            df["label_forums_response"] = df["mean_label_num"].apply(self.numeric_to_label)

        return df

    def subject_analysis(self, subject_id, version, connector, start_at, end_at, tutor_ids):
        df_responses_forums = self.mapper.fetch_responses_forums(connector, version, subject_id, start_at, end_at, tutor_ids)
                
        df_tutores = df_responses_forums[['tutor_id', 'tutor_completo']].drop_duplicates()
        df_forum = df_responses_forums.dropna(subset=['resposta_id']).copy()
        
        df_forum["autor_resposta_completo"] = df_forum.get("autor_resposta_completo", pd.Series())
        df_forum["resposta_enviada_em"] = pd.to_datetime(df_forum["resposta_enviada_em"], errors='coerce')
        df_forum["post_criado_em"] = pd.to_datetime(df_forum["post_criado_em"], errors='coerce')
        
        if not df_forum.empty:
            df_forum_first_response = (
                df_forum.sort_values("resposta_enviada_em")
                .groupby("post_aluno_id", as_index=False)
                .first()
            )
        else:
            df_forum_first_response = pd.DataFrame(columns=df_forum.columns)

        if not df_forum_first_response.empty:
            valid_dates = df_forum_first_response["resposta_enviada_em"].notna() & df_forum_first_response["post_criado_em"].notna()
            if valid_dates.any():
                time_diff = (df_forum_first_response.loc[valid_dates, "resposta_enviada_em"] -
                            df_forum_first_response.loc[valid_dates, "post_criado_em"])
                df_forum_first_response.loc[valid_dates, "horas"] = time_diff.dt.total_seconds() / 3600
            else:
                df_forum_first_response["horas"] = np.nan
        else:
            df_forum_first_response["horas"] = np.nan

        def classificar_resposta(horas):
            if horas <= 24:
                return 'num_response_fast_forum'
            elif horas > 120:
                return 'num_response_late_forum'
            else:
                return 'num_response_normal_forum'

        df_forum_first_response["classificacao"] = df_forum_first_response["horas"].apply(classificar_resposta)

        if not df_forum_first_response.empty:
            forum_count = df_forum_first_response.groupby(["autor_resposta_id", "autor_resposta_completo"])["resposta_id"].count().reset_index()
            forum_count.columns = ["tutor_id", "tutor_completo", "total_response_forum"]

            class_count = df_forum_first_response.groupby(["autor_resposta_id", "classificacao"])["resposta_id"].count().unstack(fill_value=0).reset_index()
            class_count = class_count.rename(columns={"autor_resposta_id": "tutor_id"})

            estatisticas = (
                df_forum_first_response.groupby("autor_resposta_id")["horas"]
                .agg(["mean", "median"])
                .reset_index()
                .rename(columns={
                    "autor_resposta_id": "tutor_id",
                    "mean": "mean_forums_response_hours",
                    "median": "median_forums_response_hours"
                })
            )

            forum_count = forum_count.merge(estatisticas, on="tutor_id", how="left")
            forum_count = forum_count.merge(class_count, on="tutor_id", how="left")
        else:
            forum_count = pd.DataFrame(columns=[
                "tutor_id", "tutor_completo", "total_response_forum",
                "mean_forums_response_hours", "median_forums_response_hours"
            ])
            
        forum_count = df_tutores.merge(forum_count, on=["tutor_id", "tutor_completo"], how="left")

        forum_count["total_response_forum"] = forum_count["total_response_forum"].fillna(0).astype(int)
        forum_count["mean_forums_response_hours"] = pd.to_numeric(forum_count["mean_forums_response_hours"], errors="coerce")
        forum_count["median_forums_response_hours"] = pd.to_numeric(forum_count["median_forums_response_hours"], errors="coerce")

        for col in ["num_response_fast_forum", "num_response_normal_forum", "num_response_late_forum"]:
            if col not in forum_count.columns:
                forum_count[col] = 0
            forum_count[col] = forum_count[col].fillna(0).astype(int)
        
        total = forum_count["total_response_forum"]

        forum_count["score_access"] = np.where(
            total > 0,
            (forum_count["num_response_fast_forum"]*3
            + forum_count["num_response_normal_forum"]*2
            + forum_count["num_response_late_forum"]*1) / total,
            np.nan 
        )

        forum_count = self.run_discretization(forum_count)

        return forum_count[["tutor_id", "total_response_forum", "median_forums_response_hours", "mean_forums_response_hours", "score_access",
                            "mean_forums_response_hours_label", "median_forums_response_hours_label", "score_access_label",
                            "label_forums_response",
                            "num_response_fast_forum", "num_response_late_forum", "num_response_normal_forum"]]