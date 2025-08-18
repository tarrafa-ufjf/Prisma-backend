from io import BytesIO
from matplotlib import pyplot as plt
import pandas as pd

class Engagement:
    def __init__(self, mapper):
        self.mapper = mapper

    def course_analysis(self, course_id, version, connector):
        df_posts = self.mapper.get_engagement_data(connector, course_id, version)
        df_alunos = self.mapper.get_all_students(connector, course_id, version)

        df_alunos["course_id"] = course_id
        
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
                return "Muito baixo"
            elif x <= q1:
                return "Baixo"
            elif x <= q3:
                return "Médio"
            elif x <= lim_sup:
                return "Alto"
            else:
                return "Muito alto"

        df_final["posts_required_label"] = df_final["num_posts_required"].apply(
            lambda x: discretize(x, lim_inf, q1, q3, lim_sup)
        )

        # Teste
        return df_final