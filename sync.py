import os
from app import create_app, db
from flask_migrate import Migrate, init, migrate, upgrade

def force_sync():
    app = create_app()
    Migrate(app, db)

    with app.app_context():
        print("--- Iniciando Sincronização ---")

        if not os.path.exists('migrations'):
            init()
            print("Pasta migrations criada.")

        print("Aplicando migrations pendentes...")
        try:
            upgrade()
            print("Banco atualizado com sucesso.")
        except Exception as e:
            print(f"Erro ao aplicar migrations: {e}")
            return

        print("Detectando mudanças nos modelos...")
        try:
            migrate(message="Adicionando colunas faltantes")
            upgrade()
            print("\n SUCESSO")
        except Exception as e:
            print(f"Nenhuma mudança detectada ou erro: {e}")

if __name__ == "__main__":
    force_sync()
