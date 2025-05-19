from flask import Flask
from flask_migrate import Migrate
from app import app, db

# Inicializa o Flask-Migrate
migrate = Migrate(app, db)

# Comandos disponíveis após importar este arquivo:
# flask db init - Inicializa o sistema de migrações (apenas na primeira vez)
# flask db migrate -m "descrição da mudança" - Cria uma nova migração
# flask db upgrade - Aplica as migrações pendentes
# flask db downgrade - Reverte a última migração
# flask db history - Mostra o histórico de migrações
# flask db current - Mostra a versão atual do banco
# flask db stamp - Marca o banco como estando em uma versão específica 