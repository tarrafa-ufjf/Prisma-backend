import pandas as pd
from ......indicator import Indicator

class Engagement(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

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
        df_posts = self.mapper.get_engagement_data(connector, subject_id, version)
        df_alunos = self.mapper.get_all_students(connector, subject_id, version)

        df_alunos["subject_id"] = subject_id
        
        posts_por_usuario = df_posts.groupby('user_id')['post_id_required'].count().reset_index()
        posts_por_usuario = posts_por_usuario.rename(columns={'post_id_required': 'num_posts_required'})

        df_final = df_alunos.merge(posts_por_usuario, on='user_id', how='left')
        df_final['num_posts_required'] = df_final['num_posts_required'].fillna(0).astype(int)

        q1 = df_final["num_posts_required"].quantile(0.25)
        q3 = df_final["num_posts_required"].quantile(0.75)
        q2 = df_final["num_posts_required"].quantile(0.5)

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

        df_final["posts_required_label"] = df_final["num_posts_required"].apply(
            lambda x: discretize(x, lim_inf, q1, q3, lim_sup)
        )

        return df_final
