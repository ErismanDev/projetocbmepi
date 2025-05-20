# Este arquivo torna o diretório routes um pacote Python 

from flask import Blueprint

def register_routes(app):
    from .atividades import atividades_bp
    app.register_blueprint(atividades_bp) 