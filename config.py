import os
from datetime import timedelta

class Config:
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bombeiro_mirim.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Configurações de email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_TYPE = 'filesystem'
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'sua-chave-csrf-aqui'
    PASSWORD_SALT = os.environ.get('PASSWORD_SALT') or 'salt-padrao'
    TOKEN_EXPIRATION = timedelta(hours=1)  # Tempo de expiração do token de recuperação de senha
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de compressão
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # Configurações de limitação de taxa
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Configurações de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'sua-chave-jwt-aqui'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Configurações de CORS
    CORS_HEADERS = 'Content-Type'
    
    # Configurações de debug
    DEBUG = os.environ.get('FLASK_DEBUG', True)
    TESTING = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Configurações específicas para produção
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configuração de log
        handler = RotatingFileHandler('logs/bombeiro_mirim.log', maxBytes=10000, backupCount=1)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 