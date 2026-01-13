from typing import Any, Dict

from database import DatabaseAdmin, Database  
from src.analysis_lib.analysis.analysis import Analyzer  

def build_general_rankings(kind: str = "best-performance", limit: int = 10):
    db_admin = DatabaseAdmin()
    analyzer = Analyzer()

    db_config = db_admin.get_db_config_from_database(1)
    connector = db_admin.get_connection_with_config(db_config)
    try:
        version = analyzer.get_moodle_version(connector)
        data = analyzer.rankings_general_analysis(version=version, connector=connector, kind=kind, limit=limit)
        return data
    finally:
        try:
            connector.close()
        except Exception:
            pass