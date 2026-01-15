from typing import Any, Dict

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analyzer import Analyzer  

def build_tutors_subject_access(subject_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)

    try:
        version = analyzer.get_moodle_version(connector)
        df = analyzer.access_analysis(subject_id, 'subject', version, connector)
        
        if df is None:
            return []

        missing = [c for c in ["tutor_id", "full_name", "n_login", "label_access",
                                "mean_weekly_course_views_window"] if c not in df.columns]
        if missing:
            raise KeyError(f"missing columns in engagement_analysis output: {missing}")


        out = df.loc[:, ["tutor_id", "full_name", "n_login", "label_access", 
                                "mean_weekly_course_views_window"]].copy()

        return out.to_dict(orient="records")
    
    finally:
        try:
            connector.close()
        except Exception:
            pass