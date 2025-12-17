import pandas as pd
import numpy as np
from ....indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Pedagogic(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        pd.set_option('future.no_silent_downcasting', True)
        
    def student_analysis(self, subject_id, student_id, version, connector):
        df_course = self.subject_analysis(subject_id, version, connector)

        df_course["user_id"] = pd.to_numeric(df_course["user_id"], errors="coerce")
        sid = pd.to_numeric(student_id, errors="coerce")

        student_df = df_course.loc[df_course["user_id"] == sid]
        if student_df.empty:
            return None 

        row = student_df.iloc[0]
        row = row.where(pd.notna(row), None).to_dict()
        return row

    def subject_analysis(self, subject_id, version, connector):
        df = self.mapper.get_forum_data(connector, subject_id, version)
        df_alunos = self.mapper.get_all_students(connector, subject_id, version)
        df_alunos["subject_id"] = subject_id
        
        if df.empty or "post_aluno_id" not in df.columns or "resposta_id" not in df.columns:
            df_alunos["n_responses_relation_teacher_student"] = 0
            df_alunos["label_relation_teacher_student"] = "muito_baixo"
            return df_alunos[
                ["subject_id", "user_id", "n_responses_relation_teacher_student", "label_relation_teacher_student"]
            ]

        df_respostas = (
            df.dropna(subset=["resposta_id"])
            .groupby("aluno_id")
            .agg(n_responses_relation_teacher_student=("resposta_id", "count"))
            .reset_index()
            .rename(columns={"aluno_id": "user_id"})
        )
        
        df_final = df_alunos.merge(df_respostas, on="user_id", how="left")
        df_final["n_responses_relation_teacher_student"] = df_final["n_responses_relation_teacher_student"].fillna(0).astype(int)

        valores = df_final["n_responses_relation_teacher_student"].astype(float)
        q1 = valores.quantile(0.25)
        q3 = valores.quantile(0.75)
        iqr = q3 - q1
        lim_inf = q1 - 1.5 * iqr
        lim_sup = q3 + 1.5 * iqr

        def discretize(x):
            if x <= lim_inf:
                return "muito_baixo"
            elif x <= q1:
                return "baixo"
            elif x <= q3:
                return "medio"
            elif x <= lim_sup:
                return "alto"
            else:
                return "muito_alto"

        df_final["label_relation_teacher_student"] = df_final["n_responses_relation_teacher_student"].apply(discretize)

        df_final["version"] = version
        df_final["institution_id"] = 1

        return df_final[["institution_id","version","subject_id","user_id", "full_name", "n_responses_relation_teacher_student","label_relation_teacher_student"]]