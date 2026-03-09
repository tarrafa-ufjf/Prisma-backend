from typing import Any, Dict

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analyzer import Analyzer  

def build_subject_students_cognitive(subject_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)

    try:
        version = analyzer.get_moodle_version(connector)
        df = analyzer.cognitive_analysis(subject_id, 'subject', version, connector)
        
        if df is None or df.empty:
            return []
        
        missing = [c for c in ["user_id", "full_name", "label", "forum_mean_level", "quiz_mean_level", "assign_mean_level"] if c not in df.columns]
        if missing:
            raise KeyError(f"missing columns in cognitive_analysis output: {missing}")


        out = df.loc[:, ["user_id", "full_name", "label", "forum_mean_level", "quiz_mean_level", "assign_mean_level"]].copy()
        out["full_name"] = out["full_name"].astype(str)

        return out.to_dict(orient="records")
    
    finally:
        try:
            connector.close()
        except Exception:
            pass