import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

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

        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)  
            df_courses = pd.DataFrame(df_courses, columns=['course_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]
        df = pd.DataFrame(columns=['user_id', 'course_id', 'forum_id_unrequired', 'num_posts_unrequired', 'full_name'])

        for i in range(processed + 1, total + 1):
            result = self.course_analysis(i, version, connector)
            result = self._fillna_mixed(result)
            df = pd.concat([df, result], ignore_index=True)
            analysis_config["processed"] += 1

            self.print_load("Motivação", analysis_config["processed"], total, 7)

            if analysis_config["processed"] % batch_size == 0:
                self._insert_ignore_conflicts(df, engine, "motivation_global")
                return analysis_config
        
        if not df.empty:
            self._insert_ignore_conflicts(df, engine, "motivation_global")

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

    def _insert_ignore_conflicts(self, df, engine, table_name):
        """Insere no banco ignorando duplicatas (PostgreSQL)."""
        df = df.infer_objects(copy=False)
        df["s_user"] = 1

        # Substitui NaN ou None por 0 em todas as colunas inteiras
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            df[col] = df[col].fillna(0).astype(int)

        metadata = MetaData()
        metadata.reflect(bind=engine, only=[table_name])
        table = metadata.tables[table_name]

        with engine.begin() as conn:
            for _, row in df.iterrows():
                stmt = insert(table).values(row.to_dict())
                stmt = stmt.on_conflict_do_nothing()  # IGNORA duplicatas
                conn.execute(stmt)
