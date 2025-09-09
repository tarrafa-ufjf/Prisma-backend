import pandas as pd
from sqlalchemy import Table, Column, Integer, MetaData, String, create_engine
import os, sys
from dotenv import load_dotenv

class Engagement:
    def __init__(self, mapper):
        self.mapper = mapper
        load_dotenv()
    
    def get_connector(self):
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", 5432))
        DB_NAME = os.getenv("DB_DATABASE")

        engine = create_engine(
            f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        return engine
    

    def get_global_analysis_table(self):
        metadata = MetaData()
        global_analysis = Table(
            'gl_indicators_status', metadata,
            Column('s_user', Integer, primary_key=True),
            Column('course_id', Integer, primary_key=True),
            Column('indicator', Integer, primary_key=True),
            Column('status', String(1), nullable=False)
        )
        return global_analysis
    
    def insert_global_analysis_status(self, s_user: int, course_id: int, indicator: int, status: str):
        engine = self.get_connector()
        global_analysis = self.get_global_analysis_table()

        with engine.connect() as conn:
            insert_stmt = global_analysis.insert().values(
                s_user=s_user,
                course_id=course_id,
                indicator=indicator,
                status=status
            )
            conn.execute(insert_stmt)
            conn.commit()
        

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
    
    def print_load(self, processed, total):
        percent = (processed / total) * 100
        bar_length = 40
        filled_length = int(bar_length * processed // total)
        bar = '#' * filled_length + '-' * (bar_length - filled_length)

        # sobrescreve a linha atual
        sys.stdout.write(f'\rGlobal Analysis: |{bar}| {percent:.2f}% Complete')
        sys.stdout.flush()

        if processed == total:
            print(' ✅\n')

    
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
        df = pd.DataFrame(columns=['course_id', 'full_name', 'num_posts_required', 'posts_required_label', 'user_id'])

        # Processar cursos a partir do ponto onde parou
        for i in range(processed + 1, total + 1):
            result = self.course_analysis(i, version, connector)
            df = pd.concat([df, result], ignore_index=True)
            analysis_config["processed"] += 1

            self.print_load(analysis_config["processed"], total)

            # Quando atingir batch_size, salvar e retornar
            if analysis_config["processed"] % batch_size == 0:
                df_counts = (
                    df.groupby(['course_id', 'posts_required_label'])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )

                df_counts.columns = (
                    df_counts.columns.str.strip()  
                    .str.lower()                   
                    .str.replace(" ", "_")        
                )

                df_counts["s_user"] = 1 
                for col in ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]:
                    if col not in df_counts.columns:
                        df_counts[col] = 0
                
                df_counts = df_counts.groupby("course_id", as_index=False).sum()

                df_counts.to_sql("engajamento_global", engine, if_exists="append", index=False)

                df = pd.DataFrame(columns=['course_id', 'full_name', 'num_posts_required', 'posts_required_label', 'user_id'])

                return analysis_config

        # Se terminar todos os cursos (salva o que restou)
        if not df.empty:
            df_counts = (
                df.groupby(['course_id', 'posts_required_label'])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )

            df_counts.columns = (
                df_counts.columns.str.strip() 
                .str.lower()   
                .str.replace(" ", "_") 
            )

            df_counts["s_user"] = 1

            for col in ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]:
                if col not in df_counts.columns:
                    df_counts[col] = 0
            
            df_counts = df_counts.groupby("course_id", as_index=False).sum()
            
            df_counts.to_sql("engajamento_global", engine, if_exists="append", index=False)

        return analysis_config
