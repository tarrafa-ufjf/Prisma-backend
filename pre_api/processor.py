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
    
        # for sid in subjects[:200]:
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
