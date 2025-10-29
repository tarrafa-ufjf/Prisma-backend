from typing import Any, Dict

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analysis import Analyzer  

def build_subject_student_give_up(subject_id: int, student_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)
    try:
        version = analyzer.get_moodle_version(connector)
        data = analyzer.give_up_analysis(subject_id, 'user', version, connector, student_id)
        return data
    finally:
        try:
            connector.close()
        except Exception:
            pass