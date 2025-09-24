from flask_sqlalchemy import SQLAlchemy
import os
import pymysql
from sqlalchemy import and_, select, create_engine, MetaData, Table, Column, Integer, String, DECIMAL
from sqlalchemy.dialects.postgresql import insert as pg_insert
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        pass

    def get_connection(self):
        return pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_GRAD_PORT')),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            db=os.getenv('MYSQL_DATABASE'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def get_systems_local_database_connection(self):
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_DATABASE")

        engine = create_engine(
            f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

        return engine
    
    def get_connection_with_config(self, config):
        return pymysql.connect(
            host = config['host'],
            port = config['port'],
            user = config['user'],
            password = config['password'],
            db = config['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

class DatabaseAdmin:
    @staticmethod
    def get_connector():
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", 5432))
        DB_NAME = os.getenv("DB_DATABASE")

        engine = create_engine(
            f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        return engine

    def get_global_analysis_table(self):
        metadata = MetaData()
        global_analysis = Table(
            'gl_indicators_status', metadata,
            Column('s_user', Integer, primary_key=True),
            Column('indicator', Integer, primary_key=True),
            Column('status', String(1), nullable=False)
        )
        return global_analysis
    
    def update_global_analysis_status(self, s_user: int, indicator: int, status: str):
        engine = self.get_connector()
        table = self.get_global_analysis_table()

        stmt = pg_insert(table).values(
            s_user=s_user,
            indicator=indicator,
            status=status
        ).on_conflict_do_update(
            constraint="gl_indicators_status_pkey",
            set_={"status": status}
        )

        with engine.begin() as conn:
            conn.execute(stmt)
    
    def get_all_from_table(self, table_name, user_id=1):
        engine = self.get_connector()
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = select(table).where(table.c.s_user == user_id)  # TODO
            return conn.execute(query).mappings().all()
    
    def get_version_in_database(self, user):
        engine = self.get_connector()
        metadata = MetaData()
        configs = Table("configs", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = select(configs).where(configs.c.s_user == user)
            result = conn.execute(query).mappings().all()  # retorna lista de dicts
            if len(result) > 0:
                return result[0]['version']
            else:
                return None
    
    def verify_if_there_is_version_in_database(self, user):
        engine = self.get_connector()
        metadata = MetaData()
        configs = Table("configs", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = select(configs).where(configs.c.s_user == user)
            result = conn.execute(query).mappings().all()  # retorna lista de dicts
            if len(result) > 0:
                return True
            return False
    
    def insert_version_in_database(self, user, version, db_config):
        engine = self.get_connector()
        metadata = MetaData()
        configs = Table("configs", metadata, autoload_with=engine)

        with engine.connect() as conn:
            insert_stmt = configs.insert().values(
                s_user=user,
                version=version,
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['db'],
                user=db_config['user'],
                password=db_config['password']
            )
            conn.execute(insert_stmt)
            conn.commit()
    
    def global_analysis_status(self, indicator, user_id=1):
        db_config = self.get_db_config_from_database()
        engine = create_engine(
            f"postgresql+psycopg://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db']}"
        )
        metadata = MetaData()
        global_analysis = Table('gl_indicators_status', metadata, autoload_with=engine)
        with engine.connect() as conn:
            query = global_analysis.select().where(and_(global_analysis.c.s_user == user_id,
                                                        global_analysis.c.indicator == indicator))
            result = conn.execute(query).mappings().all()
            return {row['indicator']: row['status'] for row in result}
    
    def insert_global_analysis_status(self, s_user: int, indicator: int, status: str):
        engine = self.get_connector()
        table = self.get_global_analysis_table()

        stmt = pg_insert(table).values(
            s_user=s_user,
            indicator=indicator,
            status=status
        ).on_conflict_do_update(
            constraint="gl_indicators_status_pkey",
            set_={"status": status}
        )

        with engine.begin() as conn:
            conn.execute(stmt)

db = SQLAlchemy()