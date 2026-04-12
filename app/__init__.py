import os
from datetime import timedelta
from flask import Flask
from app.auth import register_auth_hooks
from app.models import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'estoque-dev-secret-change-me'
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY') or app.config['SECRET_KEY']
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_EXPIRE_MINUTES'] = int(os.getenv('JWT_EXPIRE_MINUTES', '60'))
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    register_auth_hooks(app)

    with app.app_context():
        from app import models 
        
        from app.routes.auth import auth
        from app.routes.departamento import departamento
        from app.routes.obra import obra
        from app.routes.usuarios import usuarios
        from app.routes.marca import marca
        from app.routes.sku import sku
        from app.routes.produtos import produtos
        from app.routes.familia import familia
        from app.routes.tipo import tipo
        from app.routes.main import main

        app.register_blueprint(auth)
        app.register_blueprint(departamento)
        app.register_blueprint(obra)
        app.register_blueprint(usuarios)
        app.register_blueprint(main)
        app.register_blueprint(produtos)
        app.register_blueprint(sku)
        app.register_blueprint(familia)
        app.register_blueprint(tipo)
        app.register_blueprint(marca)

    return app