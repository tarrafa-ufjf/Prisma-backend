from app import app
from auth import initialize_auth_storage


if __name__ == "__main__":
    initialize_auth_storage(app)
    print("Tabelas e roles de autenticacao local criadas com sucesso.")
