import pandas as pd
from src.analysis.indicator import Indicator

class Motivation(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def course_analysis(self, course_id, version, connector):
        df_posts = self.mapper.get_foruns_non_required(connector, course_id, version)
        df_alunos = self.mapper.get_all_students(connector, course_id, version)

        df_alunos["course_id"] = course_id

        posts_por_usuario = df_posts.groupby('user_id')['post_id_unrequired'].count().reset_index()
        posts_por_usuario = posts_por_usuario.rename(columns={'post_id_unrequired': 'num_posts_unrequired'})

        df_final = df_alunos.merge(posts_por_usuario, on='user_id', how='left')
        df_final['num_posts_unrequired'] = df_final['num_posts_unrequired'].fillna(0).astype(int) 

        return df_final
    
    def general_analysis(self, version, connector, analysis_config):
        batch_size = analysis_config["batch_size"]
        processed = analysis_config["processed"]
        engine = self.get_connector()

        # Se total ainda não foi definido, calcular (baseado no banco fonte)
        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)  
            df_courses = pd.DataFrame(df_courses, columns=['course_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]
        df = pd.DataFrame(columns=['user_id', 'course_id', 'forum_id_unrequired', 'num_posts_unrequired', 'full_name'])

        for i in range(processed + 1, total + 1):
            result = self.course_analysis(i, version, connector)
            df = pd.concat([df, result], ignore_index=True)
            analysis_config["processed"] += 1

            self.print_load("Motivação", analysis_config["processed"], total, 7)

            if analysis_config["processed"] % batch_size == 0:
                df = df.infer_objects(copy=False)
                df["s_user"] = 1
                df.to_sql('motivation_global', con=engine, if_exists='append', index=False)
                return analysis_config
        
        if not df.empty:
            df = df.infer_objects(copy=False)
            df["s_user"] = 1
            df.to_sql('motivation_global', con=engine, if_exists='append', index=False)
        return analysis_config