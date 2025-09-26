from sqlalchemy import Table, Column, Integer, MetaData, String, create_engine
import os, sys
from dotenv import load_dotenv

class Indicator:
    def __init__(self, mapper):
        self.mapper = mapper
        load_dotenv()
    
    def get_connector(self):
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", 5432))
        DB_NAME = os.getenv("DB_DATABASE")

        engine = create_engine(
            f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        return engine
    
    def insert_global_analysis_status(self, s_user: int, course_id: int, indicator: int, status: str):
        engine = self.get_connector()
        global_analysis = self.get_global_analysis_table()

        with engine.connect() as conn:
            insert_stmt = global_analysis.insert().values(
                s_user=s_user,
                course_id=course_id,
                indicator=indicator,
                status=status
            )
            conn.execute(insert_stmt)
            conn.commit()
    
    def get_global_analysis_table(self):
        metadata = MetaData()
        global_analysis = Table(
            'gl_indicators_status', metadata,
            Column('s_user', Integer, primary_key=True),
            Column('course_id', Integer, primary_key=True),
            Column('indicator', Integer, primary_key=True),
            Column('status', String(1), nullable=False)
        )
        return global_analysis
    
    def print_load(self, name, processed, total, line):
        percent = (processed / total) * 100
        bar_length = 20
        filled = "#" * (bar_length * processed // total)
        empty = "-" * (bar_length - len(filled))

        line = line + 10
        
        # \033[{row};0H move o cursor para a linha "row"
        sys.stdout.write(f"\033[{line};0H Análise Global {name}|{filled}{empty}| {percent:.2f}%")
        sys.stdout.flush()

        if processed == total:
            print(' ✅\n')