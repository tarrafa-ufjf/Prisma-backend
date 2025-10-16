import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Pedagogic(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        pd.set_option('future.no_silent_downcasting', True)

    def course_analysis(self, subject_id, version, connector):
        df = self.mapper.get_forum_data(connector, subject_id, version)

        df_tutores = df[['tutor_id', 'tutor_completo']].drop_duplicates()
        df_forum = df.dropna(subset=['resposta_id'])
        df_forum = df.dropna(subset=['resposta_id']).copy()

        # ===============================
        # Normalizações
        # ===============================
        df_forum["autor_resposta_completo"] = df_forum.get("autor_resposta_completo", pd.Series()).fillna("Sem resposta")
        df_forum["resposta_enviada_em"] = pd.to_datetime(df_forum["resposta_enviada_em"], errors='coerce')
        df_forum["post_criado_em"] = pd.to_datetime(df_forum["post_criado_em"], errors='coerce')

        # ===============================
        # Primeira resposta por post
        # ===============================
        if not df_forum.empty:
            df_forum_primeira = (
                df_forum.sort_values("resposta_enviada_em")
                .groupby("post_aluno_id", as_index=False)
                .first()
            )
        else:
            df_forum_primeira = pd.DataFrame(columns=df_forum.columns)

        # ===============================
        # Calcular tempo de resposta (horas)
        # ===============================
        if not df_forum_primeira.empty:
            valid_dates = df_forum_primeira["resposta_enviada_em"].notna() & df_forum_primeira["post_criado_em"].notna()
            if valid_dates.any():
                time_diff = (df_forum_primeira.loc[valid_dates, "resposta_enviada_em"] -
                            df_forum_primeira.loc[valid_dates, "post_criado_em"])
                df_forum_primeira.loc[valid_dates, "horas"] = time_diff.dt.total_seconds() / 3600
            else:
                df_forum_primeira["horas"] = np.nan
        else:
            df_forum_primeira["horas"] = np.nan
        
        def classificar_resposta(horas):
            if pd.isna(horas):
                return 'sem resposta'
            elif horas <= 24:
                return 'rapida'
            elif horas > 120:
                return 'atrasada'
            else:
                return 'normal'

        df_forum_primeira["classificacao"] = df_forum_primeira["horas"].apply(classificar_resposta)

        # ===============================
        # Contagens por tutor
        # ===============================
        if not df_forum_primeira.empty:
            forum_count = df_forum_primeira.groupby(["autor_resposta_id", "autor_resposta_completo"])["resposta_id"].count().reset_index()
            forum_count.columns = ["tutor_id", "tutor_completo", "total_respostas_forum"]

            class_count = df_forum_primeira.groupby(["autor_resposta_id", "classificacao"])["resposta_id"].count().unstack(fill_value=0).reset_index()
            class_count = class_count.rename(columns={"autor_resposta_id": "tutor_id"})

            estatisticas = (
                df_forum_primeira.groupby("autor_resposta_id")["horas"]
                .agg(["mean", "median"])
                .reset_index()
                .rename(columns={
                    "autor_resposta_id": "tutor_id",
                    "mean": "media_horas_resposta",
                    "median": "mediana_horas_resposta"
                })
            )

            forum_count = forum_count.merge(estatisticas, on="tutor_id", how="left")
            forum_count = forum_count.merge(class_count, on="tutor_id", how="left")
        else:
            forum_count = pd.DataFrame(columns=[
                "tutor_id", "tutor_completo", "total_respostas_forum",
                "media_horas_resposta", "mediana_horas_resposta"
            ])

        # ===============================
        # Integração com todos os tutores
        # ===============================
        forum_count = df_tutores.merge(forum_count, on=["tutor_id", "tutor_completo"], how="left")

        forum_count["total_respostas_forum"] = forum_count["total_respostas_forum"].fillna(0).astype(int)
        forum_count["media_horas_resposta"] = forum_count["media_horas_resposta"].fillna(0).astype(int)
        forum_count["mediana_horas_resposta"] = forum_count["mediana_horas_resposta"].fillna(0).astype(int)

        for col in ["rapida", "normal", "atrasada", "sem resposta"]:
            if col not in forum_count.columns:
                forum_count[col] = 0
            forum_count[col] = forum_count[col].fillna(0).astype(int)
        
        return forum_count

        
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
        cols = ["rapida", "normal", "atrasada", "sem_resposta"]
        df = pd.DataFrame(columns=["institution_id", "subject_id"] + cols)

        # Processar cursos a partir do ponto onde parou
        for i in range(processed + 1, total + 1):
            result = self.course_analysis(i, version, connector)

            # Garantir estrutura mesmo se não houver dados
            if result is None or result.empty:
                result = pd.DataFrame([{
                    "subject_id": i,
                    **{col: 0 for col in cols}
                }])
            else:
                # Garante que todas as colunas necessárias existam
                result["subject_id"] = i
                for col in cols:
                    if col not in result.columns:
                        result[col] = 0
                    result[col] = result[col].fillna(0).astype(int)

            # Adiciona coluna institution_id e força tipos corretos
            result["institution_id"] = 1
            result = result.infer_objects(copy=False)

            # Mantém apenas colunas relevantes
            df = pd.concat([df, result[["institution_id", "subject_id"] + cols]], ignore_index=True)

            # Atualiza progresso
            analysis_config["processed"] += 1
            self.print_load("Pedagógico", analysis_config["processed"], total, 9)

            # Quando atingir o tamanho do lote, salva no banco
            if analysis_config["processed"] % batch_size == 0:
                self.upsert_sum_dataframe(df, "pedagogico_global", engine)
                df = pd.DataFrame(columns=["institution_id", "subject_id"] + cols)
                return analysis_config  # retorna após salvar o lote

        # Salva o restante ao final do processamento
        if not df.empty:
            self.upsert_sum_dataframe(df, "pedagogico_global", engine)

        return analysis_config


    def upsert_sum_dataframe(self, df, table_name, engine):
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        with engine.begin() as conn:
            for _, row in df.iterrows():
                stmt = insert(table).values(**row.to_dict())
                stmt = stmt.on_conflict_do_update(
                    index_elements=["institution_id", "subject_id"],
                    set_={
                        "rapida": table.c["rapida"] + row["rapida"],
                        "normal": table.c["normal"] + row["normal"],
                        "atrasada": table.c["atrasada"] + row["atrasada"],
                        "sem_resposta": table.c["sem_resposta"] + row["sem_resposta"]
                    }
                )
                conn.execute(stmt)