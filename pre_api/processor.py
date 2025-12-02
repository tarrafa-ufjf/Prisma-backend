import json, time
import pandas as pd
from rabbit import RabbitMQAdmin
from sqlalchemy import and_, select
from database import DatabaseAdmin, Database
from src.analysis_lib.analysis.analysis import Analyzer

class Processor:
    def __init__(self, user=None):
        self.rabbit_admin = RabbitMQAdmin()
        self.db_admin = DatabaseAdmin()
        self.user = user
        self.db_config = None
        self.analysis = Analyzer()
        self.connector_inst = Database()

    _ANALYSIS_MAP = {
        "performance": ("general_performance_analysis", "performance_analysis"),
        "engagement": ("general_engagement_analysis", "engagement_analysis"),
        "motivation": ("general_motivation_analysis", "motivation_analysis"),
        "pedagogic": ("general_pedagogic_analysis", "pedagogic_analysis"),
        "cognitive": ("general_cognitive_analysis", "cognitive_analysis"),
        "give_up": ("general_give_up_analysis", "give_up_analysis"),
    }

    def get_done_message(self, name):
        global channel
        found = False
        res = None
        while not found:
            time.sleep(0.25)
            method_frame, _, body = self.rabbit_admin.channel.basic_get(queue="Done", auto_ack=False)
            if method_frame:
                message = json.loads(body.decode())
                nome = message.get("name") 
                if nome == name:
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    found = True
                    res = message.get("body")
                else:
                    channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                    time.sleep(0.1)
            else:
                time.sleep(0.25)
        return res

    # def wait_until_done(self, institution_id, indicator, status, poll_interval=2):
    #     engine = self.db_admin.get_connector()
    #     global_analysis = self.db_admin.get_global_analysis_table()

    #     while True:
    #         with engine.connect() as conn:
    #             query = select(global_analysis.c.status).where(
    #                 and_(
    #                     global_analysis.c.institution_id == institution_id,
    #                     global_analysis.c.status == status,
    #                     global_analysis.c.indicator == indicator
    #                 )
    #             )
    #             result = conn.execute(query).fetchone()

    #             if result and result.status == "D":
    #                 return True

    #         time.sleep(poll_interval)  # espera antes de checar de novo

    def wait_subject_done(self, institution_id, subject_id, status='D', poll_interval=2):
        engine = self.db_admin.get_connector()
        table = self.db_admin.get_subjects_status_table()
        
        while True:
            with engine.connect() as conn:
                q = select(table.c.status).where(
                    and_(table.c.institution_id == institution_id,
                         table.c.subject_id == subject_id)
                )
                row = conn.execute(q).fetchone()
                if row and row.status == status:
                    return True
            time.sleep(poll_interval)

    def handle_analysis(self, analysis_type, global_fn, request, indicator_index=0):
        version = self.db_admin.get_version_in_database(1)
        subject_id = request.args.get("id", type=int)
        type_ = request.args.get("query")
        db_config = self.db_admin.get_db_config_from_database(1)

        if not subject_id and type_ != "general":
            return {"error": "Course ID is required"}, 400

        analysis_config = {"query": type_, "id": subject_id}
        if type_ != "general":
            name = f"user:{analysis_type}"
            task = {
                "name": name,
                "version": version,
                "body": {
                    "db_inst_config": db_config,
                    "analysis_config": analysis_config,
                    "type": analysis_type,
                },
            }
            body = self.select_indicator(analysis_type, task)
            return body, 200
        else:
            self.wait_until_done(1, indicator_index, "D")

            if global_fn == 'get_all_from_table':
                rows = self.db_admin.get_all_from_table(analysis_type, institution_id=1)
            elif global_fn == 'get_all_performance_global':
                rows = self.get_all_performance_global(institution_id=1)
            elif global_fn == 'get_all_engajamento_global':
                rows = self.get_all_engajamento_global(institution_id=1)
            elif global_fn == 'get_all_motivation_global':
                rows = self.get_all_motivation_global(institution_id=1)
            elif global_fn == 'get_all_pedagogic_global':
                rows = self.get_all_pedagogic_global(institution_id=1)
            elif global_fn == 'get_all_give_up_global':
                rows = self.get_all_give_up_global(institution_id=1)

            data = [dict(row) for row in rows]
            return data, 200
    
    def select_indicator(self, indicator, message):
        body = message.get("body")
        analysis_config = body.get("analysis_config")
        simple_indicator = indicator.split("_")[-1]

        if simple_indicator not in self._ANALYSIS_MAP:
            return {"error": "Invalid indicator"}, 400
        
        general_func_name, specific_func_name = self._ANALYSIS_MAP[simple_indicator]

        try:
            connector = self.db_admin.get_connection_with_config(body["db_inst_config"])
            version = message.get("version")
        except KeyError:
             return {"error": "Missing 'db_inst_config' in message body"}, 400

        if analysis_config.get("query") == 'general':
            analysis_func = getattr(self.analysis, general_func_name)
            response = analysis_func(connector, version, analysis_config)
        else:
            analysis_func = getattr(self.analysis, specific_func_name)
            analysis_id = analysis_config.get("id")
            analysis_type = analysis_config.get("query")
            response = analysis_func(analysis_id, analysis_type, version, connector)
        
        data = response.to_dict(orient='records')
        return data
    
    def get_all_engajamento_global(self, institution_id=1):
        return self.db_admin.get_all_from_table("engajamento_global", institution_id)

    def get_all_performance_global(self, institution_id=1):
        return self.db_admin.get_all_from_table("performance_global", institution_id)

    def get_all_motivation_global(self, institution_id=1):
        return self.db_admin.get_all_from_table("motivation_global", institution_id)

    def get_all_pedagogic_global(self, institution_id=1):
        return self.db_admin.get_all_from_table("pedagogic_global", institution_id)
    
    def get_all_give_up_global(self, institution_id=1):
        return self.db_admin.get_all_from_table("give_up_global", institution_id)
    
    # def set_global_analysis(self, indicators, db_config=None):
    #     counter = 1
    #     for indicator in indicators:
    #         task = {
    #             "name" : f"user:global_analysis_{indicator.lower()}",
    #             "body" : {
    #                 "db_inst_config" : db_config,
    #                 "type" : f"global_analysis_{indicator.lower()}",
    #                 "analysis_config" : {
    #                     "id" : None,
    #                     "type" : "general",
    #                     "batch_size" : 20,
    #                     "processed" : 0,
    #                     "total" : 0
    #                 }
    #             }
    #         }

    #         # try:
    #         self.db_admin.insert_global_analysis_status(1, counter, 'P')  # Indicador 1: Engagement, Status 'I' (Idle
    #         counter += 1
    #         self.rabbit_admin.publish_message("tasks_to_process", task, priority=1)
    #         # except Exception as e:
    #         #     print(f"Erro ao inserir status para {indicator}: {e}")

    def set_subjects_analysis(self, db_config=None, subject_ids=None, batch_size=1):
        connector = self.connector_inst.get_connection_with_config(db_config)
        version = self.get_version(institution_id=1, db_config=db_config)

        if subject_ids is None:
            subjects_dict = self.analysis.get_all_subjects(version, connector)
            subjects_df = pd.DataFrame(subjects_dict)
            subjects_df = subjects_df["subjects"].apply(pd.Series)

            if "id" not in subjects_df.columns:
                raise ValueError("Coluna 'id' não encontrada em get_all_subjects().")

            subjects = (pd.to_numeric(subjects_df["id"], errors="coerce").dropna().astype(int).tolist())
        else:
            if isinstance(subject_ids, (list, tuple, set)):
                subjects = [int(x) for x in subject_ids]
            else:
                subjects = [int(subject_ids)]

        if not subjects:
            print("Nenhuma turma encontrada para enfileirar.")
            return
    
        # for sid in subjects:
        for sid in [37, 41, 78, 83, 84, 222, 223, 224]:
            try:
                self.db_admin.insert_subject_analysis_status(1, sid, 'P')
            except Exception as e:
                print(f"Falha ao inserir status de subject {sid}: {e}")

            task = {
                "name": f"user:subject_analysis:{sid}",
                "body": {
                    "type": "subject_analysis",
                    "db_inst_config": db_config,
                    "analysis_config": {
                        "subject_id": sid,
                        "batch_size": batch_size
                    }
                }
            }

            self.rabbit_admin.publish_message("tasks_to_process", task, priority=1)

    def get_version(self, institution_id=1, db_config=None):
        version = self.db_admin.get_version_in_database(institution_id)
        if version is None:
            connector = self.connector_inst.get_connection_with_config(db_config)
            version = self.analysis.get_moodle_version(connector)
        return version
