import os
import sys
from app import app, db
from config import config

# Carrega a configuração apropriada
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])
config[config_name].init_app(app)

# Cria as pastas necessárias
os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'uploads', 'alunos'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'uploads', 'instrutores'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'uploads', 'documentos'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'uploads', 'certificados'), exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Cria o banco de dados se não existir
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    print("\n[AVISO] Para rodar o sistema corretamente, use:\n  flask run\nou\n  python -m projetocbmepi.run\n\nRodar diretamente pode causar erros de importação!\n")
    sys.exit(1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 