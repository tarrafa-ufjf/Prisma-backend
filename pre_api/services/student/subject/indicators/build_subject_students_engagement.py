from typing import Any, Dict

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analyzer import Analyzer  

def build_subject_students_engagement(subject_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)

    try:
        version = analyzer.get_moodle_version(connector)
        df = analyzer.engagement_analysis(subject_id, 'subject', version, connector)
        
        if df is None or df.empty:
            return []

        missing = [c for c in ["user_id", "full_name", "posts_required_label", "num_posts_required"] if c not in df.columns]
        if missing:
            raise KeyError(f"missing columns in engagement_analysis output: {missing}")


        out = df.loc[:, ["user_id", "full_name", "posts_required_label", "num_posts_required"]].copy()
        out["full_name"] = out["full_name"].astype(str)
        out["posts_required_label"] = out["posts_required_label"].fillna("").astype(str)

        if "num_posts_required" in out:
            out["num_posts_required"] = out["num_posts_required"].fillna(0).astype(int)

        return out.to_dict(orient="records")
    
    finally:
        try:
            connector.close()
        except Exception:
            pass