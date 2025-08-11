import pandas as pd
from analysis.analysis import Analyzer

class Engagement(Analyzer):
    def __init__(self):
        pass

    def analysis(self, course_id):
        df_posts = pd.read_csv('exports/foruns_ava.csv')
        df_alunos = pd.read_csv('exports/all_students.csv')

        df_alunos['course_id'] = course_id

        posts_por_usuario = df_posts.groupby('user_id')['post_id_required'].count().reset_index()
        posts_por_usuario = posts_por_usuario.rename(columns={'post_id_required': 'num_posts_required'})

        df_final = df_alunos.merge(posts_por_usuario, on='user_id', how='left')
        df_final['num_posts_required'] = df_final['num_posts_required'].fillna(0).astype(int)

        df_final.to_csv('exports/foruns_ava.csv', index=False)