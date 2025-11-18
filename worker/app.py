from database import Database, DatabaseAdmin
from rabbit import RabbitMQAdmin
from src.analysis_lib.analysis.analysis import Analyzer
import json
import pandas as pd

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
    
    def select_indicator_analysis(self, analysis_type, connector, version, analysis_config):
        if analysis_type == "global_analysis_performance":
            return self.analyzer.general_performance_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_engagement":
            return self.analyzer.general_engagement_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_motivation":
            return self.analyzer.general_motivation_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_pedagogic":
            return self.analyzer.general_pedagogic_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_cognitive":
            return self.analyzer.general_cognitive_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_give_up":
            return self.analyzer.general_give_up_analysis(connector, version, analysis_config)
        else:
            raise ValueError(f"Tipo de análise desconhecido: {analysis_type}")

    def global_analysis(self, message):
        body = message["body"]
        analysis_type = body["type"]
        version = self.db_admin.get_version_in_database(1)
        message["version"] = version
        connector = conn.get_connection_with_config(body.get("db_inst_config"))

        if analysis_type not in ANALYSIS_MAP:
            raise ValueError(f"Tipo de análise desconhecido: {analysis_type}")

        config = body.get("db_inst_config") or body.get("db_config")
        entry = ANALYSIS_MAP[analysis_type]

        res = self.select_indicator_analysis(analysis_type, connector, version, body.get("analysis_config", {}))
        
        if res["processed"] != res["total"]:
            self.rabbit_admin.publish_message("tasks_to_process", {
                "name": f"user:{analysis_type}",
                "body": {
                    "type": analysis_type,
                    "db_inst_config": config,
                    "analysis_config": res
                },
                "version": version
            }, priority=0)
        else:
            self.db_admin.update_global_analysis_status(1, entry["status_index"], 'D')

    def subject_analysis(self, message):
        body = message["body"]
        cfg = body.get("analysis_config", {})
        subject_id = int(cfg["subject_id"])
        version = self.db_admin.get_version_in_database(1)
        connector = conn.get_connection_with_config(body.get("db_inst_config"))
        engine = self.db_admin.get_connector()

        eng = self.analyzer.engagement_analysis(subject_id, 'course', version, connector)
        per = self.analyzer.performance_analysis(subject_id, 'course', version, connector)
        mot = self.analyzer.motivation_analysis(subject_id, 'course', version, connector)
        cog = self.analyzer.cognitive_analysis(subject_id, 'course', version, connector)
        giv = self.analyzer.give_up_analysis(subject_id, 'course', version, connector)

        indicator_dfs = {"eng": eng, "per": per, "mot": mot, "cog": cog, "giv": giv}
        normalized = []

        for name, df in indicator_dfs.items():
            if df is None or df.empty:
                continue

            df = df.copy()
            normalized.append(df)

        if not normalized:
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
            "label": "label_give_up",
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
            "mean_responses_relation_teacher_student",
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
                "mean_responses_relation_teacher_student": "first",
                "label_relation_teacher_student": "first",
                "label_give_up": "first",
            }
        )

        subject_df.to_sql("local_indicators", engine, if_exists="append", index=False)

        self.db_admin.update_subject_analysis_status(1, subject_id, "D")

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
