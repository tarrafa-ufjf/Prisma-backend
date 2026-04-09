from database import Database, DatabaseAdmin
from rabbit import RabbitMQAdmin
from src.analysis_lib.analysis.analyzer import Analyzer
from src.analysis_lib.mapper.map import Mapper
from indicator_publisher import IndicatorPublisher, register_default_indicators
import json
import pandas as pd
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
import numpy as np
import math
import time
import traceback

pd.set_option("future.no_silent_downcasting", True)

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
    },
}


class Worker:
    def __init__(self, rabbit_admin):
        self.rabbit_admin = rabbit_admin
        self.db_admin = DatabaseAdmin()
        self.analyzer = Analyzer()
        self.mapper = Mapper()
        self.engine = self.db_admin.get_connector()
        self.publisher = IndicatorPublisher(retries=0, sleep_s=0.3)
        register_default_indicators(self.publisher, self.analyzer)

    def set_mysql_session_timeouts(
        self,
        conn,
        *,
        lock_wait_s=50,
        net_timeout_s=120,
        idle_timeout_s=28800,
        max_exec_ms=600_000,
    ):
        cur = conn.cursor()
        try:
            desired = {
                "innodb_lock_wait_timeout": int(lock_wait_s),
                "lock_wait_timeout": int(lock_wait_s),
                "net_read_timeout": int(net_timeout_s),
                "net_write_timeout": int(net_timeout_s),
                "wait_timeout": int(idle_timeout_s),
                "max_execution_time": int(max_exec_ms),
                "max_statement_time": int(max_exec_ms / 1000),
            }

            applied = {}

            for var, val in desired.items():
                cur.execute("SHOW VARIABLES LIKE %s", (var,))
                row = cur.fetchone()
                if not row:
                    continue

                try:
                    cur.execute(f"SET SESSION {var} = %s", (val,))
                    cur.execute("SHOW VARIABLES LIKE %s", (var,))
                    applied[var] = cur.fetchone()
                except Exception as e:
                    applied[var] = f"FAILED: {e}"

            # print("[mysql session timeouts] applied:", applied)
            return applied

        finally:
            cur.close()

    def _table(self, engine, table_name):
        metadata = MetaData()
        return Table(table_name, metadata, autoload_with=engine)

    def _df_to_records(self, df):
        if df is None or df.empty:
            return []

        cleaned = df.astype(object).where(pd.notna(df), None)
        return cleaned.to_dict(orient="records")

    def _upsert_dynamic(self, engine, table_name, records, pk_columns):
        if not records:
            return

        table = self._table(engine, table_name)
        stmt = pg_insert(table)

        record_keys = []
        seen = set()
        for key in records[0].keys():
            if key not in seen:
                record_keys.append(key)
                seen.add(key)

        update_columns = [col for col in record_keys if col not in pk_columns]

        if update_columns:
            stmt = stmt.on_conflict_do_update(
                index_elements=pk_columns,
                set_={col: stmt.excluded[col] for col in update_columns},
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=pk_columns)

        with engine.begin() as conn:
            conn.execute(stmt, records)

    def _aggregate_first_by_keys(self, df, key_columns):
        if df is None or df.empty:
            return df

        value_columns = [c for c in df.columns if c not in key_columns]
        if not value_columns:
            return df[key_columns].drop_duplicates().reset_index(drop=True)

        return df.groupby(key_columns, as_index=False).agg(
            {column: "first" for column in value_columns}
        )

    def subject_analysis(self, message):
        body = message["body"]
        cfg = body.get("analysis_config", {})
        subject_id = int(cfg["subject_id"])
        channel = cfg.get("channel", "diario")
        version = self.db_admin.get_version_in_database(1, engine=self.engine)

        connector = conn.get_connection_with_config(body.get("db_inst_config"))
        engine = self.engine

        try:
            self.db_admin.update_subject_analysis_status(
                1,
                subject_id,
                "P",
                update_type=channel,
                engine=engine,
            )

            self.set_mysql_session_timeouts(
                connector,
                lock_wait_s=50,
                net_timeout_s=120,
                idle_timeout_s=28800,
                max_exec_ms=600_000,
            )

            subject_df_student = self.students_subject_analysis(
                subject_id, version, connector, engine, channel=channel
            )
            subject_df_tutor = self.tutors_subject_analysis(
                subject_id, version, connector, engine, channel=channel
            )

            self.save_subject_global_indicators_students(subject_df_student, engine)
            self.save_NaN_global_indicators_tutors(subject_df_tutor, engine)

            self.db_admin.update_subject_analysis_status(
                1,
                subject_id,
                "D",
                update_type=channel,
                engine=engine,
            )

        except Exception as e:
            try:
                self.db_admin.update_subject_analysis_status(
                    1,
                    subject_id,
                    "E",
                    update_type=channel,
                    engine=engine,
                )
            except Exception as status_error:
                print(
                    f"[subject_analysis] subject_id={subject_id} channel={channel} "
                    f"failed_to_set_error_status={status_error}"
                )

            print(
                f"[subject_analysis] subject_id={subject_id} channel={channel} error={e}"
            )
            traceback.print_exc()
            raise

        finally:
            try:
                connector.close()
            except Exception:
                pass

    def students_subject_analysis(
        self, subject_id, version, connector, engine, channel="diario"
    ):
        print(f"students_subject_analysis_{subject_id}")
        notify_result = self.publisher.notify(
            actor="student",
            channel=channel,
            subject_id=subject_id,
            version=version,
            connector=connector,
            engine=engine,
            mapper=self.mapper,
        )
        indicator_dfs = notify_result.get("results", {})
        indicator_errors = notify_result.get("errors", {})

        for indicator_name in indicator_dfs.keys():
            self.db_admin.upsert_indicator_status(
                1, subject_id, "student", indicator_name, "D", engine
            )

        for indicator_name in indicator_errors.keys():
            self.db_admin.upsert_indicator_status(
                1, subject_id, "student", indicator_name, "E", engine
            )

        if indicator_errors:
            print(
                f"[students_subject_analysis] actor=student channel={channel} errors={list(indicator_errors.keys())}"
            )
        normalized = []

        for name, df in indicator_dfs.items():
            if df is None or df.empty:
                continue

            df = df.copy()
            normalized.append(df)

        if not normalized:
            self.db_admin.update_subject_analysis_status(
                1,
                subject_id,
                "D",
                update_type=channel,
                engine=engine,
            )
            return

        merged = None

        for df in normalized:
            df = df.copy()

            if merged is None:
                merged = df
                continue

            common_cols = [
                c for c in merged.columns if c in df.columns and c != "user_id"
            ]

            if common_cols:
                merged = merged.merge(
                    df, on="user_id", how="outer", suffixes=("", "_dup")
                )
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

        merged["institution_id"] = 1

        desired_cols = [
            "institution_id",
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

        existing_cols = [c for c in desired_cols if c in merged.columns]
        subject_df = merged[existing_cols].copy()

        numeric_cols = [
            "n_posts_engagement",
            "n_posts_motivation",
            "grade_performance",
            "grade_comparative_performance",
            "mean_forum_interactions_cognitive",
            "mean_quiz_interactions_cognitive",
            "mean_assign_interactions_cognitive",
            "n_responses_relation_teacher_student",
        ]
        for c in numeric_cols:
            if c in subject_df.columns:
                subject_df[c] = pd.to_numeric(subject_df[c], errors="coerce").fillna(0)

        subject_df["subject_id"] = subject_id

        subject_df = self._aggregate_first_by_keys(
            subject_df,
            ["institution_id", "version", "subject_id", "student_id"],
        )

        records = self._df_to_records(subject_df)
        self._upsert_dynamic(
            engine,
            "local_indicators_students",
            records,
            ["institution_id", "version", "subject_id", "student_id"],
        )

        return subject_df

    def _best_block_dynamic_window(
        self,
        df_daily_events,
        gap_days: int = 21,
        pct_of_peak: float = 0.02,
        floor_min: int = 10,
    ):
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
        daily["events"] = (
            pd.to_numeric(daily["events"], errors="coerce").fillna(0).astype(int)
        )
        daily = daily.dropna(subset=["day"]).sort_values("day").reset_index(drop=True)

        if daily.empty or daily["events"].sum() <= 0:
            return None, None

        peak_daily = int(daily["events"].max())
        active_min_dynamic = max(floor_min, int(math.ceil(pct_of_peak * peak_daily)))

        active_days = daily[daily["events"] >= active_min_dynamic].copy()
        if active_days.empty:
            pos = daily[
                daily["events"] > 0
            ]  # se nada bater o active_min, devolve janela total (dias com evento > 0)
            if pos.empty:
                return None, None
            return pos["day"].iloc[0], pos["day"].iloc[-1]

        active_days = active_days.sort_values("day").reset_index(drop=True)

        # Quebra em blocos quando gap > gap_days
        active_days["prev_day"] = active_days["day"].shift(1)
        active_days["gap"] = (active_days["day"] - active_days["prev_day"]).dt.days
        active_days["new_block"] = active_days["gap"].isna() | (
            active_days["gap"] > gap_days
        )
        active_days["block_id"] = active_days["new_block"].cumsum()

        agg = (
            active_days.groupby("block_id")
            .agg(
                start_day=("day", "min"),
                end_day=("day", "max"),
                events_sum=("events", "sum"),
                days=("day", "count"),
            )
            .reset_index()
        )

        best = agg.sort_values(["events_sum", "days"], ascending=[False, False]).iloc[0]

        start_at = best["start_day"]
        end_at = best["end_day"]

        return start_at, end_at

    def _ensure_one_row_per_tutor(self, df_in, cols):
        df_out = df_in.copy()

        keep = [c for c in cols if c in df_out.columns]
        df_out = df_out[keep].copy()

        df_out["tutor_id"] = pd.to_numeric(df_out["tutor_id"], errors="coerce")
        df_out = df_out.dropna(subset=["tutor_id"])
        df_out["tutor_id"] = df_out["tutor_id"].astype(int)

        df_out = (
            df_out.sort_values("tutor_id").groupby("tutor_id", as_index=False).first()
        )

        return df_out

    def tutors_subject_analysis(
        self, subject_id, version, connector, engine, channel="diario"
    ):
        print(f"tutors_subject_analysis_{subject_id}")
        df_daily_events = self.mapper.fetch_daily_events(connector, version, subject_id)
        start_at, end_at = self._best_block_dynamic_window(
            df_daily_events, gap_days=21, pct_of_peak=0.02, floor_min=10
        )

        df_all_tutors = self.mapper.fetch_all_tutors(
            connector, version, subject_id, start_at, end_at
        )
        if df_all_tutors is None or df_all_tutors.empty:
            return None

        tutor_ids = set(
            pd.to_numeric(df_all_tutors["tutor_id"], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )

        tutor_ids = sorted(set(tutor_ids))

        if not tutor_ids:
            return None

        notify_result = self.publisher.notify(
            actor="tutor",
            channel=channel,
            subject_id=subject_id,
            version=version,
            connector=connector,
            engine=engine,
            mapper=self.mapper,
            start_at=start_at,
            end_at=end_at,
            tutor_ids=tutor_ids,
        )
        indicator_dfs = notify_result.get("results", {})
        indicator_errors = notify_result.get("errors", {})

        for indicator_name in indicator_dfs.keys():
            self.db_admin.upsert_indicator_status(
                1, subject_id, "tutor", indicator_name, "D", engine
            )

        for indicator_name in indicator_errors.keys():
            self.db_admin.upsert_indicator_status(
                1, subject_id, "tutor", indicator_name, "E", engine
            )

        analysis_response_foruns = indicator_dfs.get("response_foruns")
        analysis_feedback_df = indicator_dfs.get("feedback")
        analysis_login_df = indicator_dfs.get("login")
        if indicator_errors:
            print(
                f"[tutors_subject_analysis] actor=tutor channel={channel} errors={list(indicator_errors.keys())}"
            )

        if (
            (analysis_response_foruns is None or analysis_response_foruns.empty)
            and (analysis_login_df is None or analysis_login_df.empty)
            and (analysis_feedback_df is None or analysis_feedback_df.empty)
        ):
            return None

        df = pd.DataFrame({"tutor_id": tutor_ids}).merge(
            df_all_tutors[["tutor_id"]].drop_duplicates(),
            on="tutor_id",
            how="inner",
            validate="m:1",
        )
        df["institution_id"] = 1
        df["subject_id"] = subject_id
        df["version"] = version

        if analysis_response_foruns is not None and not analysis_response_foruns.empty:
            forum_cols = list(analysis_response_foruns.columns)
            forum_1 = self._ensure_one_row_per_tutor(
                analysis_response_foruns, forum_cols
            )

            df = df.merge(forum_1, on="tutor_id", how="left", validate="1:1")

        if analysis_feedback_df is not None and not analysis_feedback_df.empty:
            feedback_cols = [
                "tutor_id",
                "n_corrections",
                "n_corrections_with_feedback",
                "percentage_feedback",
                "n_textual_feedback",
                "n_feedback_pdf",
                "n_corrections_label",
                "n_corrections_with_feedback_label",
                "percentage_feedback_label",
                "n_textual_feedback_label",
                "n_feedback_pdf_label",
                "label_feedback",
            ]
            feedback_1 = self._ensure_one_row_per_tutor(
                analysis_feedback_df, feedback_cols
            )

            df = df.merge(feedback_1, on="tutor_id", how="left", validate="1:1")

        if analysis_login_df is not None and not analysis_login_df.empty:
            login_cols = [
                "tutor_id",
                "n_login",
                "n_login_subject",
                "n_login_weekly",
                "n_login_label",
                "n_login_weekly_label",
                "label_access",
                "maximum_inactivity_days",
                "maximum_inactivity_days_label",
            ]
            login_1 = self._ensure_one_row_per_tutor(analysis_login_df, login_cols)

            df = df.merge(login_1, on="tutor_id", how="left", validate="1:1")

        if "label_forums_response" in df.columns:
            df["label_forums_response"] = df["label_forums_response"].fillna(
                "Muito baixo"
            )

        for col in [
            "n_login",
            "n_login_subject",
            "n_login_weekly",
            "total_response_forum",
            "median_forums_response_hours",
            "mean_forums_response_hours",
            "score_access",
            "num_response_fast_forum",
            "num_response_late_forum",
            "num_response_normal_forum",
            "n_corrections",
            "n_corrections_with_feedback",
            "percentage_feedback",
            "n_textual_feedback",
            "n_feedback_pdf",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        desired_cols = [
            "institution_id",
            "version",
            "subject_id",
            "tutor_id",
            "total_response_forum",
            "median_forums_response_hours",
            "mean_forums_response_hours",
            "score_access",
            "mean_forums_response_hours_label",
            "median_forums_response_hours_label",
            "score_access_label",
            "label_forums_response",
            "num_response_fast_forum",
            "num_response_late_forum",
            "num_response_normal_forum",
            "n_login",
            "n_login_subject",
            "n_login_weekly",
            "n_login_label",
            "n_login_weekly_label",
            "label_access",
            "maximum_inactivity_days",
            "maximum_inactivity_days_label",
            "n_corrections",
            "n_corrections_with_feedback",
            "percentage_feedback",
            "n_textual_feedback",
            "n_feedback_pdf",
            "n_corrections_label",
            "n_corrections_with_feedback_label",
            "percentage_feedback_label",
            "n_textual_feedback_label",
            "n_feedback_pdf_label",
            "label_feedback",
        ]

        existing_cols = [c for c in desired_cols if c in df.columns]
        df = df[existing_cols].copy()
        df = self._aggregate_first_by_keys(
            df,
            ["institution_id", "version", "subject_id", "tutor_id"],
        )

        records = self._df_to_records(df)
        self._upsert_dynamic(
            engine,
            "local_indicators_tutors",
            records,
            ["institution_id", "version", "subject_id", "tutor_id"],
        )

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
                        end_date = :end_date,
                        updated_at = NOW(),
                        update_type = :update_type
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
                    "update_type": channel or "nao_indicado",
                },
            )

        return df

    # ------------------------------------------------------------------
    # Calcula as médias da disciplina e salva em global_indicators_students
    # ------------------------------------------------------------------
    def save_subject_global_indicators_students(self, subject_df, engine):
        print("save_subject_global_indicators_students")
        if subject_df is None or subject_df.empty:
            return

        subject_id = int(pd.to_numeric(subject_df["subject_id"], errors="coerce").iloc[0])
        version = str(subject_df["version"].iloc[0])

        df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM local_indicators_students
                WHERE subject_id = :subject_id
                AND version = :version
                """
            ),
            engine,
            params={"subject_id": subject_id, "version": version},
        )

        if df.empty:
            return

        # ------------------------------------------------------------------
        # Cálculo da média cognitiva geral do aluno (média das três interações: fórum, quiz e assign)
        # ------------------------------------------------------------------
        cognitive_columns = [
            column
            for column in [
                "mean_forum_interactions_cognitive",
                "mean_quiz_interactions_cognitive",
                "mean_assign_interactions_cognitive",
            ]
            if column in df.columns
        ]
        if cognitive_columns:
            df["mean_interactions_cognitive"] = (
                df[cognitive_columns]
                .apply(pd.to_numeric, errors="coerce")
                .mean(axis=1)
            )
        else:
            df["mean_interactions_cognitive"] = np.nan

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
            if s == "true":
                return 1.0
            if s == "false":
                return 0.0

            return np.nan

        if "label_give_up" in df.columns:
            df["give_up_numeric"] = df["label_give_up"].apply(give_up_to_numeric)
        else:
            df["give_up_numeric"] = np.nan

        if "institution_id" in df.columns:
            institution_id = int(
                pd.to_numeric(df["institution_id"], errors="coerce").dropna().iloc[0]
            )
        else:
            institution_id = 1
            df["institution_id"] = institution_id

        grouped_keys = {
            "institution_id": institution_id,
            "version": version,
            "subject_id": subject_id,
        }
        global_values = {
            "mean_posts_engagement": np.nan,
            "mean_posts_motivation": np.nan,
            "mean_grade_performance": np.nan,
            "mean_interactions_cognitive": np.nan,
            "mean_responses_relation_teacher_student": np.nan,
            "mean_give_up": np.nan,
        }

        metric_sources = {
            "mean_posts_engagement": "n_posts_engagement",
            "mean_posts_motivation": "n_posts_motivation",
            "mean_grade_performance": "grade_performance",
            "mean_interactions_cognitive": "mean_interactions_cognitive",
            "mean_responses_relation_teacher_student": "n_responses_relation_teacher_student",
            "mean_give_up": "give_up_numeric",
        }
        for target_column, source_column in metric_sources.items():
            if source_column in df.columns:
                global_values[target_column] = pd.to_numeric(
                    df[source_column], errors="coerce"
                ).mean()

        global_subject_df = pd.DataFrame([{**grouped_keys, **global_values}])

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

        records = self._df_to_records(global_subject_df)
        self._upsert_dynamic(
            engine,
            "global_indicators_students",
            records,
            ["institution_id", "version", "subject_id"],
        )

    def discretize_global_indicators(self, institution_id: int = 1):
        engine = self.engine
        version = self.db_admin.get_version_in_database(institution_id, engine=engine)

        df = pd.read_sql_table("global_indicators_students", engine)

        if df.empty:
            return

        mask = (df["institution_id"] == institution_id) & (
            df["version"] == str(version)
        )
        df_sub = df.loc[mask].copy()

        if df_sub.empty:
            return

        def discretize_metric(series):
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
        # Atualiza a tabela global_indicators_students no banco
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
                    "label_relation_teacher_student": clean_na(
                        row.get("label_relation_teacher_student")
                    ),
                    "label_give_up": clean_na(row.get("label_give_up")),
                }

                conn.execute(
                    text(
                        """
                        UPDATE global_indicators_students
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

    def save_NaN_global_indicators_tutors(self, subject_df, engine):
        print("save_NaN_global_indicators_tutors")

        if subject_df is None or subject_df.empty:
            return

        required_keys = ["institution_id", "version", "subject_id"]
        for k in required_keys:
            if k not in subject_df.columns:
                raise ValueError(f"subject_df precisa ter a coluna '{k}'")

        institution_id = int(
            pd.to_numeric(subject_df["institution_id"], errors="coerce").dropna().iloc[0]
        )
        version = str(subject_df["version"].iloc[0])
        subject_id = int(
            pd.to_numeric(subject_df["subject_id"], errors="coerce").dropna().iloc[0]
        )

        local_df = pd.read_sql_query(
            text(
                """
                SELECT *
                FROM local_indicators_tutors
                WHERE institution_id = :institution_id
                AND subject_id = :subject_id
                AND version = :version
                """
            ),
            engine,
            params={
                "institution_id": institution_id,
                "subject_id": subject_id,
                "version": version,
            },
        )

        if local_df.empty:
            return

        placeholder = pd.DataFrame(
            [
                {
                    "institution_id": institution_id,
                    "version": version,
                    "subject_id": subject_id,
                    "score_global_forum": np.nan,
                    "label_global_forum": pd.NA,
                    "score_global_access": np.nan,
                    "label_global_access": pd.NA,
                    "score_global_feedback": np.nan,
                    "label_global_feedback": pd.NA,
                }
            ]
        )

        records = self._df_to_records(placeholder)
        self._upsert_dynamic(
            engine,
            "global_indicators_tutors",
            records,
            ["institution_id", "version", "subject_id"],
        )

    def _minmax(
        self, series, low_q: float = 0.05, high_q: float = 0.95, invert: bool = False
    ):
        """
        Normalização (percentis), evitando distorção por outliers.
        Retorna valores em [0,1]. NaN permanece NaN.
        """
        s = pd.to_numeric(series, errors="coerce")
        out = pd.Series(np.nan, index=s.index, dtype="float64")

        valid = s.dropna()
        if valid.empty:
            return out

        lo = valid.quantile(low_q)
        hi = valid.quantile(high_q)

        if pd.isna(lo) or pd.isna(hi) or hi <= lo:
            out.loc[s.notna()] = 0.5
            return out

        clipped = s.clip(lower=lo, upper=hi)
        norm = (clipped - lo) / (hi - lo)

        if invert:
            norm = 1 - norm

        out.loc[norm.index] = norm
        return out

    def _discretize_rank_5bins(self, values):
        s = pd.to_numeric(values, errors="coerce")
        out = pd.Series(pd.NA, index=s.index, dtype="object")

        valid = s.dropna()
        if valid.empty:
            return out

        if valid.nunique() == 1:
            out.loc[valid.index] = "Médio"
            return out

        pct = valid.rank(method="average", pct=True)

        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        labels = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]

        out.loc[valid.index] = pd.cut(
            pct, bins=bins, labels=labels, include_lowest=True
        ).astype(str)

        return out

    def discretize_global_indicators_tutors(self, institution_id: int = 1):
        """
        1) Lê local_indicators_tutors da instituição/version
        2) Padroniza métricas em escala comum (0..1) com referência institucional
        3) Inverte métricas onde menor é melhor
        4) Calcula MÉDIA SIMPLES por dimensão (fórum, acesso, feedback) para cada tutor
        5) Calcula MÉDIA dos tutores por disciplina
        6) Discretiza as disciplinas em 5 faixas (rank percentílico)
        """
        engine = self.engine
        version = str(self.db_admin.get_version_in_database(institution_id, engine=engine))

        try:
            local_df = pd.read_sql_table("local_indicators_tutors", engine)
        except Exception as e:
            print("[WARN] failed reading local_indicators_tutors:", e)
            return

        if local_df is None or local_df.empty:
            return

        local_df["version"] = local_df["version"].astype(str)

        mask = (
            pd.to_numeric(local_df["institution_id"], errors="coerce") == institution_id
        ) & (local_df["version"] == version)
        df = local_df.loc[mask].copy()

        if df.empty:
            return

        for c in ["institution_id", "version", "subject_id", "tutor_id"]:
            if c not in df.columns:
                print(f"[WARN] coluna ausente em local_indicators_tutors: {c}")
                return

        expected_numeric = [
            # Fórum
            "total_response_forum",
            "mean_forums_response_hours",
            "median_forums_response_hours",
            # Acesso
            "n_login",
            "n_login_subject",
            "maximum_inactivity_days",
            # Feedback
            "n_corrections",
            "n_corrections_with_feedback",
            "percentage_feedback",
            "n_textual_feedback",
            "n_feedback_pdf",
        ]
        for c in expected_numeric:
            if c not in df.columns:
                df[c] = np.nan
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # Fórum
        df["total_response_forum"] = df["total_response_forum"].fillna(0.0)

        has_forum_response = df["total_response_forum"] > 0

        df["response_norm_inst"] = self._minmax(
            df["total_response_forum"], invert=False
        )
        df["mean_resp_time_norm_inst"] = self._minmax(
            df["mean_forums_response_hours"], invert=True
        )
        df["median_resp_time_norm_inst"] = self._minmax(
            df["median_forums_response_hours"], invert=True
        )

        df.loc[~has_forum_response, "mean_resp_time_norm_inst"] = 0.0
        df.loc[~has_forum_response, "median_resp_time_norm_inst"] = 0.0

        df["response_norm_inst"] = df["response_norm_inst"].fillna(0.0)

        df["score_forum_tutor_inst"] = df[
            [
                "response_norm_inst",
                "mean_resp_time_norm_inst",
                "median_resp_time_norm_inst",
            ]
        ].mean(axis=1, skipna=True)

        # Acesso
        df["n_login"] = df["n_login"].fillna(0.0)
        df["n_login_subject"] = df["n_login_subject"].fillna(0.0)

        df["n_login_norm_inst"] = self._minmax(df["n_login"], invert=False).fillna(0.0)
        df["n_login_subject_norm_inst"] = self._minmax(
            df["n_login_subject"], invert=False
        ).fillna(0.0)
        df["maximum_inactivity_days_norm_inst"] = self._minmax(
            df["maximum_inactivity_days"], invert=True
        )

        df["score_access_tutor_inst"] = df[
            [
                "n_login_norm_inst",
                "n_login_subject_norm_inst",
                "maximum_inactivity_days_norm_inst",
            ]
        ].mean(axis=1, skipna=True)

        for c in [
            "n_corrections",
            "n_corrections_with_feedback",
            "n_textual_feedback",
            "n_feedback_pdf",
        ]:
            df[c] = df[c].fillna(0.0)

        # Feedback
        df["percentage_feedback"] = pd.to_numeric(
            df["percentage_feedback"], errors="coerce"
        )
        if df["percentage_feedback"].dropna().gt(1).any():
            df["percentage_feedback"] = df["percentage_feedback"] / 100.0
        df["percentage_feedback"] = df["percentage_feedback"].clip(lower=0, upper=1)

        df["n_corrections_norm_inst"] = self._minmax(
            df["n_corrections"], invert=False
        ).fillna(0.0)
        df["n_corrections_with_feedback_norm_inst"] = self._minmax(
            df["n_corrections_with_feedback"], invert=False
        ).fillna(0.0)
        df["n_textual_feedback_norm_inst"] = self._minmax(
            df["n_textual_feedback"], invert=False
        ).fillna(0.0)
        df["n_feedback_pdf_norm_inst"] = self._minmax(
            df["n_feedback_pdf"], invert=False
        ).fillna(0.0)

        df["percentage_feedback_norm_inst"] = df["percentage_feedback"]

        df["score_feedback_tutor_inst"] = df[
            [
                "n_corrections_norm_inst",
                "n_corrections_with_feedback_norm_inst",
                "percentage_feedback_norm_inst",
                "n_textual_feedback_norm_inst",
                "n_feedback_pdf_norm_inst",
            ]
        ].mean(axis=1, skipna=True)

        df["institution_id"] = pd.to_numeric(
            df["institution_id"], errors="coerce"
        ).astype("Int64")
        df["subject_id"] = pd.to_numeric(df["subject_id"], errors="coerce").astype(
            "Int64"
        )
        df["version"] = df["version"].astype(str)

        df = df.dropna(subset=["institution_id", "subject_id"])
        if df.empty:
            return

        # Mediana dos tutores da disciplina
        subject_scores = df.groupby(
            ["institution_id", "version", "subject_id"], as_index=False
        ).agg(
            score_global_forum=("score_forum_tutor_inst", "median"),
            score_global_access=("score_access_tutor_inst", "median"),
            score_global_feedback=("score_feedback_tutor_inst", "median"),
        )

        if subject_scores.empty:
            return

        # discretização global
        subject_scores["label_global_forum"] = self._discretize_rank_5bins(
            subject_scores["score_global_forum"]
        )
        subject_scores["label_global_access"] = self._discretize_rank_5bins(
            subject_scores["score_global_access"]
        )
        subject_scores["label_global_feedback"] = self._discretize_rank_5bins(
            subject_scores["score_global_feedback"]
        )

        subject_scores["institution_id"] = subject_scores["institution_id"].astype(int)
        subject_scores["subject_id"] = subject_scores["subject_id"].astype(int)
        subject_scores["version"] = subject_scores["version"].astype(str)

        subject_scores = subject_scores.sort_values(
            ["institution_id", "version", "subject_id"]
        ).reset_index(drop=True)

        subject_scores = subject_scores[
            [
                "institution_id",
                "version",
                "subject_id",
                "score_global_forum",
                "label_global_forum",
                "score_global_access",
                "label_global_access",
                "score_global_feedback",
                "label_global_feedback",
            ]
        ]

        records = self._df_to_records(subject_scores)
        self._upsert_dynamic(
            engine,
            "global_indicators_tutors",
            records,
            ["institution_id", "version", "subject_id"],
        )

    def safe_df(
        self, label, fn, *args, connector=None, retries=0, sleep_s=0.3, **kwargs
    ):
        MYSQL_RETRYABLE = {1205, 1213, 1317, 3024}
        # 1205 lock wait timeout
        # 1213 deadlock
        # 1317 query interrupted
        # 3024 max_execution_time exceeded (varia por engine)

        for attempt in range(retries + 1):
            try:
                df = fn(*args, **kwargs)
                if df is None or (hasattr(df, "empty") and df.empty):
                    # print(f"[WARN] {label}: empty/None")
                    return None
                return df

            except Exception as e:
                code = None
                try:
                    if getattr(e, "args", None):
                        code = e.args[0]
                except Exception:
                    pass

                # print(f"[ERROR] {label} attempt={attempt} code={code} err={e}")
                traceback.print_exc()

                if connector is not None:
                    try:
                        connector.rollback()
                    except Exception:
                        pass
                    try:
                        connector.ping(reconnect=True)
                    except Exception:
                        pass

                if attempt < retries and code in MYSQL_RETRYABLE:
                    time.sleep(sleep_s)
                    continue

                return None


def continuously_listen():
    rabbit_admin = RabbitMQAdmin()

    def callback(ch, method, properties, body):
        worker = Worker(rabbit_admin)
        try:
            message = json.loads(body.decode())
            analysis_type = message.get("body", {}).get("type")

            if analysis_type == "subject_analysis":
                worker.subject_analysis(message)
            elif analysis_type in (...):
                worker.global_analysis(message)
            else:
                print(f"[!] Tipo de análise desconhecido: {analysis_type}")

        except Exception as e:
            print("[FATAL in callback]:", e)
            import traceback

            traceback.print_exc()

        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

            # se quiser manter sua lógica de discretização aqui, ok:
            try:
                state = ch.queue_declare(queue="tasks_to_process", passive=True)
                if state.method.message_count == 0:
                    worker.discretize_global_indicators(1)
                    worker.discretize_global_indicators_tutors(1)
            except Exception as e:
                print("[WARN] post-process failed:", e)

    rabbit_admin.channel.basic_qos(prefetch_count=1)
    rabbit_admin.channel.basic_consume(
        queue="tasks_to_process", on_message_callback=callback
    )

    print(" [*] Aguardando mensagens. Para sair pressione CTRL+C")
    while True:
        try:
            rabbit_admin.channel.start_consuming()
        except Exception as e:
            print("[consume loop error]:", e)
            time.sleep(2)


if __name__ == "__main__":
    print("Worker iniciado. Aguardando mensagens...")
    try:
        continuously_listen()
    finally:
        DatabaseAdmin.dispose_connector()
