import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Motivation(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def student_analysis(self, subject_id, student_id, version, connector):
        df_course = self.course_analysis(subject_id, version, connector)

        df_course["user_id"] = pd.to_numeric(df_course["user_id"], errors="coerce")
        sid = pd.to_numeric(student_id, errors="coerce")

        student_df = df_course.loc[df_course["user_id"] == sid]
        if student_df.empty:
            return None 

        row = student_df.iloc[0]
        row = row.where(pd.notna(row), None).to_dict()
        return row

    def course_analysis(self, subject_id, version, connector):
        df_posts = self.mapper.get_foruns_non_required(connector, subject_id, version)
        df_alunos = self.mapper.get_all_students(connector, subject_id, version)

        df_alunos["subject_id"] = subject_id

        posts_por_usuario = df_posts.groupby('user_id')['post_id_unrequired'].count().reset_index()
        posts_por_usuario = posts_por_usuario.rename(columns={'post_id_unrequired': 'num_posts_unrequired'})

        df_final = df_alunos.merge(posts_por_usuario, on='user_id', how='left')
        df_final['num_posts_unrequired'] = df_final['num_posts_unrequired'].fillna(0).astype(int) 

        # print(f"df: {df_final}")

        q1 = df_final["num_posts_unrequired"].quantile(0.25)
        q3 = df_final["num_posts_unrequired"].quantile(0.75)
        q2 = df_final["num_posts_unrequired"].quantile(0.5)

        iqr = q3 - q1
        lim_inf = q1 - 1.5 * iqr
        lim_sup = q3 + 1.5 * iqr

        def discretize(x, lim_inf, q1, q3, lim_sup):
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

        df_final["posts_unrequired_label"] = df_final["num_posts_unrequired"].apply(
            lambda x: discretize(x, lim_inf, q1, q3, lim_sup)
        )

        return df_final
        
    
    def discrete_analysis(self, subject_id, version, connector):
        df_sit = self.course_analysis(subject_id, version, connector)
        q1 = df_sit["num_posts_unrequired"].quantile(0.25)
        q3 = df_sit["num_posts_unrequired"].quantile(0.75)
        q2 = df_sit["num_posts_unrequired"].quantile(0.5)

        iqr = q3 - q1
        lim_inf = q1 - 1.5 * iqr
        lim_sup = q3 + 1.5 * iqr

        def discretize(x, lim_inf, q1, q3, lim_sup):
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

        df_sit["label"] = df_sit["num_posts_unrequired"].apply(
            lambda x: discretize(x, lim_inf, q1, q3, lim_sup)
        )

        return df_sit[['user_id', 'subject_id','label', 'num_posts_unrequired']]
    
    def general_analysis(self, version, connector, analysis_config):
        batch_size = analysis_config["batch_size"]
        processed = analysis_config["processed"]
        engine = self.get_connector()

        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)  
            df_courses = pd.DataFrame(df_courses, columns=['subject_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]
        df = pd.DataFrame(columns=['user_id', 'subject_id','label'])

        results = []

        for i in range(processed + 2, total + 1):
            result = self.discrete_analysis(i, version, connector)
            result = result.drop_duplicates(subset=['user_id'], keep='first')
            result = self._fillna_mixed(result)
            results.append(result)
            analysis_config["processed"] += 1

            self.print_load("Motivação", analysis_config["processed"], total, 7)
            if analysis_config["processed"] % batch_size == 0:
                df = pd.concat(results, ignore_index=True)
                df['institution_id'] = 1
                df.to_sql("motivation_global", engine, if_exists="append", index=False)
                df = pd.DataFrame(columns=['user_id', 'subject_id','label'])
                return analysis_config
        
        if not df.empty:
            df = pd.concat(results, ignore_index=True)
            df['institution_id'] = 1
            df.to_sql("motivation_global", engine, if_exists="append", index=False)

        return analysis_config

    def _fillna_mixed(self, dataframe):
        for col in dataframe.columns:
            if pd.api.types.is_numeric_dtype(dataframe[col]):
                # Substitui NaN/inf por 0
                dataframe[col] = dataframe[col].replace([np.nan, np.inf, -np.inf], 0)

                # força para int64 se não tiver decimais
                if dataframe[col].dropna().apply(lambda x: float(x).is_integer()).all():
                    dataframe[col] = dataframe[col].astype(int)
            else:
                dataframe[col] = dataframe[col].fillna('')
        return dataframe