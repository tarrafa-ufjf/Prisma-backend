import json
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
import pymysql
from sqlalchemy import and_,create_engine, select, MetaData, Table, Column, Integer, String, Date, DateTime, DECIMAL, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from dotenv import load_dotenv

from src.analysis_lib.config_crypto import decrypt_config_secret, encrypt_config_secret

load_dotenv()

class Database:
    def __init__(self):
        pass

    def get_connection(self):
        return pymysql.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            db=os.getenv('DB_DATABASE'),
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
            db = config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

class DatabaseAdmin:
    _engine = None

    @classmethod
    def get_connector(cls):
        if cls._engine is None:
            database_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
            if database_uri:
                cls._engine = create_engine(database_uri)
                return cls._engine

            DB_USER = os.getenv("DB_USER")
            DB_PASSWORD = os.getenv("DB_PASSWORD")
            DB_HOST = os.getenv("DB_HOST", "localhost")
            DB_PORT = int(os.getenv("DB_PORT", 5432))
            DB_NAME = os.getenv("DB_DATABASE")
            cls._engine = create_engine(
                f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )

        return cls._engine

    @classmethod
    def dispose_connector(cls):
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None

    def get_global_analysis_table(self):
        metadata = MetaData()
        global_analysis = Table(
            'indicators_status', metadata,
            Column('institution_id', Integer, primary_key=True),
            Column('indicator', Integer, primary_key=True),
            Column('status', String(1), nullable=False)
        )
        return global_analysis
    
    def get_configs_table(self):
        metadata = MetaData()
        configs = Table(
            'configs', metadata,
            Column('institution_id', Integer, primary_key=True),
            Column('version', String(50), nullable=False),
            Column('host', String(100), nullable=False),
            Column('port', Integer, nullable=False),
            Column('database', String(100), nullable=False),
            Column('user', String(100), nullable=False),
            Column('password', String(512), nullable=False)
        )
        return configs

    def get_scheduler_status_table(self):
        metadata = MetaData()
        table = Table(
            "scheduler_status",
            metadata,
            Column("job_id", String(100), primary_key=True),
            Column("channel", String(50), nullable=False),
            Column("process_id", Integer, nullable=True),
            Column("next_run_at", DateTime(timezone=True), nullable=True),
            Column("heartbeat_at", DateTime(timezone=True), nullable=True),
            Column("last_started_at", DateTime(timezone=True), nullable=True),
            Column("last_finished_at", DateTime(timezone=True), nullable=True),
            Column("last_status", String(20), nullable=True),
            Column("last_error", String(1000), nullable=True),
            Column("updated_at", DateTime(timezone=True), nullable=False),
        )
        return table

    def upsert_scheduler_status(
        self,
        job_id: str,
        channel: str,
        process_id: int = None,
        next_run_at=None,
        heartbeat_at=None,
        last_started_at=None,
        last_finished_at=None,
        last_status: str = None,
        last_error: str = None,
        engine=None,
    ):
        engine = engine or self.get_connector()
        table = self.get_scheduler_status_table()
        values = {
            "channel": channel,
            "process_id": process_id,
            "next_run_at": next_run_at,
            "heartbeat_at": heartbeat_at,
            "last_started_at": last_started_at,
            "last_finished_at": last_finished_at,
            "last_status": last_status,
            "last_error": last_error,
            "updated_at": func.now(),
        }
        clean_values = {key: value for key, value in values.items() if value is not None}

        with engine.begin() as conn:
            existing = conn.execute(
                select(table.c.job_id).where(table.c.job_id == job_id)
            ).first()
            if existing:
                conn.execute(
                    table.update()
                    .where(table.c.job_id == job_id)
                    .values(**clean_values)
                )
            else:
                conn.execute(table.insert().values(job_id=job_id, **clean_values))

    def get_scheduler_status_rows(self, engine=None):
        engine = engine or self.get_connector()
        table = self.get_scheduler_status_table()
        with engine.connect() as conn:
            return conn.execute(select(table).order_by(table.c.job_id)).mappings().all()
    
    def update_global_analysis_status(self, institution_id: int, indicator: int, status: str, engine=None):
        engine = engine or self.get_connector()
        table = self.get_global_analysis_table()

        stmt = pg_insert(table).values(
            institution_id=institution_id,
            indicator=indicator,
            status=status
        ).on_conflict_do_update(
            constraint="indicators_status_pkey",
            set_={"status": status}
        )

        with engine.begin() as conn:
            conn.execute(stmt)
    
    def get_all_from_table(self, table_name, institution_id=1, engine=None):
        engine = engine or self.get_connector()
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = select(table).where(table.c.institution_id == institution_id)  # TODO
            return conn.execute(query).mappings().all()
    
    def get_version_in_database(self, user, engine=None):
        engine = engine or self.get_connector()
        metadata = MetaData()
        configs = Table("configs", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = select(configs).where(configs.c.institution_id == user)
            result = conn.execute(query).mappings().all()  # retorna lista de dicts
            if len(result) > 0:
                return result[0]['version']
            else:
                return None
    
    def verify_if_there_is_version_in_database(self, user, engine=None):
        engine = engine or self.get_connector()
        metadata = MetaData()
        configs = Table("configs", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = select(configs).where(configs.c.institution_id == user)
            result = conn.execute(query).mappings().all()  # retorna lista de dicts
            if len(result) > 0:
                return True
            return False
    
    def insert_version_in_database(self, user, version, db_config, engine=None):
        engine = engine or self.get_connector()
        metadata = MetaData()
        configs = Table("configs", metadata, autoload_with=engine)

        values = {
            "institution_id": user,
            "version": version,
            "host": db_config['host'],
            "port": db_config['port'],
            "database": db_config['database'],
            "user": db_config['user'],
            "password": encrypt_config_secret(db_config['password']),
        }

        with engine.begin() as conn:
            self._ensure_config_password_column_size(conn)
            existing = conn.execute(
                select(configs.c.institution_id).where(configs.c.institution_id == user)
            ).first()

            if existing:
                conn.execute(
                    configs.update()
                    .where(configs.c.institution_id == user)
                    .values(**values)
                )
            else:
                conn.execute(configs.insert().values(**values))

    def _ensure_config_password_column_size(self, conn):
        if conn.dialect.name == "postgresql":
            conn.execute(text("ALTER TABLE configs ALTER COLUMN password TYPE VARCHAR(512)"))
    
    def global_analysis_status(self, indicator, institution_id=1, engine=None):
        engine = engine or self.get_connector()
        metadata = MetaData()
        global_analysis = Table('indicators_status', metadata, autoload_with=engine)
        with engine.connect() as conn:
            query = global_analysis.select().where(and_(global_analysis.c.institution_id == institution_id,
                                                        global_analysis.c.indicator == indicator))
            result = conn.execute(query).mappings().all()
            return {row['indicator']: row['status'] for row in result}
    
    def insert_global_analysis_status(self, institution_id: int, indicator: int, status: str, engine=None):
        engine = engine or self.get_connector()
        table = self.get_global_analysis_table()

        stmt = pg_insert(table).values(
            institution_id=institution_id,
            indicator=indicator,
            status=status
        ).on_conflict_do_update(
            constraint="indicators_status_pkey",
            set_={"status": status}
        )

        with engine.begin() as conn:
            conn.execute(stmt)
    
    def get_db_config_from_database(self, institution_id=1, engine=None):
        engine = engine or self.get_connector()
        configs = self.get_configs_table()

        query = (
            select(
                configs.c.host,
                configs.c.port,
                configs.c.database,
                configs.c.user,
                configs.c.password,
                configs.c.version,
            )
            .where(configs.c.institution_id == institution_id)
            .limit(1)
        )
        with engine.connect() as conn:
            result = conn.execute(query).mappings().fetchone()
            if result:
                config = dict(result)
                config["password"] = decrypt_config_secret(config.get("password"))
                return config
            else:
                return None
            
    def get_subjects_status_table(self):
        metadata = MetaData()
        table = Table(
            "subjects_status",
            metadata,
            Column("institution_id", Integer, primary_key=True),
            Column("subject_id", Integer, primary_key=True),
            Column("status", String(1), nullable=False),
            Column("start_date", Date, nullable=True),
            Column("end_date", Date, nullable=True),
            Column("updated_at", DateTime(timezone=True), nullable=False),
            Column("update_type", String(50), nullable=False),
        )
        return table

    def get_subject_indicator_status_table(self):
        metadata = MetaData()
        table = Table(
            "subject_indicator_status",
            metadata,
            Column("institution_id", Integer, primary_key=True),
            Column("subject_id", Integer, primary_key=True),
            Column("actor", String(20), primary_key=True),
            Column("indicator_name", String(50), primary_key=True),
            Column("status", String(1), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
        )
        return table
    
    def insert_subject_analysis_status(self, institution_id: int, subject_id: int, status: str, update_type: str = None, engine=None):
        engine = engine or self.get_connector()
        table = self.get_subjects_status_table()
        resolved_update_type = update_type or "nao_indicado"
        
        stmt = pg_insert(table).values(
            institution_id=institution_id,
            subject_id=subject_id,
            status=status,
            updated_at=func.now(),
            update_type=resolved_update_type,
        ).on_conflict_do_update(
            constraint="subjects_status_pkey",
            set_={
                "status": status,
                "updated_at": func.now(),
                "update_type": resolved_update_type,
            }
        )

        with engine.begin() as conn:
            conn.execute(stmt)

    def update_subject_analysis_status(self, institution_id: int, subject_id: int, status: str, update_type: str = None, engine=None):
        """Atualiza explicitamente o status"""
        engine = engine or self.get_connector()
        table = self.get_subjects_status_table()
        resolved_update_type = update_type or "nao_indicado"
        with engine.begin() as conn:
            conn.execute(
                table.update()
                .where(
                    and_(
                        table.c.institution_id == institution_id,
                        table.c.subject_id == subject_id
                    )
                )
                .values(
                    status=status,
                    updated_at=func.now(),
                    update_type=resolved_update_type,
                )
            )

    def upsert_indicator_status(
        self,
        institution_id: int,
        subject_id: int,
        actor: str,
        indicator_name: str,
        status: str,
        engine=None,
        conn=None,
    ):
        engine = engine or self.get_connector()
        table = self.get_subject_indicator_status_table()

        stmt = pg_insert(table).values(
            institution_id=institution_id,
            subject_id=subject_id,
            actor=actor,
            indicator_name=indicator_name,
            status=status,
            updated_at=func.now(),
        ).on_conflict_do_update(
            constraint="subject_indicator_status_pkey",
            set_={
                "status": status,
                "updated_at": func.now(),
            }
        )

        if conn is not None:
            conn.execute(stmt)
        else:
            with engine.begin() as db_conn:
                db_conn.execute(stmt)
    
    def get_connection_with_config(self, config):
        return pymysql.connect(
            host = config['host'],
            port = config['port'],
            user = config['user'],
            password = config['password'],
            db = config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

db = SQLAlchemy()
