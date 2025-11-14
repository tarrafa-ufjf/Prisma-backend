from database import Database, DatabaseAdmin
from rabbit import RabbitMQAdmin
from src.analysis_lib.analysis.analysis import Analyzer
import json
import pandas as pd

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
            # ped = self.analyzer.pedagogic_analysis(subject_id, 'course', version, connector)
            giv = self.analyzer.give_up_analysis(subject_id, 'course', version, connector)

            # Executa todos os indicadores no escopo "course" (turma)
            # Merge all indicator DataFrames on subject_id and student_id (outer join to keep all students)
            dfs = [eng, per, mot, cog, giv]
            merged = None
            for df in dfs:
                if df is None or df.empty:
                    continue
                # Verificar se o dataframe tem as colunas necessárias para merge
                if 'subject_id' not in df.columns or 'user_id' not in df.columns:
                    print(f"[!] Aviso: DataFrame sem 'subject_id' ou 'user_id'. Colunas: {df.columns.tolist()}")
                    continue
                if merged is None:
                    merged = df.copy()
                else:
                    # Detectar colunas comuns (exceto as chaves de merge)
                    merge_keys = ['subject_id', 'user_id']
                    common_cols = [col for col in merged.columns if col in df.columns and col not in merge_keys]
                    if common_cols:
                        # Se há colunas em comum além das chaves, usar sufixos
                        merged = merged.merge(df, on=merge_keys, how='outer', suffixes=('', '_new'))
                    else:
                        # Se não há colunas em comum, fazer merge simples
                        merged = merged.merge(df, on=merge_keys, how='outer')

            # If nothing to merge, create empty frame with keys
            if merged is None:
                merged = pd.DataFrame(columns=['subject_id', 'user_id'])

            # Ensure version column
            merged['version'] = version

            # Desired final columns
            desired_cols = [
                'version',
                'subject_id',
                'student_id',
                'n_posts_engagement',
                'label_engagement',
                'n_posts_motivation',
                'label_motivation',
                'grade_performance',
                'grade_comparative_performance',
                'label_performance',
                'mean_forum_interactions_cognitive',
                'mean_quiz_interactions_cognitive',
                'mean_assign_interactions_cognitive',
                'label_cognitive',
                'n_responses_relation_teacher_student',
                'mean_responses_relation_teacher_student',
                'label_relation_teacher_student',
                'label_give_up'
            ]

            # Add missing columns as NA and select only desired columns
            for c in desired_cols:
                if c not in merged.columns:
                    merged[c] = pd.NA
            subject_df = merged[desired_cols]
            
            # Fill empty values with zero
            subject_df = subject_df.fillna(0)

            subject_df['institution_id'] = 1
            subject_df['subject_id'] = subject_id

            # Agrupar por subject_id e student_id para evitar duplicatas
            # Manter apenas a primeira ocorrência de cada combinação

            subject_df = subject_df.rename(columns={'user_id': 'student_id'})

            subject_df = subject_df.groupby(['subject_id', 'student_id'], as_index=False).agg({
                'version': 'first',
                'institution_id': 'first',
                'n_posts_engagement': 'first',
                'label_engagement': 'first',
                'n_posts_motivation': 'first',
                'label_motivation': 'first',
                'grade_performance': 'first',
                'grade_comparative_performance': 'first',
                'label_performance': 'first',
                'mean_forum_interactions_cognitive': 'first',
                'mean_quiz_interactions_cognitive': 'first',
                'mean_assign_interactions_cognitive': 'first',
                'label_cognitive': 'first',
                'n_responses_relation_teacher_student': 'first',
                'mean_responses_relation_teacher_student': 'first',
                'label_relation_teacher_student': 'first',
                'label_give_up': 'first'
            })

            subject_df.to_sql(
                'local_indicators',
                engine,
                if_exists='append',
                index=False
            )
            # Opcional: agregações percentuais/indicadores consolidados por turma
            # self.analyzer.indicators_analysis(subject_id, 'subject', version, connector)

            # Marca como concluído
            self.db_admin.update_subject_analysis_status(1, subject_id, 'D')

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
