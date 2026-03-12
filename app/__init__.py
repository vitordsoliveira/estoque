import os
from flask import Flask
from app.models import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from app import models 
        
        from app.routes.marca import marca
        from app.routes.sku import sku
        from app.routes.produtos import produtos
        from app.routes.familia import familia
        from app.routes.tipo import tipo
        from app.routes.main import main

        app.register_blueprint(main)
        app.register_blueprint(produtos)
        app.register_blueprint(sku)
        app.register_blueprint(familia)
        app.register_blueprint(tipo)
        app.register_blueprint(marca)

    return app