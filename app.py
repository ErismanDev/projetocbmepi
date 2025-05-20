from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from .config import Config
from .models import *
from .routes import register_routes

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicialização das extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configuração do login_manager
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Importação das rotas
    register_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 