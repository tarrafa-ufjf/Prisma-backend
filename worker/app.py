from database import Database, DatabaseAdmin
from rabbit import RabbitMQAdmin
from src.analysis_lib.analysis.analyzer import Analyzer
from src.analysis_lib.mapper.map import Mapper
import json
import pandas as pd
from sqlalchemy import text
import numpy as np
import math

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
        self.mapper = Mapper()

    def subject_analysis(self, message):
        body = message["body"]
        cfg = body.get("analysis_config", {})
        subject_id = int(cfg["subject_id"])
        version = self.db_admin.get_version_in_database(1)
        connector = conn.get_connection_with_config(body.get("db_inst_config"))
        engine = self.db_admin.get_connector()

        # subject_df_student = self.students_subject_analysis(subject_id, version, connector, engine)
        subject_df_tutor = self.tutors_subject_analysis(subject_id, version, connector, engine)
        
        # self.save_subject_global_indicators_students(subject_df_student, engine)
        self.save_subject_global_indicators_tutors(subject_df_tutor, engine)

        self.db_admin.update_subject_analysis_status(1, subject_id, "D")
    
    def students_subject_analysis(self, subject_id, version, connector, engine):
        print("A")
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
        
        print("B")
        
        return subject_df
    
    def _best_block_dynamic_window(self, df_daily_events, gap_days: int = 21, pct_of_peak: float = 0.02, floor_min: int = 10,):
            """
            - A ideia é ignorar "cauda longa" (acessos anos depois).
            - 1) Agrega logs por dia (df_daily_events já vem assim).
            - 2) Calcula pico_diario = max(events).
            - 3) Define "dia ativo" como: events_dia >= max(floor_min, ceil(pct_of_peak * pico_diario))
                * O pct escala com o tamanho da turma/curso
                * O floor evita que cursos pequenos considerem 1-2 eventos como "dia ativo"
            - 4) Considera apenas dias ativos e agrupa em blocos permitindo gaps <= gap_days.
            - 5) Escolhe o bloco com maior soma de eventos (bloco "principal" do curso).
            """
            if df_daily_events is None or df_daily_events.empty:
                return None, None
            
            daily = df_daily_events.copy()

            if "day" not in daily.columns or "events" not in daily.columns:
                return None, None

            daily["day"] = pd.to_datetime(daily["day"], errors="coerce").dt.normalize()
            daily["events"] = pd.to_numeric(daily["events"], errors="coerce").fillna(0).astype(int)
            daily = daily.dropna(subset=["day"]).sort_values("day").reset_index(drop=True)

            if daily.empty or daily["events"].sum() <= 0:
                return None, None

            peak_daily = int(daily["events"].max())
            active_min_dynamic = max(floor_min, int(math.ceil(pct_of_peak * peak_daily)))

            active_days = daily[daily["events"] >= active_min_dynamic].copy()
            if active_days.empty:
                pos = daily[daily["events"] > 0] # se nada bater o active_min, devolve janela total (dias com evento > 0)
                if pos.empty:
                    return None, None
                return pos["day"].iloc[0], pos["day"].iloc[-1]

            active_days = active_days.sort_values("day").reset_index(drop=True)

            # Quebra em blocos quando gap > gap_days
            active_days["prev_day"] = active_days["day"].shift(1)
            active_days["gap"] = (active_days["day"] - active_days["prev_day"]).dt.days
            active_days["new_block"] = active_days["gap"].isna() | (active_days["gap"] > gap_days)
            active_days["block_id"] = active_days["new_block"].cumsum()

            agg = active_days.groupby("block_id").agg(
                start_day=("day", "min"),
                end_day=("day", "max"),
                events_sum=("events", "sum"),
                days=("day", "count"),
            ).reset_index()

            best = agg.sort_values(["events_sum", "days"], ascending=[False, False]).iloc[0]

            start_at = best["start_day"]
            end_at = best["end_day"]
                    
            return start_at, end_at
    
    def tutors_subject_analysis(self, subject_id, version, connector, engine):       
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        df_daily_events = self.mapper.fetch_daily_events(connector, version, subject_id)
        start_at, end_at = self._best_block_dynamic_window(df_daily_events, gap_days=21, pct_of_peak=0.02, floor_min=10)
        print(start_at, " ", end_at)
        print("AAAA")
        response_foruns = self.analyzer.response_foruns(subject_id, "subject", version, connector, start_at, end_at)
        print("1")
        analysis_login_df = self.analyzer.analysis_login(subject_id, "subject", version, connector, start_at, end_at)
        print("2")
        analysis_feedback_df = self.analyzer.analysis_feedback(subject_id, "subject", version, connector, start_at, end_at)
        print("3")
        
        print(analysis_feedback_df)

        if (response_foruns is None or response_foruns.empty) and (analysis_login_df is None or analysis_login_df.empty):
            return None

        tutor_ids = []

        if response_foruns is not None and not response_foruns.empty:
            tutor_ids.extend(response_foruns["tutor_id"].dropna().astype(int).tolist())

        if analysis_login_df is not None and not analysis_login_df.empty:
            tutor_ids.extend(analysis_login_df["tutor_id"].dropna().astype(int).tolist())

        tutor_ids = sorted(set(tutor_ids))

        df = pd.DataFrame({"tutor_id": tutor_ids})
        df["institution_id"] = 1
        df["subject_id"] = subject_id
        df["version"] = version

        if response_foruns is not None and not response_foruns.empty:
            df = df.merge(
                response_foruns,
                on="tutor_id",
                how="left",
            )

        if analysis_login_df is not None and not analysis_login_df.empty:
            df = df.merge(
                analysis_login_df[["tutor_id", "n_login", "n_access_subject", "n_login_weekly", "n_login_label", 
                                    "n_login_weekly_label", "label_access"]],
                on="tutor_id",
                how="left",
                validate="1:1",
            )
            
        if analysis_feedback_df is not None and not analysis_feedback_df.empty:
            df = df.merge(
                analysis_feedback_df[["tutor_id","total_correcoes","correcoes_com_feedback","percentual_feedback","feedback_textual","feedback_pdf",
                                            "total_correcoes_label", "correcoes_com_feedback_label", "percentual_feedback_label",
                                            "feedback_textual_label", "feedback_pdf_label", "label_final_feedback"]],
                on="tutor_id",
                how="left",
                validate="1:1",
            )
            
        df["label_forums_response"] = df["label_forums_response"].fillna("Muito baixo")

        for col in [
            "n_login", "n_access_subject", "n_login_weekly",
            
            "total_respostas_forum", "median_forums_response_hours", "mean_forums_response_hours", "score",
            "num_response_fast_forum", "num_response_late_forum", "num_response_normal_forum",
            
            "total_correcoes","correcoes_com_feedback","percentual_feedback","feedback_textual","feedback_pdf",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        desired_cols = [
            "institution_id", "version", "subject_id", "tutor_id",
            
            "total_respostas_forum", "median_forums_response_hours", "mean_forums_response_hours", "score",
            "mean_forums_response_hours_label", "median_forums_response_hours_label", "score_label",
            "label_forums_response", "num_response_fast_forum", "num_response_late_forum", "num_response_normal_forum",
            
            "n_login", "n_access_subject", "n_login_weekly", "n_login_label", "n_login_weekly_label", "label_access",
            
            "total_correcoes","correcoes_com_feedback","percentual_feedback","feedback_textual","feedback_pdf",
            "total_correcoes_label", "correcoes_com_feedback_label", "percentual_feedback_label",
            "feedback_textual_label", "feedback_pdf_label", "label_final_feedback"
        ]

        for c in desired_cols:
            if c not in df.columns:
                df[c] = np.nan

        df = df.groupby(["institution_id", "version", "subject_id", "tutor_id"], as_index=False).agg(
            {c: "first" for c in desired_cols if c not in ["institution_id", "version", "subject_id", "tutor_id"]}
        )

        df = df[desired_cols]
        df.to_sql("local_indicators_tutors", engine, if_exists="append", index=False)

        # ---- UPDATE subjects_status (1 vez por subject) ----
        def to_db_date(x):
            if x is None or (isinstance(x, pd.Timestamp) and pd.isna(x)):
                return None
            return pd.to_datetime(x).date()  

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE subjects_status
                    SET
                        start_date = :start_date,
                        end_date = :end_date
                    WHERE
                        institution_id = :institution_id
                        AND subject_id = :subject_id
                    """
                ),
                {
                    "institution_id": 1,
                    "subject_id": subject_id,
                    "start_date": to_db_date(start_at),
                    "end_date": to_db_date(end_at),
                },
            )

        return df
    
    # ------------------------------------------------------------------
    # Calcula as médias da disciplina e salva em global_indicators_student
    # ------------------------------------------------------------------
    def save_subject_global_indicators_students(self, subject_df, engine):
        if subject_df is None or subject_df.empty:
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
            "global_indicators_student",
            engine,
            if_exists="append",  
            index=False,
        )
                
    def discretize_global_indicators(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        version = self.db_admin.get_version_in_database(institution_id)

        df = pd.read_sql_table("global_indicators_student", engine)

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
        # Atualiza a tabela global_indicators_student no banco
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
                        UPDATE global_indicators_student
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
    
    def save_subject_global_indicators_tutors(self, subject_df, engine):
        if subject_df is None or subject_df.empty:
            return

        df = subject_df.copy()

        global_subject_df = df.groupby(["institution_id", "version", "subject_id"], as_index=False,).agg(
                mean_score=("score", "mean"),
            )
        
        global_subject_df['mean_access'] = 0

        # ------------------------------------------------------------------
        # Labels globais ainda não calculados -> NA
        # ------------------------------------------------------------------
        for col in [
            "label_forum_response",
            "label_access",
        ]:
            global_subject_df[col] = pd.NA

        global_subject_df = global_subject_df[
            [
                "institution_id",
                "version",
                "subject_id",
                "mean_score",
                "label_forum_response",
                "mean_access",
                "label_access",
            ]
        ]

        global_subject_df.to_sql(
            "global_indicators_tutors",
            engine,
            if_exists="append",  
            index=False,
        )

    def discretize_global_indicators_tutors(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        version = self.db_admin.get_version_in_database(institution_id)

        df = pd.read_sql_table("global_indicators_tutors", engine)

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
            "mean_score": "label_forum_response",
            "mean_access": "label_access",
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
        # Atualiza a tabela global_indicators_tutors no banco
        # PK: (institution_id, version, subject_id)
        # ------------------------------------------------------------------
        with engine.begin() as conn:
            for _, row in df_sub.iterrows():
                params = {
                    "institution_id": int(row["institution_id"]),
                    "version": str(row["version"]),
                    "subject_id": int(row["subject_id"]),
                    "label_forum_response": clean_na(row.get("label_forum_response")),
                    "label_access": clean_na(row.get("label_access")),
                }
                
                conn.execute(
                    text(
                        """
                        UPDATE global_indicators_tutors
                        SET
                            label_forum_response = :label_forum_response,
                            label_access = :label_access
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
            worker.discretize_global_indicators_tutors(1)

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
