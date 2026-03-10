from typing import Any, Dict
import pandas as pd
from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analyzer import Analyzer  

def build_tutors_subject_feedback(subject_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)

    try:
        version = analyzer.get_moodle_version(connector)
        df = analyzer.feedback_analysis(subject_id, 'subject', 'subject', version, connector)
        
        if df is None or df.empty:
            return []

        missing = [c for c in ["tutor_id", "full_name", "n_corrections","n_corrections_with_feedback","percentage_feedback","n_textual_feedback","n_feedback_pdf",
                            "n_corrections_label", "n_corrections_with_feedback_label", "percentage_feedback_label",
                            "n_textual_feedback_label", "n_feedback_pdf_label", "label_feedback"] if c not in df.columns]
        if missing:
            raise KeyError(f"missing columns in engagement_analysis output: {missing}")


        out = df.loc[:, ["tutor_id","full_name", "n_corrections","n_corrections_with_feedback","percentage_feedback","n_textual_feedback","n_feedback_pdf",
                            "n_corrections_label", "n_corrections_with_feedback_label", "percentage_feedback_label",
                            "n_textual_feedback_label", "n_feedback_pdf_label", "label_feedback"]].copy()
        
        out = out.fillna(0)
        
        return out.to_dict(orient="records")
    
    finally:
        try:
            connector.close()
        except Exception:
            pass