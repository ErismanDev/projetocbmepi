from flask import Flask, redirect, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user
from flask_mail import Mail
from .config import Config
from .routes import register_routes
from .extensions import db, migrate, login_manager, mail

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
    
    # Importar modelos após inicializar as extensões
    from .models import Usuario
    
    # Importação das rotas
    register_routes(app)
    
    @app.route("/")
    def index():
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email")
            senha = request.form.get("senha")
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario and usuario.verificar_senha(senha):
                login_user(usuario)
                return redirect("/atividades")
            else:
                flash("Usuário ou senha inválidos", "danger")
        return render_template("login.html")
    
    @app.route("/esqueci_senha", methods=["GET", "POST"])
    def esqueci_senha():
        if request.method == "POST":
            # Aqui você pode implementar o envio de email de recuperação
            flash("Se o e-mail existir, as instruções foram enviadas.", "info")
        return render_template("esqueci_senha.html")
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    @app.route("/criar_admin")
    def criar_admin():
        from werkzeug.security import generate_password_hash
        from models import Usuario
        admin = Usuario.query.filter_by(email='admin@bombeiromirim.com').first()
        if not admin:
            admin = Usuario(
                nome='Administrador',
                email='admin@bombeiromirim.com',
                senha_hash=generate_password_hash('admin123'),
                tipo='admin',
                status='ativo'
            )
            db.session.add(admin)
            db.session.commit()
            return "Usuário admin criado com sucesso! Email: admin@bombeiromirim.com | Senha: admin123"
        else:
            return "Usuário admin já existe."
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 