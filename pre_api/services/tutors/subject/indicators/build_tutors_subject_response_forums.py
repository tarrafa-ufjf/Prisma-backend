from typing import Any, Dict
import pandas as pd

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analyzer import Analyzer  

def build_tutors_subject_response_forums(subject_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)

    try:
        version = analyzer.get_moodle_version(connector)
        df = analyzer.response_foruns_analysis(subject_id, 'subject', 'subject', version, connector)
        
        if df is None or df.empty:
            return []

        missing = [c for c in ["tutor_id", "full_name", "total_response_forum", "median_forums_response_hours", "mean_forums_response_hours", "score_access",
                            "mean_forums_response_hours_label", "median_forums_response_hours_label", "score_access_label",
                            "label_forums_response",
                            "num_response_fast_forum", "num_response_late_forum", "num_response_normal_forum"] if c not in df.columns]
        if missing:
            raise KeyError(f"missing columns in engagement_analysis output: {missing}")
        
        out = df.loc[:, ["tutor_id", "full_name", "total_response_forum", "median_forums_response_hours", "mean_forums_response_hours", "score_access",
                            "mean_forums_response_hours_label", "median_forums_response_hours_label", "score_access_label",
                            "label_forums_response",
                            "num_response_fast_forum", "num_response_late_forum", "num_response_normal_forum"]].copy()
        
        out = out.where(pd.notna(out), None)

        return out.to_dict(orient="records")
    
    finally:
        try:
            connector.close()
        except Exception:
            pass