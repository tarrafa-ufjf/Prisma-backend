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

        return df_final[["institution_id","version","subject_id","user_id","n_responses_relation_teacher_student","label_relation_teacher_student"]]
        
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