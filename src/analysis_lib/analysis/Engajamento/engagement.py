import pandas as pd
from ..indicator import Indicator

class Engagement(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def course_analysis(self, subject_id, version, connector):
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
                return "Muito baixo"
            elif x <= q1:
                return "Baixo"
            elif x <= q3:
                return "Medio"
            elif x <= lim_sup:
                return "Alto"
            else:
                return "Muito alto"

        df_final["posts_required_label"] = df_final["num_posts_required"].apply(
            lambda x: discretize(x, lim_inf, q1, q3, lim_sup)
        )

        # Teste
        return df_final

    
    def general_analysis(self, version, connector, analysis_config):
        batch_size = analysis_config["batch_size"]
        processed = analysis_config["processed"]
        engine = self.get_connector()

        # Se total ainda não foi definido, calcular (baseado no banco fonte)
        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)  
            df_courses = pd.DataFrame(df_courses, columns=['subject_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]
        df = pd.DataFrame(columns=['subject_id', 'full_name', 'num_posts_required', 'posts_required_label', 'institution_id'])

        batch_results = []

        # Processar cursos a partir do ponto onde parou
        for i in range(processed + 1, total + 1):
            result = self.course_analysis(i, version, connector)
            batch_results.append(result)
            analysis_config["processed"] += 1

            self.print_load("Engajamento", analysis_config["processed"], total, 5)

            # Quando atingir batch_size, salvar e retornar
            if analysis_config["processed"] % batch_size == 0:
                df = pd.concat(batch_results, ignore_index=True)

                df_counts = (
                    df.groupby(['subject_id', 'posts_required_label'])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )

                df_counts.columns = (
                    df_counts.columns.str.strip()  
                    .str.lower()                   
                    .str.replace(" ", "_")        
                )

                df_counts["institution_id"] = 1 
                for col in ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]:
                    if col not in df_counts.columns:
                        df_counts[col] = 0
                
                df_counts = df_counts.groupby("subject_id", as_index=False).sum()

                df_counts.to_sql("engajamento_global", engine, if_exists="append", index=False)

                df = pd.DataFrame(columns=['subject_id', 'full_name', 'num_posts_required', 'posts_required_label', 'user_id'])

                return analysis_config

        # Se terminar todos os cursos (salva o que restou)
        if not df.empty:
            df_counts = (
                df.groupby(['subject_id', 'posts_required_label'])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )

            df_counts.columns = (
                df_counts.columns.str.strip() 
                .str.lower()   
                .str.replace(" ", "_") 
            )

            df_counts["institution_id"] = 1

            for col in ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]:
                if col not in df_counts.columns:
                    df_counts[col] = 0
            
            df_counts = df_counts.groupby("subject_id", as_index=False).sum()
            
            df_counts.to_sql("engajamento_global", engine, if_exists="append", index=False)

        return analysis_config
