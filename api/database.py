from flask_sqlalchemy import SQLAlchemy
import os
import pymysql
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DECIMAL
from sqlalchemy.exc import SQLAlchemyError
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

db = SQLAlchemy()