import os
from app import create_app, db
from flask_migrate import Migrate, init, migrate, upgrade, stamp
import sqlalchemy as sa

def force_sync():
    app = create_app()
    Migrate(app, db)

    with app.app_context():
        print("--- Iniciando Sincronização Forçada ---")
        
        if not os.path.exists('migrations'):
            init()
            print("Pasta migrations criada.")

        stamp()
        print("Carimbado (stamp) realizado.")

        print("Detectando colunas faltantes...")
        try:
            migrate(message="Adicionando colunas faltantes")
            upgrade()
            print("\n SUCESSO")
        except Exception as e:
            print(f"\n ERRO ao atualizar: {e}")

if __name__ == "__main__":
    force_sync()