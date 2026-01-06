from database import Database, DatabaseAdmin
from rabbit import RabbitMQAdmin
from src.analysis_lib.analysis.analyzer import Analyzer
import json
import pandas as pd
from sqlalchemy import text
import numpy as np

pd.set_option('future.no_silent_downcasting', True)

conn = Database()
connector = None

ANALYSIS_MAP = {
    "global_analysis_performance": {
        "func": "general_performance_analysis",
        "status_index": 2,
    },
    "global_analysis_engagement": {
        "func": "general_engagement_analysis",
        "status_index": 1,
    },
    "global_analysis_motivation": {
        "func": "general_motivation_analysis",
        "status_index": 3,
    },
    "global_analysis_pedagogic": {
        "func": "general_pedagogic_analysis",
        "status_index": 4,
    },
    "global_analysis_cognitive": {
        "func": "general_cognitive_analysis",
        "status_index": 5,
    },
    "global_analysis_give_up": {
        "func": "general_give_up_analysis",
        "status_index": 6,
    }
}


class Worker:
    def __init__(self, rabbit_admin):
        self.rabbit_admin = rabbit_admin
        self.db_admin = DatabaseAdmin()
        self.analyzer = Analyzer()

    def subject_analysis(self, message):
        body = message["body"]
        cfg = body.get("analysis_config", {})
        subject_id = int(cfg["subject_id"])
        version = self.db_admin.get_version_in_database(1)
        connector = conn.get_connection_with_config(body.get("db_inst_config"))
        engine = self.db_admin.get_connector()

        subject_df_student = self.students_subject_analysis(subject_id, version, connector, engine)
        subject_df_tutor = self.tutors_subject_analysis(subject_id, version, connector, engine)

        self.save_subject_global_indicators(subject_df_student, engine)

        self.db_admin.update_subject_analysis_status(1, subject_id, "D")
    
    def students_subject_analysis(self, subject_id, version, connector, engine):
        eng = self.analyzer.engagement_analysis(subject_id, 'subject', version, connector)
        per = self.analyzer.performance_analysis(subject_id, 'subject', version, connector)
        mot = self.analyzer.motivation_analysis(subject_id, 'subject', version, connector)
        cog = self.analyzer.cognitive_analysis(subject_id, 'subject', version, connector)
        ped = self.analyzer.pedagogic_analysis(subject_id, 'subject', version, connector)
        giv = self.analyzer.give_up_analysis(subject_id, 'subject', version, connector)

        indicator_dfs = {"eng": eng, "per": per, "mot": mot, "ped": ped, "cog": cog, "giv": giv}
        normalized = []

        for name, df in indicator_dfs.items():
            if df is None or df.empty:
                continue
            
            df = df.copy()
            normalized.append(df)

        if not normalized:
            self.db_admin.update_subject_analysis_status(1, subject_id, "D")
            return

        merged = None

        for df in normalized:
            df = df.copy()

            if merged is None:
                merged = df
                continue

            common_cols = [c for c in merged.columns if c in df.columns and c != "user_id"]

            if common_cols:
                merged = merged.merge(df, on="user_id", how="outer", suffixes=("", "_dup"))
                merged = merged.loc[:, ~merged.columns.str.endswith("_dup")]
            else:
                merged = merged.merge(df, on="user_id", how="outer")
        
        merged["subject_id"] = subject_id
        merged["version"] = version

        rename_map = {
            "num_posts_required": "n_posts_engagement",
            "posts_required_label": "label_engagement",
            "num_posts_unrequired": "n_posts_motivation",
            "motivation_label": "label_motivation",
            "media_percentual": "grade_performance",
            "comparative": "grade_comparative_performance",
            "performance_label": "label_performance",
            "forum_mean_level": "mean_forum_interactions_cognitive",
            "quiz_mean_level": "mean_quiz_interactions_cognitive",
            "assign_mean_level": "mean_assign_interactions_cognitive",
            "cognitive_label": "label_cognitive",
            "n_responses_relation_teacher_student": "n_responses_relation_teacher_student",
            "label_relation_teacher_student": "label_relation_teacher_student",
            "give_up": "label_give_up",
        }
        merged = merged.rename(
            columns={k: v for k, v in rename_map.items() if k in merged.columns}
        )

        if "user_id" in merged.columns:
            merged = merged.rename(columns={"user_id": "student_id"})

        desired_cols = [
            "version",
            "subject_id",
            "student_id", 
            "n_posts_engagement",
            "label_engagement",
            "n_posts_motivation",
            "label_motivation",
            "grade_performance",
            "grade_comparative_performance",
            "label_performance",
            "mean_forum_interactions_cognitive",
            "mean_quiz_interactions_cognitive",
            "mean_assign_interactions_cognitive",
            "label_cognitive",
            "n_responses_relation_teacher_student",
            "label_relation_teacher_student",
            "label_give_up",
        ]

        for c in desired_cols:
            if c not in merged.columns:
                merged[c] = pd.NA

        subject_df = merged[desired_cols]
        subject_df = subject_df.fillna(0)

        subject_df["institution_id"] = 1
        subject_df["subject_id"] = subject_id

        subject_df = subject_df.groupby(
            ["subject_id", "student_id"],
            as_index=False,
        ).agg(
            {
                "version": "first",
                "institution_id": "first",
                "n_posts_engagement": "first",
                "label_engagement": "first",
                "n_posts_motivation": "first",
                "label_motivation": "first",
                "grade_performance": "first",
                "grade_comparative_performance": "first",
                "label_performance": "first",
                "mean_forum_interactions_cognitive": "first",
                "mean_quiz_interactions_cognitive": "first",
                "mean_assign_interactions_cognitive": "first",
                "label_cognitive": "first",
                "n_responses_relation_teacher_student": "first",
                "label_relation_teacher_student": "first",
                "label_give_up": "first",
            }
        )

        subject_df.to_sql("local_indicators_students", engine, if_exists="append", index=False)
        
        return subject_df
    
    def tutors_subject_analysis(self, subject_id, version, connector, engine):
        response_foruns = self.analyzer.response_foruns(subject_id, "subject", version, connector)
        analysis_login = self.analyzer.analysis_login(subject_id, "subject", version, connector)

        if response_foruns is None or response_foruns.empty:
            return

        df = response_foruns.copy()

        df["institution_id"] = 1
        df["subject_id"] = subject_id
        df["version"] = version

        if analysis_login is not None and not analysis_login.empty:
            analysis_login = analysis_login.copy()
            df = df.merge(analysis_login[["tutor_id", "n_login", "label_access", "mean_weekly_course_views_window"]], on="tutor_id", how="left", validate="m:1")

        desired_cols = [
            "institution_id",
            "version",
            "subject_id",
            "tutor_id",

            "median_forums_response_hours",
            "mean_forums_response_hours",
            "label_forums_response",

            "num_response_fast_forum",
            "num_response_late_forum",
            "num_response_normal_forum",

            "median_messages_response_hours",
            "mean_messages_response_hours",
            "label_messages_response",

            "n_login",
            "label_access",
            "mean_weekly_course_views_window"
        ]

        for c in desired_cols:
            if c not in df.columns:
                df[c] = np.nan

        int_cols = [
            "institution_id", "subject_id", "tutor_id",
            "num_response_fast_forum", "num_response_late_forum", "num_response_normal_forum",
            "n_login", "mean_weekly_course_views_window",
        ]
        for c in int_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.groupby(["institution_id", "version", "subject_id", "tutor_id"], as_index=False).agg(
            {c: "first" for c in desired_cols if c not in ["institution_id", "version", "subject_id", "tutor_id"]}
        )

        df = df[desired_cols]
        df.to_sql("local_indicators_tutors", engine, if_exists="append", index=False)
        
        return df
    
    # ------------------------------------------------------------------
    # Calcula as médias da disciplina e salva em global_indicators
    # ------------------------------------------------------------------
    def save_subject_global_indicators(self, subject_df, engine):
        if subject_df.empty:
            return

        df = subject_df.copy()

        # ------------------------------------------------------------------
        # Cálculo da média cognitiva geral do aluno (média das três interações: fórum, quiz e assign)
        # ------------------------------------------------------------------
        df["mean_interactions_cognitive"] = df[
            [
                "mean_forum_interactions_cognitive",
                "mean_quiz_interactions_cognitive",
                "mean_assign_interactions_cognitive",
            ]
        ].mean(axis=1)

        # ------------------------------------------------------------------
        # Converte label_give_up em 0/1 para calcular a média de "true"
        #
        # mean_give_up = proporção de alunos em situação de desistência na disciplina
        # ------------------------------------------------------------------
        def give_up_to_numeric(value):
            if pd.isna(value):
                return np.nan

            if isinstance(value, bool):
                return 1.0 if value else 0.0

            if isinstance(value, (int, float)) and value in (0, 1):
                return float(value)

            s = str(value).strip().lower()
            if s in ("true"):
                return 1.0
            if s in ("false"):
                return 0.0

            return np.nan

        df["give_up_numeric"] = df["label_give_up"].apply(give_up_to_numeric)

        # ------------------------------------------------------------------
        # Agregação por disciplina na instituição
        #
        # mean_posts_engagement                   -> média de n_posts_engagement
        # mean_posts_motivation                   -> média de n_posts_motivation
        # mean_grade_performance                  -> média de grade_performance
        # mean_interactions_cognitive             -> média da média cognitiva
        # mean_give_up                            -> média de give_up_numeric (proporção de "true")
        # mean_responses_relation_teacher_student -> média de número de respostas do tutor e professor para os alunos
        # ------------------------------------------------------------------
        global_subject_df = df.groupby(["institution_id", "version", "subject_id"], as_index=False,).agg(
                mean_posts_engagement=("n_posts_engagement", "mean"),
                mean_posts_motivation=("n_posts_motivation", "mean"),
                mean_grade_performance=("grade_performance", "mean"),
                mean_interactions_cognitive=("mean_interactions_cognitive", "mean"),
                mean_responses_relation_teacher_student = ("n_responses_relation_teacher_student", "mean"),
                mean_give_up=("give_up_numeric", "mean"),
            )

        # ------------------------------------------------------------------
        # Labels globais ainda não calculados -> NA
        # ------------------------------------------------------------------
        for col in [
            "label_engagement",
            "label_motivation",
            "label_performance",
            "label_cognitive",
            "label_relation_teacher_student",
            "label_give_up",
        ]:
            global_subject_df[col] = pd.NA

        global_subject_df = global_subject_df[
            [
                "institution_id",
                "version",
                "subject_id",
                "mean_posts_engagement",
                "label_engagement",
                "mean_posts_motivation",
                "label_motivation",
                "mean_grade_performance",
                "label_performance",
                "mean_interactions_cognitive",
                "label_cognitive",
                "mean_responses_relation_teacher_student",
                "label_relation_teacher_student",
                "mean_give_up",
                "label_give_up",
            ]
        ]

        global_subject_df.to_sql(
            "global_indicators",
            engine,
            if_exists="append",  
            index=False,
        )
                
    def discretize_global_indicators(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        version = self.db_admin.get_version_in_database(institution_id)

        df = pd.read_sql_table("global_indicators", engine)

        if df.empty:
            return

        mask = (df["institution_id"] == institution_id) & (df["version"] == str(version))
        df_sub = df.loc[mask].copy()

        if df_sub.empty:
            return

        def discretize_metric(series: pd.Series) -> pd.Series:
            if series.isna().all():
                return pd.Series([pd.NA] * len(series), index=series.index)

            values = series.astype(float)

            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            labels = pd.Series(index=values.index, dtype="object")

            labels[values < lower] = "muito_baixo"
            labels[(values >= lower) & (values < q1)] = "baixo"
            labels[(values >= q1) & (values <= q3)] = "medio"
            labels[(values > q3) & (values <= upper)] = "alto"
            labels[values > upper] = "muito_alto"

            labels[values.isna()] = pd.NA

            return labels

        metric_to_label_col = {
            "mean_posts_engagement": "label_engagement",
            "mean_posts_motivation": "label_motivation",
            "mean_grade_performance": "label_performance",
            "mean_interactions_cognitive": "label_cognitive",
            "mean_responses_relation_teacher_student": "label_relation_teacher_student",
            "mean_give_up": "label_give_up",
        }

        for metric_col, label_col in metric_to_label_col.items():
            if metric_col in df_sub.columns:
                df_sub[label_col] = discretize_metric(df_sub[metric_col])
            else:
                df_sub[label_col] = pd.NA
                
        
        def clean_na(value):
                    if pd.isna(value):
                        return None
                    return value

        # ------------------------------------------------------------------
        # Atualiza a tabela global_indicators no banco
        # PK: (institution_id, version, subject_id)
        # ------------------------------------------------------------------
        with engine.begin() as conn:
            for _, row in df_sub.iterrows():
                params = {
                    "institution_id": int(row["institution_id"]),
                    "version": str(row["version"]),
                    "subject_id": int(row["subject_id"]),
                    "label_engagement": clean_na(row.get("label_engagement")),
                    "label_motivation": clean_na(row.get("label_motivation")),
                    "label_performance": clean_na(row.get("label_performance")),
                    "label_cognitive": clean_na(row.get("label_cognitive")),
                    "label_relation_teacher_student": clean_na(row.get("label_relation_teacher_student")),
                    "label_give_up": clean_na(row.get("label_give_up")),
                }
                
                conn.execute(
                    text(
                        """
                        UPDATE global_indicators
                        SET
                            label_engagement = :label_engagement,
                            label_motivation = :label_motivation,
                            label_performance = :label_performance,
                            label_cognitive = :label_cognitive,
                            label_relation_teacher_student = :label_relation_teacher_student,
                            label_give_up = :label_give_up
                        WHERE
                            institution_id = :institution_id
                            AND version = :version
                            AND subject_id = :subject_id
                        """
                    ),
                    params,
                )

def continuously_listen():
    rabbit_admin = RabbitMQAdmin()

    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        analysis_type = message.get("body", {}).get("type")
        worker = Worker(rabbit_admin)

        if analysis_type == "subject_analysis":
            worker.subject_analysis(message)
        elif analysis_type in (
            "global_analysis_engagement",
            "global_analysis_pedagogic",
            "global_analysis_performance",
            "global_analysis_motivation",
            "global_analysis_cognitive",
            "global_analysis_give_up",
        ):
            worker.global_analysis(message)
        else:
            print(f"[!] Tipo de análise desconhecido: {analysis_type}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

        # ------------------------------------------------------------------
        # Depois de processar a mensagem, verifica se ainda há itens na fila.
        # Se não houver mais mensagens pendentes, roda a discretização dos indicadores globais.
        # ------------------------------------------------------------------
        state = ch.queue_declare(queue='tasks_to_process', passive=True)
        if state.method.message_count == 0:
            worker.discretize_global_indicators(1)

    rabbit_admin.channel.basic_qos(prefetch_count=1)
    rabbit_admin.channel.basic_consume(queue='tasks_to_process', on_message_callback=callback)

    print(' [*] Aguardando mensagens. Para sair pressione CTRL+C')
    while True:
        # try:
        rabbit_admin.channel.start_consuming()
        # except Exception as e:
        #     print(f"Erro: {e}")

if __name__ == '__main__':
    print("Worker iniciado. Aguardando mensagens...")
    continuously_listen()
