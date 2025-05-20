from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, mail

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Registrar blueprints
    from routes.atividades import atividades_bp
    app.register_blueprint(atividades_bp)
    
    # Registrar rotas
    from routes import register_routes
    register_routes(app)
    
    return app 