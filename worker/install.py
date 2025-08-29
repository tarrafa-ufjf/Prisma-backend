import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DECIMAL
from sqlalchemy.exc import SQLAlchemyError

# Carregar variáveis do arquivo .env
load_dotenv()

# Ler variáveis de ambiente
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_DATABASE")

# Criar engine de conexão
engine = create_engine(
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

metadata = MetaData()

def criar_tabela(nome_tabela, colunas):
    try:
        cols = []
        for nome, tipo in colunas.items():
            if nome == "id":
                cols.append(Column(nome, tipo, primary_key=True, autoincrement=True))
            else:
                cols.append(Column(nome, tipo))
        
        tabela = Table(nome_tabela, metadata, *cols)
        metadata.create_all(engine)
        print(f"Tabela '{nome_tabela}' criada com sucesso!")
    except SQLAlchemyError as e:
        print("Erro ao criar tabela:", e)

if __name__ == "__main__":
    colunas_engajamento_global = {
        "id": Integer,
        "course_id": Integer,
        "value": Integer
    }
    criar_tabela("engajamento_global", colunas_engajamento_global)
