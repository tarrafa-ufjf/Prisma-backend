from typing import Any, Dict

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analysis import Analyzer  

def build_subject_students_motivation(subject_id: int):
    processor_db = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = processor_db.get_db_config_from_database(1)
    connector = processor_db.get_connection_with_config(db_config)

    try:
        version = analyzer.get_moodle_version(connector)
        df = analyzer.motivation_analysis(subject_id, 'course', version, connector)

        if df is None or df.empty:
            return []

        missing = [c for c in ["full_name", "posts_unrequired_label", "num_posts_unrequired"] if c not in df.columns]
        if missing:
            raise KeyError(f"missing columns in motivation_analysis output: {missing}")

        out = df.loc[:, ["full_name", "posts_unrequired_label", "num_posts_unrequired"]].copy()
        out["full_name"] = out["full_name"].astype(str)
        out["posts_unrequired_label"] = out["posts_unrequired_label"].fillna("").astype(str)

        if "num_posts_unrequired" in out:
            out["num_posts_unrequired"] = out["num_posts_unrequired"].fillna(0).astype(int)

        return out.to_dict(orient="records")
    
    finally:
        try:
            connector.close()
        except Exception:
            pass