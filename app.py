from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, g, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateField, FileField, EmailField, PasswordField, FloatField, FieldList, FormField, BooleanField, MultipleFileField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange, EqualTo
from sqlalchemy import extract
import json
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xlsxwriter import Workbook
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bombeiro_mirim.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(photo, folder):
    if photo and photo.filename:
        # Gera um nome único para o arquivo
        filename = secure_filename(photo.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"

        # Cria o diretório se não existir
        upload_folder = os.path.join(app.root_path, 'static', 'uploads', folder)
        os.makedirs(upload_folder, exist_ok=True)

        # Salva o arquivo
        filepath = os.path.join(upload_folder, filename)
        photo.save(filepath)

        # Retorna o caminho relativo para salvar no banco
        return f'uploads/{folder}/{filename}'
    return None

def get_aniversariantes_mes():
    hoje = datetime.now()
    mes_atual = hoje.month
    
    # Busca aniversariantes entre instrutores
    instrutores = Usuario.query.filter(
        extract('month', Usuario.data_nascimento) == mes_atual,
        Usuario.status == 'ativo'
    ).all()
    
    # Busca aniversariantes entre alunos
    alunos = Aluno.query.filter(
        extract('month', Aluno.data_nascimento) == mes_atual,
        Aluno.status == 'ativo'
    ).all()
    
    return {
        'instrutores': instrutores,
        'alunos': alunos
    }

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# MODELOS
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='instrutor')  # 'instrutor' ou 'admin'
    
    # Dados pessoais
    cpf = db.Column(db.String(14), unique=True)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    telefone = db.Column(db.String(20))
    telefone_emergencia = db.Column(db.String(20))
    
    # Endereço
    cep = db.Column(db.String(9))
    logradouro = db.Column(db.String(100))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    
    # Dados profissionais
    formacao = db.Column(db.String(100))
    especializacao = db.Column(db.String(100))
    numero_registro = db.Column(db.String(50))  # Número de registro profissional
    data_admissao = db.Column(db.Date)
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, afastado, etc
    observacoes = db.Column(db.Text)
    
    # Documentos
    foto = db.Column(db.String(255))  # Caminho para a foto
    comprovante_residencia = db.Column(db.String(255))  # Caminho para o documento
    certificados = db.Column(db.String(255))  # Caminho para certificados
    
    # Relacionamentos
    atividades = db.relationship('Atividade', backref='instrutor', lazy=True)
    turmas = db.relationship('Turma', backref='instrutor', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now)  # Data/hora de cadastro

    @property
    def is_instrutor(self):
        return self.tipo == 'instrutor'

    @property
    def is_admin(self):
        return self.tipo == 'admin'

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
        
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(255))  # Caminho para a foto do aluno
    email = db.Column(db.String(100), unique=True, nullable=False)  # Email para login
    senha_hash = db.Column(db.String(128), nullable=False)  # Senha para login
    rg = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    tipo_sanguineo = db.Column(db.String(5), nullable=False)
    
    # Dados do Responsável
    responsavel_nome = db.Column(db.String(100), nullable=False)
    responsavel_cpf = db.Column(db.String(14), nullable=False)
    responsavel_telefone = db.Column(db.String(20), nullable=False)
    responsavel_email = db.Column(db.String(100), nullable=False)
    
    # Dados de Contato
    telefone = db.Column(db.String(20), nullable=False)
    telefone_emergencia = db.Column(db.String(20))
    
    # Dados de Saúde
    alergias = db.Column(db.Text)
    medicamentos = db.Column(db.Text)
    documentos = db.Column(db.Text, default='[]')
    plano_saude = db.Column(db.String(100))
    numero_plano_saude = db.Column(db.String(50))
    
    # Endereço
    cep = db.Column(db.String(9))
    logradouro = db.Column(db.String(100))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    
    # Filiação
    nome_mae = db.Column(db.String(100))
    nome_pai = db.Column(db.String(100))
    
    # Dados do Sistema
    status = db.Column(db.String(20), default='ativo')  # ativo ou inativo
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    participacoes = db.relationship('Participacao', backref='aluno', lazy=True)
    presencas = db.relationship('Presenca', backref='aluno_presenca', lazy=True)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, executada
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

class Participacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividade.id'), nullable=False)
    presente = db.Column(db.Boolean, default=False)
    observacao = db.Column(db.Text)

class Curso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    carga_horaria = db.Column(db.Integer, nullable=False)
    duracao = db.Column(db.Integer, nullable=False)  # Duração em meses
    requisitos = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativo')  # ativo ou inativo
    observacoes = db.Column(db.Text)
    turmas = db.relationship('Turma', backref='curso', lazy=True)
    disciplinas = db.relationship('Disciplina', backref='curso', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Disciplina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    carga_horaria = db.Column(db.Integer, nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    horario_inicio_manha = db.Column(db.String(5), nullable=True)  # Formato: "08:00"
    horario_fim_manha = db.Column(db.String(5), nullable=True)     # Formato: "12:00"
    horario_inicio_tarde = db.Column(db.String(5), nullable=True)  # Formato: "14:00"
    horario_fim_tarde = db.Column(db.String(5), nullable=True)     # Formato: "18:00"
    turno = db.Column(db.String(20), nullable=False, default='manha')  # manha, tarde, integral
    local = db.Column(db.String(200), nullable=False)
    vagas = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ativa')  # ativa, concluída, cancelada
    observacoes = db.Column(db.Text)  # Adicionado campo observacoes
    alunos = db.relationship('Aluno', secondary='aluno_turma', backref=db.backref('turmas', lazy='dynamic'))
    disciplinas = db.relationship('Disciplina', secondary='turma_disciplina', backref=db.backref('turmas', lazy='dynamic'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# Tabela de associação entre Turma e Disciplina
turma_disciplina = db.Table('turma_disciplina',
    db.Column('turma_id', db.Integer, db.ForeignKey('turma.id'), primary_key=True),
    db.Column('disciplina_id', db.Integer, db.ForeignKey('disciplina.id'), primary_key=True),
    db.Column('data_inicio', db.Date),
    db.Column('data_fim', db.Date)
)

class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    disciplina_id = db.Column(db.Integer, db.ForeignKey('disciplina.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='realizada')  # realizada, cancelada, remarcada
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    turma = db.relationship('Turma', backref='aulas')
    disciplina = db.relationship('Disciplina', backref='aulas')
    instrutor = db.relationship('Usuario', backref='aulas_ministradas')
    presencas = db.relationship('Presenca', backref='aula', cascade='all, delete-orphan')

class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    matricula_id = db.Column(db.Integer, db.ForeignKey('matricula.id'), nullable=True)  # Tornando opcional
    diario_id = db.Column(db.Integer, db.ForeignKey('diario_classe.id'), nullable=False)
    presente = db.Column(db.Boolean, default=False)
    justificativa = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# Tabela de associação entre Aluno e Turma
aluno_turma = db.Table('aluno_turma',
    db.Column('aluno_id', db.Integer, db.ForeignKey('aluno.id'), primary_key=True),
    db.Column('turma_id', db.Integer, db.ForeignKey('turma.id'), primary_key=True),
    db.Column('data_matricula', db.DateTime, default=datetime.now)
)

class Matricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    data_matricula = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='ativa')  # ativa, trancada, concluida, cancelada
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    turma = db.relationship('Turma', backref=db.backref('matriculas', lazy=True))
    aluno = db.relationship('Aluno', backref=db.backref('matriculas', lazy=True))
    presencas = db.relationship('Presenca', backref='matricula', lazy=True)
    avaliacoes = db.relationship('Avaliacao', backref='matricula', lazy=True)

class DiarioClasse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    disciplina_id = db.Column(db.Integer, db.ForeignKey('disciplina.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    turma = db.relationship('Turma', backref=db.backref('diarios', lazy=True))
    disciplina = db.relationship('Disciplina', backref=db.backref('diarios', lazy=True))
    presencas = db.relationship('Presenca', backref='diario', lazy=True)

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula_id = db.Column(db.Integer, db.ForeignKey('matricula.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # teorica, pratica, final
    titulo = db.Column(db.String(100), nullable=False)
    nota = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    observacoes = db.Column(db.Text)

# ROTAS
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('area_instrutor'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        # Primeiro verifica se é um usuário administrativo (admin/instrutor)
        usuario = db.session.query(Usuario).filter_by(email=email).first()
        if usuario and usuario.verificar_senha(senha):
            session['usuario_id'] = usuario.id
            session['usuario_tipo'] = usuario.tipo
            session['usuario_nome'] = usuario.nome
            # Verifica aniversário
            hoje = datetime.now().date()
            if usuario.data_nascimento and usuario.data_nascimento.month == hoje.month and usuario.data_nascimento.day == hoje.day:
                session['aniversariante'] = True
                session['aniversariante_nome'] = usuario.nome
            else:
                session.pop('aniversariante', None)
                session.pop('aniversariante_nome', None)
            return redirect(url_for('area_instrutor'))
        
        # Se não for usuário administrativo, verifica se é um aluno
        aluno = db.session.query(Aluno).filter_by(email=email).first()
        if aluno and aluno.verificar_senha(senha):
            if aluno.status == 'inativo':
                flash('Sua conta está inativa. Entre em contato com a administração.')
                return redirect(url_for('login'))
                
            session['aluno_id'] = aluno.id
            session['aluno_nome'] = aluno.nome
            # Verifica aniversário
            hoje = datetime.now().date()
            if aluno.data_nascimento and aluno.data_nascimento.month == hoje.month and aluno.data_nascimento.day == hoje.day:
                session['aniversariante'] = True
                session['aniversariante_nome'] = aluno.nome
            else:
                session.pop('aniversariante', None)
                session.pop('aniversariante_nome', None)
            return redirect(url_for('area_aluno'))
        
        flash('Email ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' in session:
        return redirect(url_for('area_instrutor'))
    elif 'aluno_id' in session:
        return redirect(url_for('area_aluno'))
    return redirect(url_for('index'))

@app.route('/instrutor')
def area_instrutor():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    if not usuario:
        session.clear()
        return redirect(url_for('login'))
    
    # Busca alunos recentes
    alunos_recentes = Aluno.query.order_by(Aluno.created_at.desc()).limit(5).all()
    
    # Busca atividades
    atividades = Atividade.query.order_by(Atividade.data.desc()).all()
    
    # Busca turmas do instrutor
    turmas = Turma.query.filter_by(instrutor_id=usuario.id).all()
    
    # Contadores
    total_alunos = Aluno.query.count()
    total_atividades = Atividade.query.count()
    total_turmas = Turma.query.count()
    
    # Atividades recentes
    atividades_recentes = Atividade.query.order_by(Atividade.data.desc()).limit(5).all()
    
    # Aniversariantes do mês
    hoje = datetime.now()
    aniversariantes = {
        'instrutores': Usuario.query.filter(
            extract('month', Usuario.data_nascimento) == hoje.month
        ).all(),
        'alunos': Aluno.query.filter(
            extract('month', Aluno.data_nascimento) == hoje.month
        ).all()
    }
    
    # Busca cursos ativos
    cursos = Curso.query.filter_by(status='ativo').all()
    
    return render_template('dashboard_instrutor.html',
                         usuario=usuario,
                         alunos=alunos_recentes,
                         atividades=atividades,
                         turmas=turmas,
                         total_alunos=total_alunos,
                         total_atividades=total_atividades,
                         total_turmas=total_turmas,
                         atividades_recentes=atividades_recentes,
                         aniversariantes=aniversariantes,
                         cursos=cursos,
                         hoje=hoje)

@app.route('/aluno')
def area_aluno():
    if 'aluno_id' not in session:
        return redirect(url_for('login'))
        
    aluno = Aluno.query.get(session['aluno_id'])
    
    # Busca as participações do aluno
    participacoes = Participacao.query.filter_by(aluno_id=aluno.id).all()
    
    # Estatísticas
    total_atividades = len(participacoes)
    total_presencas = len([p for p in participacoes if p.presente])
    
    # Próximas atividades (atividades futuras)
    hoje = datetime.now()
    proximas_atividades = Atividade.query.filter(Atividade.data >= hoje).order_by(Atividade.data).limit(5).all()
    
    # Turmas do aluno
    turmas = aluno.turmas.all()
    
    # Adiciona o aluno ao contexto global do template
    g.aluno = aluno
    
    return render_template('dashboard_aluno.html',
                         aluno=aluno,
                         participacoes=participacoes,
                         total_atividades=total_atividades,
                         total_presencas=total_presencas,
                         proximas_atividades=proximas_atividades,
                         turmas=turmas)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session or \
           db.session.get(Usuario, session['usuario_id']).tipo != 'admin':
            flash('Acesso negado. Apenas administradores podem realizar esta ação.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session and 'aluno_id' not in session:
            flash('Por favor, faça login para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/usuarios/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        
        if tipo == 'admin':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            if senha != confirmar_senha:
                flash('As senhas não coincidem')
                return redirect(url_for('cadastrar_usuario'))

            if Usuario.query.filter_by(email=email).first():
                flash('Email já cadastrado')
                return redirect(url_for('cadastrar_usuario'))

            novo_usuario = Usuario(
                nome=nome,
                email=email,
                tipo='admin',
                status='ativo'
            )
            novo_usuario.set_senha(senha)
            
        elif tipo == 'instrutor':
            instrutor_id = request.form.get('instrutor_id')
            if not instrutor_id:
                flash('Selecione um instrutor')
                return redirect(url_for('cadastrar_usuario'))
                
            instrutor = Usuario.query.get(instrutor_id)
            if not instrutor or instrutor.tipo != 'instrutor':
                flash('Instrutor não encontrado')
                return redirect(url_for('cadastrar_usuario'))
                
            if Usuario.query.filter_by(email=instrutor.email).first():
                flash('Este instrutor já possui um usuário cadastrado')
                return redirect(url_for('cadastrar_usuario'))
                
            novo_usuario = Usuario(
                nome=instrutor.nome,
                email=instrutor.email,
                tipo='instrutor',
                status='ativo'
            )
            novo_usuario.set_senha('123456')  # Senha padrão
            
        elif tipo == 'aluno':
            aluno_id = request.form.get('aluno_id')
            if not aluno_id:
                flash('Selecione um aluno')
                return redirect(url_for('cadastrar_usuario'))
                
            aluno = Aluno.query.get(aluno_id)
            if not aluno:
                flash('Aluno não encontrado')
                return redirect(url_for('cadastrar_usuario'))
                
            if Usuario.query.filter_by(email=aluno.email).first():
                flash('Este aluno já possui um usuário cadastrado')
                return redirect(url_for('cadastrar_usuario'))
                
            novo_usuario = Usuario(
                nome=aluno.nome,
                email=aluno.email,
                tipo='aluno',
                status='ativo'
            )
            novo_usuario.set_senha('123456')  # Senha padrão
            
        else:
            flash('Tipo de usuário inválido')
            return redirect(url_for('cadastrar_usuario'))
            
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!')
            return redirect(url_for('listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar usuário: {str(e)}')
            return redirect(url_for('cadastrar_usuario'))
            
    # Carrega lista de instrutores e alunos para o formulário
    instrutores = Usuario.query.filter_by(tipo='instrutor').all()
    alunos = Aluno.query.filter_by(status='ativo').all()
    
    return render_template('cadastrar_usuario.html', instrutores=instrutores, alunos=alunos)

@app.route('/cadastrar_instrutor', methods=['GET', 'POST'])
@admin_required
def cadastrar_instrutor():
    if request.method == 'POST':
        try:
            # Verifica se o CPF já existe
            cpf = request.form['cpf'].replace('.', '').replace('-', '')
            if Usuario.query.filter_by(cpf=cpf).first():
                flash('Este CPF já está cadastrado no sistema', 'error')
                return redirect(url_for('cadastrar_instrutor'))

            # Verifica se o email já existe
            email = request.form['email']
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado no sistema', 'error')
                return redirect(url_for('cadastrar_instrutor'))

            # Verifica se as senhas coincidem
            senha = request.form['senha']
            confirmar_senha = request.form['confirmar_senha']
            if senha != confirmar_senha:
                flash('As senhas não coincidem', 'error')
                return redirect(url_for('cadastrar_instrutor'))

            # Processa a foto se foi enviada
            foto_path = None
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto.filename != '':
                    foto_path = save_photo(foto, 'instrutores')

            # Cria o novo instrutor
            instrutor = Usuario(
                nome=request.form['nome'],
                email=email,
                senha=generate_password_hash(senha),
                cpf=cpf,
                rg=request.form['rg'],
                data_nascimento=datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else None,
                telefone=request.form['telefone'],
                telefone_emergencia=request.form.get('telefone_emergencia'),
                formacao=request.form.get('formacao'),
                especializacao=request.form.get('especializacao'),
                data_admissao=datetime.strptime(request.form['data_admissao'], '%Y-%m-%d').date() if request.form.get('data_admissao') else None,
                status=request.form['status'],
                tipo='instrutor',
                foto=foto_path,
                cep=request.form.get('cep'),
                logradouro=request.form.get('logradouro'),
                numero=request.form.get('numero'),
                complemento=request.form.get('complemento'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                estado=request.form.get('estado')
            )
            
            db.session.add(instrutor)
            db.session.commit()
            flash('Instrutor cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_instrutores'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar instrutor: {str(e)}', 'error')
            print(f"Erro detalhado: {str(e)}")
            return redirect(url_for('cadastrar_instrutor'))
            
    return render_template('cadastrar_instrutor.html')

@app.route('/cadastrar_aluno', methods=['GET', 'POST'])
@admin_required
def cadastrar_aluno():
    if request.method == 'POST':
        try:
            # Verifica se o CPF já existe
            cpf = request.form['cpf'].replace('.', '').replace('-', '')
            if Aluno.query.filter_by(cpf=cpf).first():
                flash('Este CPF já está cadastrado no sistema', 'error')
                return redirect(url_for('cadastrar_aluno'))

            # Verifica se o email já existe
            if Usuario.query.filter_by(email=request.form['email']).first() or Aluno.query.filter_by(email=request.form['email']).first():
                flash('Este email já está cadastrado no sistema', 'error')
                return redirect(url_for('cadastrar_aluno'))

            # Verifica se as senhas coincidem
            if request.form['senha'] != request.form['confirmar_senha']:
                flash('As senhas não coincidem', 'error')
                return redirect(url_for('cadastrar_aluno'))

            # Processa a foto se foi enviada
            foto_path = None
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto.filename != '':
                    foto_path = save_photo(foto, 'alunos')

            # Processa a data de nascimento e calcula a idade
            data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
            hoje = datetime.now().date()
            idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

            # Processa o CPF do responsável
            cpf_responsavel = request.form['responsavel_cpf'].replace('.', '').replace('-', '')

            # Cria o aluno com os dados do formulário
            aluno = Aluno(
                nome=request.form['nome'],
                foto=foto_path,
                email=request.form['email'],
                senha_hash=generate_password_hash(request.form['senha']),
                rg=request.form['rg'],
                cpf=cpf,
                data_nascimento=data_nascimento,
                idade=idade,
                tipo_sanguineo=request.form['tipo_sanguineo'],
                responsavel_nome=request.form['responsavel_nome'],
                responsavel_cpf=cpf_responsavel,
                responsavel_telefone=request.form['responsavel_telefone'],
                responsavel_email=request.form['responsavel_email'],
                telefone=request.form['telefone'],
                telefone_emergencia=request.form.get('telefone_emergencia'),
                alergias=request.form.get('alergias'),
                medicamentos=request.form.get('medicamentos'),
                plano_saude=request.form.get('plano_saude'),
                numero_plano_saude=request.form.get('numero_plano_saude'),
                nome_mae=request.form['nome_mae'],
                nome_pai=request.form.get('nome_pai'),
                status='ativo'
            )

            # Processa documentos enviados (edição de aluno)
            documentos = []
            arquivos = request.files.getlist('documentos')
            for idx, arquivo in enumerate(arquivos):
                if arquivo and arquivo.filename:
                    caminho = save_photo(arquivo, 'alunos/docs')
                    nome_identificador = request.form.get(f'nome_identificador_{idx}', '')
                    documentos.append({'caminho': caminho, 'nome_identificador': nome_identificador})

            # Mantém documentos antigos
            if aluno.documentos:
                antigos = json.loads(aluno.documentos)
                documentos = antigos + documentos

            aluno.documentos = json.dumps(documentos)

            db.session.add(aluno)
            db.session.commit()
            flash('Aluno cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_alunos'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar aluno: {str(e)}', 'error')
            print(f"Erro detalhado: {str(e)}")
            return redirect(url_for('cadastrar_aluno'))

    return render_template('cadastrar_aluno.html')

@app.route('/aluno/<int:aluno_id>')
def detalhes_aluno(aluno_id):
    # Permitir acesso se for admin OU se o aluno logado for o dono do perfil
    if 'usuario_id' not in session and (session.get('aluno_id') != aluno_id):
        return redirect(url_for('index'))
    aluno = Aluno.query.get_or_404(aluno_id)
    participacoes = Participacao.query.filter_by(aluno_id=aluno_id).all()
    import json
    docs = json.loads(aluno.documentos) if aluno.documentos else []
    return render_template('detalhes_aluno.html', aluno=aluno, participacoes=participacoes, documentos=docs)

@app.route('/aluno/<int:aluno_id>/atualizar', methods=['POST'])
@admin_required
def atualizar_aluno(aluno_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    aluno = Aluno.query.get_or_404(aluno_id)
    try:
        # Verifica se o CPF já existe e não pertence ao aluno atual
        cpf = request.form['cpf']
        aluno_existente = Aluno.query.filter_by(cpf=cpf).first()
        if aluno_existente and aluno_existente.id != aluno_id:
            flash('Este CPF já está cadastrado no sistema')
            return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))

        # Processa a foto se foi enviada
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                # Remove a foto antiga se existir
                if aluno.foto:
                    try:
                        old_photo_path = os.path.join('static', aluno.foto)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    except Exception as e:
                        print(f"Erro ao remover foto antiga: {str(e)}")
                
                # Salva a nova foto
                foto_path = save_photo(foto, 'alunos')
                aluno.foto = foto_path

        aluno.nome = request.form['nome']
        aluno.email = request.form['email']
        aluno.senha_hash = generate_password_hash(request.form['senha'])
        aluno.rg = request.form['rg']
        aluno.cpf = request.form['cpf']
        aluno.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
        aluno.idade = int(request.form['idade'])
        aluno.responsavel_nome = request.form['responsavel_nome']
        aluno.responsavel_cpf = request.form['responsavel_cpf']
        aluno.responsavel_telefone = request.form['responsavel_telefone']
        aluno.responsavel_email = request.form['responsavel_email']
        aluno.telefone = request.form['telefone']
        aluno.telefone_emergencia = request.form['telefone_emergencia']
        aluno.cep = request.form['cep']
        aluno.logradouro = request.form['logradouro']
        aluno.numero = request.form['numero']
        aluno.complemento = request.form['complemento']
        aluno.bairro = request.form['bairro']
        aluno.cidade = request.form['cidade']
        aluno.estado = request.form['estado']
        aluno.nome_mae = request.form['nome_mae']
        aluno.nome_pai = request.form['nome_pai']
        aluno.status = request.form['status']
        
        db.session.commit()
        flash('Aluno atualizado com sucesso!')
    except Exception as e:
        flash('Erro ao atualizar aluno')
        print(e)
    status_filtro = request.form.get('status_filtro', 'todos')
    return redirect(url_for('listar_alunos', status=status_filtro))

@app.route('/aluno/<int:aluno_id>/excluir', methods=['POST'])
@admin_required
def excluir_aluno(aluno_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    aluno = Aluno.query.get_or_404(aluno_id)
    try:
        aluno.status = 'inativo'
        db.session.commit()
        flash('Aluno inativado com sucesso!')
    except Exception as e:
        flash('Erro ao inativar aluno')
        print(e)
    return redirect(url_for('dashboard'))

@app.route('/atividade/<int:atividade_id>')
def detalhes_atividade(atividade_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    atividade = Atividade.query.get_or_404(atividade_id)
    alunos = Aluno.query.filter_by(status='ativo').all()
    presencas = {p.aluno_id for p in Participacao.query.filter_by(atividade_id=atividade_id, presente=True)}
    observacoes = {p.aluno_id: p.observacao for p in Participacao.query.filter_by(atividade_id=atividade_id)}
    return render_template('detalhes_atividade.html', 
                         atividade=atividade, 
                         alunos=alunos, 
                         presencas=presencas,
                         observacoes=observacoes)

@app.route('/atividade/<int:atividade_id>/atualizar', methods=['POST'])
@login_required
def atualizar_atividade(atividade_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    atividade = Atividade.query.get_or_404(atividade_id)
    
    atividade.titulo = request.form.get('titulo')
    atividade.descricao = request.form.get('descricao')
    atividade.data = datetime.strptime(request.form.get('data'), '%Y-%m-%d').date()

    db.session.commit()
    flash('Atividade atualizada com sucesso!', 'success')
    return redirect(url_for('detalhes_atividade', atividade_id=atividade.id))

@app.route('/atividade/<int:atividade_id>/excluir', methods=['POST'])
@admin_required
def excluir_atividade(atividade_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    atividade = Atividade.query.get_or_404(atividade_id)
    try:
        db.session.delete(atividade)
        db.session.commit()
        flash('Atividade excluída com sucesso!')
    except Exception as e:
        flash('Erro ao excluir atividade')
        print(e)
    return redirect(url_for('dashboard'))

@app.route('/atividade/<int:atividade_id>/presenca', methods=['POST'])
@admin_required
def registrar_presenca(atividade_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    try:
        # Limpa presenças anteriores
        Participacao.query.filter_by(atividade_id=atividade_id).delete()
        
        # Registra novas presenças
        alunos = Aluno.query.filter_by(status='ativo').all()
        for aluno in alunos:
            presente = f'presenca_{aluno.id}' in request.form
            observacao = request.form.get(f'obs_{aluno.id}', '')
            participacao = Participacao(
                aluno_id=aluno.id,
                atividade_id=atividade_id,
                presente=presente,
                observacao=observacao
            )
            db.session.add(participacao)
        
        db.session.commit()
        flash('Presenças registradas com sucesso!')
    except Exception as e:
        flash('Erro ao registrar presenças')
        print(e)
    return redirect(url_for('detalhes_atividade', atividade_id=atividade_id))

@app.route('/resetar_senha', methods=['GET', 'POST'])
def resetar_senha():
    if request.method == 'POST':
        email = request.form['email']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Aqui você implementaria o envio real do email
            # Por enquanto, apenas simulamos com uma mensagem
            flash('Se o email existir em nossa base, você receberá as instruções para resetar sua senha.')
        else:
            # Mesmo que o usuário não exista, mostramos a mesma mensagem por segurança
            flash('Se o email existir em nossa base, você receberá as instruções para resetar sua senha.')
        
        return redirect(url_for('login'))
    return render_template('resetar_senha.html')

def criar_usuario_inicial():
    with app.app_context():
        if not Usuario.query.filter_by(email='admin@bombeiromirim.com').first():
            admin = Usuario(
                nome='Administrador',
                email='admin@bombeiromirim.com',
                senha_hash=generate_password_hash('admin123'),
                tipo='admin'
            )
            db.session.add(admin)
            db.session.commit()

@app.route('/cursos')
def listar_cursos():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    cursos = Curso.query.all()
    return render_template('cursos.html', cursos=cursos)

@app.route('/cursos/novo', methods=['GET', 'POST'])
@login_required
def novo_curso():
    form = CursoForm()
    if form.validate_on_submit():
        try:
            curso = Curso(
                nome=form.nome.data,
                descricao=form.descricao.data,
                carga_horaria=form.carga_horaria.data,
                duracao=form.duracao.data,
                requisitos=form.requisitos.data,
                status=form.status.data,
                observacoes=form.observacoes.data
            )
            db.session.add(curso)
            db.session.commit()
            flash('Curso cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_cursos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar curso: {str(e)}', 'error')
    print(form.errors)
    return render_template('novo_curso.html', form=form)

@app.route('/curso/<int:curso_id>')
@login_required
def detalhes_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    # Busca todas as disciplinas do curso
    disciplinas = Disciplina.query.filter_by(curso_id=curso_id).all()
    # Busca todas as turmas do curso
    turmas = Turma.query.filter_by(curso_id=curso_id).all()
    return render_template('detalhes_curso.html', 
                         curso=curso, 
                         disciplinas=disciplinas,
                         turmas=turmas)

@app.route('/curso/<int:curso_id>/atualizar', methods=['POST'])
@login_required
def atualizar_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    try:
        # Validação dos dados recebidos
        if not request.form.get('nome'):
            raise ValueError('O nome do curso é obrigatório')
            
        # Atualização dos dados
        curso.nome = request.form.get('nome')
        curso.descricao = request.form.get('descricao', '')
        
        # Validação e conversão de números
        try:
            curso.carga_horaria = int(request.form.get('carga_horaria', 0))
            curso.duracao = int(request.form.get('duracao', 0))
        except ValueError:
            raise ValueError('Carga horária e duração devem ser números válidos')
            
        curso.requisitos = request.form.get('requisitos', '')
        curso.status = request.form.get('status', 'ativo')
        curso.observacoes = request.form.get('observacoes', '')
        
        # Atualiza o timestamp
        curso.updated_at = datetime.now()
        
        db.session.commit()
        flash('Curso atualizado com sucesso!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Erro ao atualizar curso: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar curso: {str(e)}', 'error')
        print(f"Erro detalhado: {str(e)}")
        
    return redirect(url_for('detalhes_curso', curso_id=curso_id))

@app.route('/turmas')
def listar_turmas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    # Busca todas as turmas com seus relacionamentos
    turmas = Turma.query.options(
        db.joinedload(Turma.curso),
        db.joinedload(Turma.instrutor),
        db.joinedload(Turma.disciplinas)
    ).all()
    
    return render_template('turmas.html', turmas=turmas)

@app.route('/turmas/nova', methods=['GET', 'POST'])
@login_required
def nova_turma():
    form = TurmaForm()
    form.curso_id.choices = [(c.id, c.nome) for c in Curso.query.filter_by(status='ativo').all()]
    form.instrutor_id.choices = [(i.id, i.nome) for i in Usuario.query.filter_by(tipo='instrutor', status='ativo').all()]
    
    if form.validate_on_submit():
        try:
            turma = Turma(
                nome=form.nome.data,
                curso_id=form.curso_id.data,
                instrutor_id=form.instrutor_id.data,
                data_inicio=form.data_inicio.data,
                data_fim=form.data_fim.data,
                turno=form.turno.data,
                horario_inicio_manha=form.horario_inicio_manha.data,
                horario_fim_manha=form.horario_fim_manha.data,
                horario_inicio_tarde=form.horario_inicio_tarde.data,
                horario_fim_tarde=form.horario_fim_tarde.data,
                local=form.local.data,
                vagas=form.vagas.data,
                status=form.status.data,
                observacoes=form.observacoes.data
            )
            
            # Adiciona as disciplinas do curso à turma
            curso = Curso.query.get(form.curso_id.data)
            if curso and curso.disciplinas:
                turma.disciplinas.extend(curso.disciplinas)
            
            db.session.add(turma)
            db.session.commit()
            flash('Turma cadastrada com sucesso!', 'success')
            return redirect(url_for('listar_turmas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar turma: {str(e)}', 'error')
            print(f"Erro detalhado ao criar turma: {str(e)}")
    
    return render_template('nova_turma.html', form=form)

@app.route('/turma/<int:turma_id>')
def detalhes_turma(turma_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    turma = Turma.query.get_or_404(turma_id)
    instrutores = Usuario.query.filter_by(tipo='instrutor', status='ativo').all()
    return render_template('detalhes_turma.html', turma=turma, instrutores=instrutores)

@app.route('/turma/<int:turma_id>/atualizar', methods=['POST'])
@admin_required
def atualizar_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    try:
        turma.nome = request.form['nome']
        turma.instrutor_id = int(request.form['instrutor_id'])
        turma.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
        turma.data_fim = datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date()
        turma.status = request.form['status']
        
        db.session.commit()
        flash('Turma atualizada com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar turma: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('detalhes_turma', turma_id=turma.id))

@app.route('/aluno/resetar_senha', methods=['GET', 'POST'])
def resetar_senha_aluno():
    if request.method == 'POST':
        email = request.form['email']
        aluno = Aluno.query.filter_by(email=email).first()
        
        if aluno:
            # Aqui você implementaria o envio real do email
            # Por enquanto, apenas simulamos com uma mensagem
            flash('Se o email existir em nossa base, você receberá as instruções para resetar sua senha.')
        else:
            # Mesmo que o aluno não exista, mostramos a mesma mensagem por segurança
            flash('Se o email existir em nossa base, você receberá as instruções para resetar sua senha.')
        
        return redirect(url_for('login'))
    return render_template('resetar_senha_aluno.html')

@app.route('/aluno/perfil')
def perfil_aluno():
    if 'aluno_id' not in session:
        return redirect(url_for('login'))
        
    aluno = Aluno.query.get_or_404(session['aluno_id'])
    participacoes = Participacao.query.filter_by(aluno_id=aluno.id).all()
    return render_template('perfil_aluno.html', aluno=aluno, participacoes=participacoes)

@app.route('/usuarios')
@admin_required
def listar_usuarios():
    # Busca todos os usuários (instrutores e admin)
    usuarios = Usuario.query.all()
    
    # Busca todos os alunos ativos
    alunos = Aluno.query.filter_by(status='ativo').all()
    
    return render_template('usuarios.html', 
                         usuarios=usuarios, 
                         alunos=alunos)

@app.route('/usuario/<int:usuario_id>/atualizar', methods=['POST'])
@admin_required
def atualizar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Atualiza os dados básicos
    usuario.nome = request.form.get('nome')
    usuario.email = request.form.get('email')
    usuario.cpf = request.form.get('cpf')
    usuario.rg = request.form.get('rg')
    usuario.tipo = request.form.get('tipo')
    usuario.status = request.form.get('status')
    
    # Atualiza a foto se uma nova foi enviada
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto and allowed_file(foto.filename):
            # Remove a foto antiga se existir
            if usuario.foto:
                try:
                    os.remove(os.path.join(app.static_folder, usuario.foto))
                except:
                    pass
            # Salva a nova foto
            usuario.foto = save_photo(foto, 'usuarios')
    
    try:
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        status_filtro = request.form.get('status_filtro', 'todos')
        return redirect(url_for('listar_usuarios', status=status_filtro))
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar usuário. Por favor, tente novamente.', 'error')
        print(f"Erro ao atualizar usuário: {str(e)}")
        return redirect(url_for('listar_usuarios', status=request.form.get('status_filtro', 'todos')))

@app.route('/aluno/<int:aluno_id>/alterar_senha', methods=['POST'])
@admin_required
def alterar_senha_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    try:
        nova_senha = request.form['nova_senha']
        if len(nova_senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres')
            return redirect(url_for('listar_usuarios'))
            
        aluno.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()
        flash('Senha alterada com sucesso!')
    except Exception as e:
        flash('Erro ao alterar senha')
        print(e)
    return redirect(url_for('listar_usuarios'))

@app.route('/instrutores')
@admin_required
def listar_instrutores():
    status_filtro = request.args.get('status', 'todos')
    
    if status_filtro == 'ativo':
        instrutores = Usuario.query.filter_by(tipo='instrutor', status='ativo').all()
    elif status_filtro == 'inativo':
        instrutores = Usuario.query.filter_by(tipo='instrutor', status='inativo').all()
    else:
        instrutores = Usuario.query.filter_by(tipo='instrutor').all()
    
    return render_template('instrutores.html', instrutores=instrutores, status_filtro=status_filtro)

@app.route('/instrutor/<int:instrutor_id>/atualizar', methods=['POST'])
@admin_required
def atualizar_instrutor(instrutor_id):
    instrutor = Usuario.query.get_or_404(instrutor_id)
    if instrutor.tipo != 'instrutor':
        flash('Usuário não é um instrutor', 'error')
        return redirect(url_for('listar_instrutores'))
    try:
        # Atualiza dados básicos
        instrutor.nome = request.form['nome']
        instrutor.email = request.form['email']
        instrutor.cpf = request.form.get('cpf')
        instrutor.rg = request.form.get('rg')
        instrutor.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else None
        instrutor.telefone = request.form.get('telefone')
        instrutor.telefone_emergencia = request.form.get('telefone_emergencia')
        instrutor.formacao = request.form.get('formacao')
        instrutor.especializacao = request.form.get('especializacao')
        instrutor.data_admissao = datetime.strptime(request.form['data_admissao'], '%Y-%m-%d').date() if request.form.get('data_admissao') else None
        
        # Atualiza a foto se foi enviada
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename:
                if instrutor.foto:
                    try:
                        old_photo_path = os.path.join(app.static_folder, instrutor.foto.lstrip('/'))
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    except Exception as e:
                        print(f"Erro ao remover foto antiga: {str(e)}")
                foto_path = save_photo(foto, 'instrutores')
                instrutor.foto = foto_path
        
        # Processa upload de documentos
        if 'documentos' in request.files:
            arquivos = request.files.getlist('documentos')
            novos_docs = []
            for arquivo in arquivos:
                if arquivo and arquivo.filename:
                    doc_path = save_photo(arquivo, 'instrutores/docs')
                    novos_docs.append(doc_path)
            
            # Mantém os antigos e adiciona os novos
            docs_atuais = instrutor.certificados.split(';') if instrutor.certificados else []
            docs_atuais = [d for d in docs_atuais if d]  # Remove entradas vazias
            instrutor.certificados = ';'.join(docs_atuais + novos_docs)
        
        db.session.commit()
        flash('Instrutor atualizado com sucesso!', 'success')
        return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar instrutor: {str(e)}', 'error')
        print(f"Erro detalhado: {str(e)}")
        return redirect(url_for('editar_instrutor', instrutor_id=instrutor_id))

@app.route('/alunos')
@admin_required
def listar_alunos():
    status = request.args.get('status', 'todos')
    
    if status == 'ativo':
        alunos = Aluno.query.filter_by(status='ativo').all()
    elif status == 'inativo':
        alunos = Aluno.query.filter_by(status='inativo').all()
    else:
        alunos = Aluno.query.all()
        
    return render_template('alunos.html', alunos=alunos, status_filtro=status)

@app.route('/aluno/<int:aluno_id>/alterar_status', methods=['POST'])
@admin_required
def alterar_status_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    try:
        novo_status = 'inativo' if aluno.status == 'ativo' else 'ativo'
        aluno.status = novo_status
        db.session.commit()
        flash(f'Aluno {novo_status} com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status do aluno: {str(e)}', 'error')
    return redirect(url_for('listar_alunos'))

@app.route('/curso/<int:curso_id>/disciplinas')
@admin_required
def listar_disciplinas(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    instrutores = Usuario.query.filter_by(tipo='instrutor', status='ativo').all()
    return render_template('disciplinas.html', curso=curso, instrutores=instrutores)

@app.route('/curso/<int:curso_id>/disciplina/nova', methods=['POST'])
@admin_required
def nova_disciplina(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    try:
        disciplina = Disciplina(
            nome=request.form['nome'],
            descricao=request.form['descricao'],
            carga_horaria=int(request.form['carga_horaria']),
            curso_id=curso_id,
            instrutor_id=request.form.get('instrutor_id')
        )
        db.session.add(disciplina)
        db.session.commit()
        flash('Disciplina adicionada com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar disciplina: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('listar_disciplinas', curso_id=curso_id))

@app.route('/disciplina/<int:disciplina_id>/atualizar', methods=['POST'])
@admin_required
def atualizar_disciplina(disciplina_id):
    disciplina = Disciplina.query.get_or_404(disciplina_id)
    try:
        disciplina.nome = request.form['nome']
        disciplina.descricao = request.form['descricao']
        disciplina.carga_horaria = int(request.form['carga_horaria'])
        disciplina.instrutor_id = request.form.get('instrutor_id')
        
        db.session.commit()
        flash('Disciplina atualizada com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar disciplina: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('listar_disciplinas', curso_id=disciplina.curso_id))

@app.route('/disciplina/<int:disciplina_id>/excluir', methods=['POST'])
@admin_required
def excluir_disciplina(disciplina_id):
    disciplina = Disciplina.query.get_or_404(disciplina_id)
    curso_id = disciplina.curso_id
    try:
        db.session.delete(disciplina)
        db.session.commit()
        flash('Disciplina excluída com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir disciplina: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('listar_disciplinas', curso_id=curso_id))

@app.route('/turma/<int:turma_id>/disciplinas')
@admin_required
def gerenciar_disciplinas_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    instrutores = Usuario.query.filter_by(tipo='instrutor', status='ativo').all()
    return render_template('gerenciar_disciplinas_turma.html', turma=turma, instrutores=instrutores)

@app.route('/turma/<int:turma_id>/disciplinas/adicionar', methods=['POST'])
@admin_required
def adicionar_disciplina_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    try:
        disciplina = Disciplina(
            nome=request.form['nome'],
            descricao=request.form['descricao'],
            carga_horaria=int(request.form['carga_horaria']),
            instrutor_id=request.form['instrutor_id'] or None,
            status=request.form['status'],
            turma_id=turma.id
        )
        db.session.add(disciplina)
        db.session.commit()
        flash('Disciplina adicionada com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar disciplina: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('gerenciar_disciplinas_turma', turma_id=turma.id))

@app.route('/turma/<int:turma_id>/disciplinas/<int:disciplina_id>/atualizar', methods=['POST'])
@admin_required
def atualizar_disciplina_turma(turma_id, disciplina_id):
    turma = Turma.query.get_or_404(turma_id)
    disciplina = Disciplina.query.get_or_404(disciplina_id)
    
    if disciplina.turma_id != turma.id:
        flash('Disciplina não pertence a esta turma!')
        return redirect(url_for('gerenciar_disciplinas_turma', turma_id=turma.id))
    
    try:
        disciplina.nome = request.form['nome']
        disciplina.descricao = request.form['descricao']
        disciplina.carga_horaria = int(request.form['carga_horaria'])
        disciplina.instrutor_id = request.form['instrutor_id'] or None
        disciplina.status = request.form['status']
        
        db.session.commit()
        flash('Disciplina atualizada com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar disciplina: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('gerenciar_disciplinas_turma', turma_id=turma.id))

@app.route('/turma/<int:turma_id>/disciplinas/<int:disciplina_id>/remover', methods=['POST'])
@admin_required
def remover_disciplina_turma(turma_id, disciplina_id):
    turma = Turma.query.get_or_404(turma_id)
    disciplina = Disciplina.query.get_or_404(disciplina_id)
    
    if disciplina.turma_id != turma.id:
        flash('Disciplina não pertence a esta turma!')
        return redirect(url_for('gerenciar_disciplinas_turma', turma_id=turma.id))
    
    try:
        db.session.delete(disciplina)
        db.session.commit()
        flash('Disciplina removida com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover disciplina: {str(e)}')
        print(f"Erro detalhado: {str(e)}")
    return redirect(url_for('gerenciar_disciplinas_turma', turma_id=turma.id))

@app.route('/turma/<int:turma_id>/alunos', methods=['GET', 'POST'])
@admin_required
def gerenciar_alunos_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    
    if request.method == 'POST':
        try:
            # Limpa os alunos existentes
            turma.alunos = []
            
            # Adiciona os alunos selecionados
            alunos_ids = request.form.getlist('alunos')
            for aluno_id in alunos_ids:
                aluno = Aluno.query.get(int(aluno_id))
                if aluno and aluno.status == 'ativo':
                    turma.alunos.append(aluno)
            
            db.session.commit()
            flash('Alunos da turma atualizados com sucesso!')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar alunos: {str(e)}')
            
    return render_template('alunos_turma.html', 
                         turma=turma,
                         todos_alunos=Aluno.query.filter_by(status='ativo').all())

@app.route('/turma/<int:turma_id>/aulas')
def listar_aulas(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    return render_template('aulas.html', turma=turma)

@app.route('/aula/<int:aula_id>')
def detalhes_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    return render_template('detalhes_aula.html', aula=aula)

@app.route('/aula/<int:aula_id>/presenca', methods=['POST'])
def registrar_presenca_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    
    if request.method == 'POST':
        try:
            for aluno in aula.turma.alunos:
                presenca = Presenca.query.filter_by(aula_id=aula.id, aluno_id=aluno.id).first()
                if not presenca:
                    presenca = Presenca(aula_id=aula.id, aluno_id=aluno.id)
                    db.session.add(presenca)
                
                presenca.presente = f'presenca_{aluno.id}' in request.form
                presenca.justificativa = request.form.get(f'justificativa_{aluno.id}', '')
            
            db.session.commit()
            flash('Presenças registradas com sucesso!')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar presenças: {str(e)}')
    
    return redirect(url_for('detalhes_aula', aula_id=aula.id))

@app.route('/aula/<int:aula_id>/atualizar', methods=['POST'])
def atualizar_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    
    if request.method == 'POST':
        try:
            aula.disciplina_id = request.form['disciplina_id']
            aula.instrutor_id = request.form['instrutor_id']
            aula.data = datetime.strptime(f"{request.form['data']} {request.form['hora']}", '%Y-%m-%d %H:%M')
            aula.conteudo = request.form['conteudo']
            aula.observacoes = request.form['observacoes']
            aula.status = request.form['status']
            
            db.session.commit()
            flash('Aula atualizada com sucesso!')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar aula: {str(e)}')
            print(f"Erro detalhado: {str(e)}")
    
    return redirect(url_for('detalhes_aula', aula_id=aula.id))

@app.route('/turma/<int:turma_id>/aulas/nova', methods=['POST'])
@login_required
def nova_aula(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    try:
        aula = Aula(
            turma_id=turma_id,
            disciplina_id=request.form['disciplina_id'],
            instrutor_id=request.form['instrutor_id'],
            data=datetime.strptime(f"{request.form['data']} {request.form['hora']}", '%Y-%m-%d %H:%M'),
            conteudo=request.form['conteudo'],
            observacoes=request.form.get('observacoes', ''),
            status='realizada'
        )
        db.session.add(aula)
        db.session.commit()
        flash('Aula cadastrada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar aula: {str(e)}', 'error')
    return redirect(url_for('listar_aulas', turma_id=turma_id))

class AlunoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    rg = StringField('RG', validators=[DataRequired(), Length(max=20)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(max=14)])
    data_nascimento = DateField('Data de Nascimento', validators=[DataRequired()])
    tipo_sanguineo = SelectField('Tipo Sanguíneo', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    foto = FileField('Foto')
    
    # Dados do Responsável
    responsavel_nome = StringField('Nome do Responsável', validators=[DataRequired(), Length(max=100)])
    responsavel_cpf = StringField('CPF do Responsável', validators=[DataRequired(), Length(max=14)])
    responsavel_telefone = StringField('Telefone do Responsável', validators=[DataRequired(), Length(max=20)])
    responsavel_email = EmailField('Email do Responsável', validators=[DataRequired(), Email(), Length(max=100)])
    
    # Dados de Contato
    telefone = StringField('Telefone', validators=[DataRequired(), Length(max=20)])
    telefone_emergencia = StringField('Telefone de Emergência', validators=[Optional(), Length(max=20)])
    
    # Dados de Saúde
    alergias = TextAreaField('Alergias', validators=[Optional()])
    medicamentos = TextAreaField('Medicamentos em Uso', validators=[Optional()])
    plano_saude = StringField('Plano de Saúde', validators=[Optional(), Length(max=100)])
    numero_plano_saude = StringField('Número do Plano de Saúde', validators=[Optional(), Length(max=50)])
    
    # Endereço
    cep = StringField('CEP', validators=[Optional(), Length(max=9)])
    logradouro = StringField('Logradouro', validators=[Optional(), Length(max=100)])
    numero = StringField('Número', validators=[Optional(), Length(max=10)])
    complemento = StringField('Complemento', validators=[Optional(), Length(max=100)])
    bairro = StringField('Bairro', validators=[Optional(), Length(max=100)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=100)])
    estado = SelectField('Estado', choices=[
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ], validators=[Optional()])
    
    # Filiação
    nome_mae = StringField('Nome da Mãe', validators=[Optional(), Length(max=100)])
    nome_pai = StringField('Nome do Pai', validators=[Optional(), Length(max=100)])
    
    # Status
    status = SelectField('Status', choices=[
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo')
    ], validators=[DataRequired()])

class CursoForm(FlaskForm):
    nome = StringField('Nome do Curso', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    duracao = IntegerField('Duração (meses)', validators=[DataRequired(), NumberRange(min=1)])
    carga_horaria = IntegerField('Carga Horária (horas)', validators=[DataRequired(), NumberRange(min=1)])
    status = SelectField('Status', choices=[
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo')
    ], validators=[DataRequired()])
    requisitos = TextAreaField('Requisitos', validators=[Optional(), Length(max=500)])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])

class TurmaForm(FlaskForm):
    nome = StringField('Nome da Turma', validators=[DataRequired(), Length(min=3, max=100)])
    curso_id = SelectField('Curso', coerce=int, validators=[DataRequired()])
    instrutor_id = SelectField('Coordenador', coerce=int, validators=[DataRequired()])
    data_inicio = DateField('Data de Início', validators=[DataRequired()])
    data_fim = DateField('Data de Término', validators=[DataRequired()])
    turno = SelectField('Turno', choices=[
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('integral', 'Integral')
    ], validators=[DataRequired()])
    horario_inicio_manha = StringField('Horário Início Manhã', validators=[Optional(), Length(max=5)])
    horario_fim_manha = StringField('Horário Fim Manhã', validators=[Optional(), Length(max=5)])
    horario_inicio_tarde = StringField('Horário Início Tarde', validators=[Optional(), Length(max=5)])
    horario_fim_tarde = StringField('Horário Fim Tarde', validators=[Optional(), Length(max=5)])
    local = StringField('Local', validators=[DataRequired(), Length(max=200)])
    vagas = IntegerField('Vagas', validators=[DataRequired(), NumberRange(min=1)])
    status = SelectField('Status', choices=[
        ('ativa', 'Ativa'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada')
    ], validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        # Validação dos horários baseada no turno
        if self.turno.data == 'manha':
            if not self.horario_inicio_manha.data or not self.horario_fim_manha.data:
                self.horario_inicio_manha.errors.append('Horários da manhã são obrigatórios para turno da manhã')
                return False
            self.horario_inicio_tarde.data = None
            self.horario_fim_tarde.data = None
        elif self.turno.data == 'tarde':
            if not self.horario_inicio_tarde.data or not self.horario_fim_tarde.data:
                self.horario_inicio_tarde.errors.append('Horários da tarde são obrigatórios para turno da tarde')
                return False
            self.horario_inicio_manha.data = None
            self.horario_fim_manha.data = None
        elif self.turno.data == 'integral':
            if not all([self.horario_inicio_manha.data, self.horario_fim_manha.data,
                        self.horario_inicio_tarde.data, self.horario_fim_tarde.data]):
                self.horario_inicio_manha.errors.append('Todos os horários são obrigatórios para turno integral')
                return False
        return True

@app.route('/alunos/novo', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    form = AlunoForm()
    if form.validate_on_submit():
        try:
            aluno = Aluno(
                nome_completo=form.nome.data,
                data_nascimento=form.data_nascimento.data,
                sexo=form.sexo.data,
                rg=form.rg.data,
                cpf=form.cpf.data,
                endereco=form.endereco.data,
                telefone=form.telefone.data,
                email=form.email.data,
                nome_responsavel=form.nome_responsavel.data,
                telefone_responsavel=form.telefone_responsavel.data,
                email_responsavel=form.email_responsavel.data,
                status=form.status.data,
                observacoes=form.observacoes.data
            )
            
            if form.foto.data:
                filename = secure_filename(form.foto.data.filename)
                form.foto.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                aluno.foto = filename
            
            db.session.add(aluno)
            db.session.commit()
            flash('Aluno cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_alunos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar aluno: {str(e)}', 'error')
    
    return render_template('novo_aluno.html', form=form)

@app.route('/login_aluno', methods=['GET', 'POST'])
def login_aluno():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        aluno = Aluno.query.filter_by(email=email).first()
        if aluno and aluno.verificar_senha(senha):
            if aluno.status == 'inativo':
                flash('Sua conta está inativa. Entre em contato com a administração.')
                return redirect(url_for('login_aluno'))
                
            session['aluno_id'] = aluno.id
            session['aluno_nome'] = aluno.nome
            return redirect(url_for('area_aluno'))
            
        flash('Email ou senha inválidos')
    return render_template('login_aluno.html')

@app.route('/turma/<int:turma_id>/excluir', methods=['POST'])
@admin_required
def excluir_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    try:
        turma.status = 'cancelada'
        db.session.commit()
        flash('Turma cancelada com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar turma: {str(e)}')
    return redirect(url_for('listar_turmas'))

@app.route('/curso/<int:curso_id>/excluir', methods=['POST'])
@admin_required
def excluir_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    try:
        curso.status = 'inativo'
        db.session.commit()
        flash('Curso inativado com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao inativar curso: {str(e)}')
    return redirect(url_for('listar_cursos'))

@app.route('/aula/<int:aula_id>/excluir', methods=['POST'])
@login_required
def excluir_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    turma_id = aula.turma_id
    try:
        db.session.delete(aula)
        db.session.commit()
        flash('Aula excluída com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir aula: {str(e)}')
    return redirect(url_for('listar_aulas', turma_id=turma_id))

@app.route('/usuario/<int:usuario_id>/alterar_senha', methods=['POST'])
@admin_required
def alterar_senha_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    nova_senha = request.form.get('nova_senha')
    
    if nova_senha:
        usuario.set_senha(nova_senha)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
    else:
        flash('Nova senha não fornecida.', 'error')
    
    return redirect(url_for('detalhes_usuario', usuario_id=usuario_id))

@app.route('/usuario/<int:usuario_id>/excluir', methods=['POST'])
@admin_required
def excluir_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verifica se o usuário não é o último administrador
    if usuario.tipo == 'admin':
        admin_count = Usuario.query.filter_by(tipo='admin').count()
        if admin_count <= 1:
            flash('Não é possível excluir o último administrador do sistema.', 'error')
            return redirect(url_for('detalhes_usuario', usuario_id=usuario_id))
    
    try:
        # Remove a foto do usuário se existir
        if usuario.foto:
            foto_path = os.path.join(app.static_folder, usuario.foto)
            if os.path.exists(foto_path):
                os.remove(foto_path)
        
        # Remove os documentos do usuário se existirem
        if usuario.certificados:
            for doc in usuario.certificados.split(';'):
                if doc:
                    doc_path = os.path.join(app.static_folder, doc)
                    if os.path.exists(doc_path):
                        os.remove(doc_path)
        
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuário: {str(e)}', 'error')
        return redirect(url_for('detalhes_usuario', usuario_id=usuario_id))

@app.route('/usuario/<int:usuario_id>')
@login_required
def detalhes_usuario(usuario_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Verifica se o usuário tem permissão para ver os detalhes
    if session.get('usuario_id') != usuario_id and session.get('usuario_tipo') != 'admin':
        flash('Você não tem permissão para acessar esta página.')
        return redirect(url_for('dashboard'))
        
    return render_template('detalhes_usuario.html', usuario=usuario)

@app.route('/instrutor/<int:instrutor_id>')
@login_required
def detalhes_instrutor(instrutor_id):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
        
    instrutor = Usuario.query.get_or_404(instrutor_id)
    if instrutor.tipo != 'instrutor':
        flash('Usuário não é um instrutor')
        return redirect(url_for('listar_instrutores'))
        
    # Verifica se o usuário é admin ou se está acessando seus próprios detalhes
    usuario_atual = Usuario.query.get(session['usuario_id'])
    if not usuario_atual.is_admin and usuario_atual.id != instrutor_id:
        flash('Você não tem permissão para acessar estes detalhes')
        return redirect(url_for('area_instrutor'))
        
    return render_template('detalhes_instrutor.html', instrutor=instrutor, usuario_atual=usuario_atual)

@app.route('/instrutor/<int:instrutor_id>/alterar-senha', methods=['POST'])
@admin_required
def alterar_senha_instrutor(instrutor_id):
    instrutor = Usuario.query.get_or_404(instrutor_id)
    if instrutor.tipo != 'instrutor':
        flash('Usuário não é um instrutor', 'error')
        return redirect(url_for('listar_instrutores'))
        
    nova_senha = request.form.get('nova_senha')
    confirmar_senha = request.form.get('confirmar_senha')
    
    if nova_senha != confirmar_senha:
        flash('As senhas não coincidem', 'error')
        return redirect(url_for('visualizar_instrutor', instrutor_id=instrutor_id))
        
    try:
        instrutor.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar senha: {str(e)}', 'error')
        
    return redirect(url_for('visualizar_instrutor', instrutor_id=instrutor_id))

@app.route('/instrutor/<int:instrutor_id>/excluir', methods=['POST'])
@admin_required
def excluir_instrutor(instrutor_id):
    instrutor = Usuario.query.get_or_404(instrutor_id)
    if instrutor.tipo != 'instrutor':
        flash('Usuário não é um instrutor', 'error')
        return redirect(url_for('listar_instrutores'))
        
    try:
        # Remove a foto se existir
        if instrutor.foto:
            try:
                foto_path = os.path.join(app.root_path, 'static', instrutor.foto)
                if os.path.exists(foto_path):
                    os.remove(foto_path)
            except Exception as e:
                print(f"Erro ao remover foto: {str(e)}")
                
        db.session.delete(instrutor)
        db.session.commit()
        flash('Instrutor excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir instrutor: {str(e)}', 'error')
        
    return redirect(url_for('listar_instrutores'))

class MatriculaForm(FlaskForm):
    aluno_id = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    turma_id = SelectField('Turma', coerce=int, validators=[DataRequired()])
    data_matricula = DateField('Data da Matrícula', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('ativa', 'Ativa'),
        ('trancada', 'Trancada'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada')
    ], validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])

class AlunoPresencaForm(FlaskForm):
    aluno_id = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    presente = BooleanField('Presente')
    justificativa = TextAreaField('Justificativa', validators=[Optional(), Length(max=500)])

class PresencaForm(FlaskForm):
    turma_id = SelectField('Turma', coerce=int, validators=[DataRequired()])
    data = DateField('Data', validators=[DataRequired()])
    alunos = FieldList(FormField(AlunoPresencaForm), min_entries=1)
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])

class AvaliacaoForm(FlaskForm):
    aluno_id = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    turma_id = SelectField('Turma', coerce=int, validators=[DataRequired()])
    data = DateField('Data', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[
        ('teorica', 'Teórica'),
        ('pratica', 'Prática'),
        ('final', 'Final')
    ], validators=[DataRequired()])
    nota = FloatField('Nota', validators=[DataRequired(), NumberRange(min=0, max=10)])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])

class UsuarioForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    tipo = SelectField('Tipo', choices=[
        ('admin', 'Administrador'),
        ('professor', 'Professor'),
        ('secretaria', 'Secretaria')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo')
    ], validators=[DataRequired()])

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar = BooleanField('Lembrar-me')

class RecuperarSenhaForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])

class RedefinirSenhaForm(FlaskForm):
    senha = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(),
        EqualTo('senha', message='As senhas não conferem')
    ])

class AlterarSenhaForm(FlaskForm):
    senha_atual = PasswordField('Senha Atual', validators=[DataRequired()])
    nova_senha = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(),
        EqualTo('nova_senha', message='As senhas não conferem')
    ])

class PerfilForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    foto = FileField('Foto')
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    cep = StringField('CEP', validators=[Optional(), Length(max=9)])
    logradouro = StringField('Logradouro', validators=[Optional(), Length(max=100)])
    numero = StringField('Número', validators=[Optional(), Length(max=10)])
    complemento = StringField('Complemento', validators=[Optional(), Length(max=100)])
    bairro = StringField('Bairro', validators=[Optional(), Length(max=100)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=100)])
    estado = SelectField('Estado', choices=[
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ], validators=[Optional()])

class ConfiguracoesForm(FlaskForm):
    nome_escola = StringField('Nome da Escola', validators=[DataRequired(), Length(min=3, max=100)])
    email_escola = EmailField('Email da Escola', validators=[DataRequired(), Email(), Length(max=100)])
    telefone_escola = StringField('Telefone da Escola', validators=[DataRequired(), Length(max=20)])
    cep_escola = StringField('CEP da Escola', validators=[DataRequired(), Length(max=9)])
    logradouro_escola = StringField('Logradouro da Escola', validators=[DataRequired(), Length(max=100)])
    numero_escola = StringField('Número da Escola', validators=[DataRequired(), Length(max=10)])
    complemento_escola = StringField('Complemento da Escola', validators=[Optional(), Length(max=100)])
    bairro_escola = StringField('Bairro da Escola', validators=[DataRequired(), Length(max=100)])
    cidade_escola = StringField('Cidade da Escola', validators=[DataRequired(), Length(max=100)])
    estado_escola = SelectField('Estado da Escola', choices=[
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ], validators=[DataRequired()])
    logo_escola = FileField('Logo da Escola')
    cor_primaria = StringField('Cor Primária', validators=[DataRequired(), Length(max=7)])
    cor_secundaria = StringField('Cor Secundária', validators=[DataRequired(), Length(max=7)])
    cor_terciaria = StringField('Cor Terciária', validators=[DataRequired(), Length(max=7)])

class BackupForm(FlaskForm):
    tipo = SelectField('Tipo de Backup', choices=[
        ('completo', 'Backup Completo'),
        ('banco', 'Apenas Banco de Dados'),
        ('arquivos', 'Apenas Arquivos')
    ], validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])

class RestauracaoForm(FlaskForm):
    arquivo = FileField('Arquivo de Backup', validators=[DataRequired()])
    tipo = SelectField('Tipo de Restauração', choices=[
        ('completo', 'Restauração Completa'),
        ('banco', 'Apenas Banco de Dados'),
        ('arquivos', 'Apenas Arquivos')
    ], validators=[DataRequired()])
    confirmar = BooleanField('Confirmo que desejo restaurar o backup', validators=[DataRequired()])

class LogForm(FlaskForm):
    data_inicio = DateField('Data Inicial', validators=[DataRequired()])
    data_fim = DateField('Data Final', validators=[DataRequired()])
    tipo = SelectField('Tipo de Log', choices=[
        ('todos', 'Todos'),
        ('login', 'Login'),
        ('cadastro', 'Cadastro'),
        ('edicao', 'Edição'),
        ('exclusao', 'Exclusão'),
        ('backup', 'Backup'),
        ('restauracao', 'Restauração')
    ], validators=[DataRequired()])
    usuario = SelectField('Usuário', coerce=int, validators=[Optional()])

class RelatorioForm(FlaskForm):
    tipo = SelectField('Tipo de Relatório', choices=[
        ('alunos', 'Alunos'),
        ('cursos', 'Cursos'),
        ('turmas', 'Turmas'),
        ('matriculas', 'Matrículas'),
        ('presencas', 'Presenças'),
        ('avaliacoes', 'Avaliações'),
        ('financeiro', 'Financeiro')
    ], validators=[DataRequired()])
    data_inicio = DateField('Data Inicial', validators=[DataRequired()])
    data_fim = DateField('Data Final', validators=[DataRequired()])
    formato = SelectField('Formato', choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ], validators=[DataRequired()])
    filtros = TextAreaField('Filtros Adicionais', validators=[Optional(), Length(max=500)])

class MensagemForm(FlaskForm):
    destinatario = SelectField('Destinatário', choices=[
        ('todos', 'Todos os Alunos'),
        ('turma', 'Turma Específica'),
        ('aluno', 'Aluno Específico')
    ], validators=[DataRequired()])
    turma_id = SelectField('Turma', coerce=int, validators=[Optional()])
    aluno_id = SelectField('Aluno', coerce=int, validators=[Optional()])
    assunto = StringField('Assunto', validators=[DataRequired(), Length(min=3, max=100)])
    mensagem = TextAreaField('Mensagem', validators=[DataRequired(), Length(max=1000)])
    anexos = MultipleFileField('Anexos', validators=[Optional()])

class NotificacaoForm(FlaskForm):
    tipo = SelectField('Tipo de Notificação', choices=[
        ('info', 'Informação'),
        ('sucesso', 'Sucesso'),
        ('alerta', 'Alerta'),
        ('erro', 'Erro')
    ], validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired(), Length(min=3, max=100)])
    mensagem = TextAreaField('Mensagem', validators=[DataRequired(), Length(max=500)])
    destinatario = SelectField('Destinatário', choices=[
        ('todos', 'Todos os Usuários'),
        ('admin', 'Apenas Administradores'),
        ('professor', 'Apenas Professores'),
        ('secretaria', 'Apenas Secretaria'),
        ('alunos', 'Apenas Alunos')
    ], validators=[DataRequired()])
    data_expiracao = DateField('Data de Expiração', validators=[Optional()])

class AjudaForm(FlaskForm):
    categoria = SelectField('Categoria', choices=[
        ('duvida', 'Dúvida'),
        ('sugestao', 'Sugestão'),
        ('problema', 'Problema'),
        ('outro', 'Outro')
    ], validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired(), Length(max=1000)])
    anexos = MultipleFileField('Anexos', validators=[Optional()])

class FeedbackForm(FlaskForm):
    tipo = SelectField('Tipo de Feedback', choices=[
        ('sugestao', 'Sugestão'),
        ('critica', 'Crítica'),
        ('elogio', 'Elogio'),
        ('outro', 'Outro')
    ], validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired(), Length(max=1000)])
    anexos = MultipleFileField('Anexos', validators=[Optional()])

@app.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.tipo = request.form.get('tipo')
        usuario.status = request.form.get('status')
        usuario.rg = request.form.get('rg')
        usuario.cpf = request.form.get('cpf')
        usuario.formacao = request.form.get('formacao')
        usuario.especializacao = request.form.get('especializacao')
        usuario.data_admissao = datetime.strptime(request.form.get('data_admissao'), '%Y-%m-%d') if request.form.get('data_admissao') else None
        
        # Processar foto se fornecida
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename:
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                usuario.foto = filename

        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))

    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/aluno/<int:aluno_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    
    if request.method == 'POST':
        try:
            cpf = request.form['cpf'].replace('.', '').replace('-', '')
            aluno_existente = Aluno.query.filter_by(cpf=cpf).first()
            if aluno_existente and aluno_existente.id != aluno_id:
                flash('Este CPF já está cadastrado no sistema', 'error')
                return redirect(url_for('editar_aluno', aluno_id=aluno_id))
            email = request.form['email']
            if Usuario.query.filter_by(email=email).first() or \
               (Aluno.query.filter_by(email=email).first() and Aluno.query.filter_by(email=email).first().id != aluno_id):
                flash('Este email já está cadastrado no sistema', 'error')
                return redirect(url_for('editar_aluno', aluno_id=aluno_id))
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto.filename != '':
                    if aluno.foto:
                        try:
                            old_photo_path = os.path.join(app.root_path, 'static', aluno.foto)
                            if os.path.exists(old_photo_path):
                                os.remove(old_photo_path)
                        except Exception as e:
                            print(f"Erro ao remover foto antiga: {str(e)}")
                    foto_path = save_photo(foto, 'alunos')
                    aluno.foto = foto_path

            # Processa documentos enviados
            documentos = []
            if aluno.documentos:
                documentos = json.loads(aluno.documentos)
            
            arquivos = request.files.getlist('documentos')
            for idx, arquivo in enumerate(arquivos):
                if arquivo and arquivo.filename:
                    caminho = save_photo(arquivo, 'alunos/docs')
                    nome_identificador = request.form.get(f'nome_identificador_{idx}', '')
                    documentos.append({
                        'caminho': caminho,
                        'nome_identificador': nome_identificador
                    })

            aluno.documentos = json.dumps(documentos)
            
            aluno.nome = request.form['nome']
            aluno.email = email
            aluno.rg = request.form['rg']
            aluno.cpf = cpf
            aluno.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date()
            aluno.idade = int(request.form['idade'])
            aluno.tipo_sanguineo = request.form['tipo_sanguineo']
            aluno.responsavel_nome = request.form['responsavel_nome']
            aluno.responsavel_cpf = request.form['responsavel_cpf'].replace('.', '').replace('-', '')
            aluno.responsavel_telefone = request.form['responsavel_telefone']
            aluno.responsavel_email = request.form['responsavel_email']
            aluno.telefone = request.form['telefone']
            aluno.telefone_emergencia = request.form.get('telefone_emergencia')
            aluno.alergias = request.form.get('alergias')
            aluno.medicamentos = request.form.get('medicamentos')
            aluno.plano_saude = request.form.get('plano_saude')
            aluno.numero_plano_saude = request.form.get('numero_plano_saude')
            aluno.nome_mae = request.form['nome_mae']
            aluno.nome_pai = request.form.get('nome_pai')
            aluno.status = request.form['status']
            aluno.cep = request.form.get('cep')
            aluno.logradouro = request.form.get('logradouro')
            aluno.numero = request.form.get('numero')
            aluno.complemento = request.form.get('complemento')
            aluno.bairro = request.form.get('bairro')
            aluno.cidade = request.form.get('cidade')
            aluno.estado = request.form.get('estado')
            
            db.session.commit()
            flash('Aluno atualizado com sucesso!', 'success')
            return redirect(url_for('listar_alunos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar aluno: {str(e)}', 'error')
            print(f"Erro detalhado: {str(e)}")
            return redirect(url_for('editar_aluno', aluno_id=aluno_id))
            
    return render_template('editar_aluno.html', aluno=aluno)

@app.route('/instrutor/<int:instrutor_id>/alterar_status', methods=['POST'])
@admin_required
def alterar_status_instrutor(instrutor_id):
    instrutor = Usuario.query.get_or_404(instrutor_id)
    if instrutor.tipo != 'instrutor':
        flash('Usuário não é um instrutor', 'error')
        return redirect(url_for('listar_instrutores'))
        
    try:
        novo_status = 'inativo' if instrutor.status == 'ativo' else 'ativo'
        instrutor.status = novo_status
        db.session.commit()
        flash(f'Instrutor {novo_status} com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status do instrutor: {str(e)}', 'error')
    return redirect(url_for('listar_instrutores'))

@app.route('/instrutor/<int:instrutor_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_instrutor(instrutor_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    instrutor = Usuario.query.get_or_404(instrutor_id)
        
    if request.method == 'POST':
        try:
            # Atualiza dados pessoais
            instrutor.nome = request.form.get('nome')
            instrutor.email = request.form.get('email')
            instrutor.cpf = request.form.get('cpf')
            instrutor.rg = request.form.get('rg')
            instrutor.data_nascimento = datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d') if request.form.get('data_nascimento') else None
            instrutor.telefone = request.form.get('telefone')
            instrutor.telefone_emergencia = request.form.get('telefone_emergencia')
            
            # Atualiza dados profissionais
            instrutor.formacao = request.form.get('formacao')
            instrutor.especializacao = request.form.get('especializacao')
            instrutor.numero_registro = request.form.get('numero_registro')
            instrutor.data_admissao = datetime.strptime(request.form.get('data_admissao'), '%Y-%m-%d') if request.form.get('data_admissao') else None
            instrutor.status = request.form.get('status')
            
            # Atualiza endereço
            instrutor.cep = request.form.get('cep')
            instrutor.logradouro = request.form.get('logradouro')
            instrutor.numero = request.form.get('numero')
            instrutor.complemento = request.form.get('complemento')
            instrutor.bairro = request.form.get('bairro')
            instrutor.cidade = request.form.get('cidade')
            instrutor.estado = request.form.get('estado')
            
            # Atualiza observações
            instrutor.observacoes = request.form.get('observacoes')

            # Processa a foto se foi enviada
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename:
                    # Remove a foto antiga se existir
                    if instrutor.foto:
                        try:
                            old_photo_path = os.path.join(app.static_folder, instrutor.foto)
                            if os.path.exists(old_photo_path):
                                os.remove(old_photo_path)
                        except Exception as e:
                            print(f"Erro ao remover foto antiga: {str(e)}")
                    foto_path = save_photo(foto, 'instrutores')
                    instrutor.foto = foto_path

            # Processa certificados se foram enviados
            if 'certificados' in request.files:
                arquivos = request.files.getlist('certificados')
                novos_docs = []
                for arquivo in arquivos:
                    if arquivo and arquivo.filename:
                        doc_path = save_photo(arquivo, 'instrutores/docs')
                        novos_docs.append(doc_path)
                
                # Mantém os antigos e adiciona os novos
                docs_atuais = instrutor.certificados.split(';') if instrutor.certificados else []
                docs_atuais = [d for d in docs_atuais if d]  # Remove entradas vazias
                instrutor.certificados = ';'.join(docs_atuais + novos_docs)
            
            db.session.commit()
            flash('Instrutor atualizado com sucesso!', 'success')
            return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar instrutor: {str(e)}', 'danger')
            print(f"Erro detalhado: {str(e)}")
            return redirect(url_for('editar_instrutor', instrutor_id=instrutor_id))

    return render_template('editar_instrutor.html', instrutor=instrutor)

@app.route('/instrutor/<int:instrutor_id>/documento/<int:doc_idx>/excluir', methods=['POST'])
@login_required
def excluir_documento_instrutor(instrutor_id, doc_idx):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    instrutor = Usuario.query.get_or_404(instrutor_id)
    documentos = instrutor.certificados.split(';') if instrutor.certificados else []
    
    if doc_idx >= len(documentos):
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))
    
    doc = documentos[doc_idx]
    
    try:
        # Remove o arquivo físico
        caminho_completo = os.path.join(app.static_folder, doc)
        if os.path.exists(caminho_completo):
            os.remove(caminho_completo)
        
        # Remove o documento da lista
        documentos.pop(doc_idx)
        instrutor.certificados = ';'.join(documentos)
        db.session.commit()
        flash('Documento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir documento: {str(e)}', 'danger')
    
    return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))

@app.route('/usuario/<int:usuario_id>/instrutor/<int:instrutor_id>/documento/<int:doc_idx>/editar', methods=['GET', 'POST'])
@admin_required
def editar_nome_documento_instrutor_admin(usuario_id, instrutor_id, doc_idx):
    usuario = db.session.get(Usuario, instrutor_id)
    if usuario.tipo != 'instrutor':
        flash('Usuário não é um instrutor')
        return redirect(url_for('listar_instrutores'))
    
    documentos = usuario.certificados.split(';') if usuario.certificados else []
    
    if doc_idx >= len(documentos):
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))
    
    doc = documentos[doc_idx]
    
    if request.method == 'POST':
        novo_nome = request.form.get('novo_nome')
        if not novo_nome:
            flash('O novo nome do documento é obrigatório.', 'danger')
            return render_template('editar_nome_documento_instrutor.html', usuario=usuario, doc=doc, doc_idx=doc_idx)
        
        try:
            # Mantém o caminho do arquivo, apenas atualiza o nome
            caminho_antigo = os.path.join(app.static_folder, doc)
            if os.path.exists(caminho_antigo):
                # Extrai a extensão do arquivo original
                _, extensao = os.path.splitext(doc)
                novo_caminho = os.path.join(os.path.dirname(caminho_antigo), f"{novo_nome}{extensao}")
                os.rename(caminho_antigo, novo_caminho)
                
                # Atualiza o caminho na lista de documentos
                documentos[doc_idx] = os.path.relpath(novo_caminho, app.static_folder).replace('\\', '/')
                usuario.certificados = ';'.join(documentos)
                db.session.commit()
                flash('Nome do documento atualizado com sucesso!', 'success')
                return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))
            else:
                flash('Arquivo físico não encontrado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar nome do documento: {str(e)}', 'danger')
    
    return render_template('editar_nome_documento_instrutor.html', usuario=usuario, doc=doc, doc_idx=doc_idx)

@app.route('/usuario/<int:usuario_id>/aluno/<int:aluno_id>/documento/<int:doc_idx>/editar', methods=['GET', 'POST'])
@admin_required
def editar_nome_documento_aluno_admin(usuario_id, aluno_id, doc_idx):
    aluno = Aluno.query.get_or_404(aluno_id)
    documentos = json.loads(aluno.documentos) if aluno.documentos else []
    
    if doc_idx >= len(documentos):
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))
    
    doc = documentos[doc_idx]
    
    if request.method == 'POST':
        novo_nome = request.form.get('novo_nome')
        if not novo_nome:
            flash('O novo nome do documento é obrigatório.', 'danger')
            return render_template('editar_nome_documento_aluno.html', aluno=aluno, doc=doc, doc_idx=doc_idx)
        
        try:
            # Atualiza o nome identificador do documento
            documentos[doc_idx]['nome_identificador'] = novo_nome
            aluno.documentos = json.dumps(documentos)
            db.session.commit()
            flash('Nome do documento atualizado com sucesso!', 'success')
            return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar nome do documento: {str(e)}', 'danger')
            return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))
    
    return render_template('editar_nome_documento_aluno.html', aluno=aluno, doc=doc, doc_idx=doc_idx)

@app.route('/usuario/<int:usuario_id>/aluno/<int:aluno_id>/documento/<int:doc_idx>/excluir')
@admin_required
def excluir_documento_aluno_admin(usuario_id, aluno_id, doc_idx):
    aluno = Aluno.query.get_or_404(aluno_id)
    documentos = json.loads(aluno.documentos) if aluno.documentos else []
    
    if doc_idx >= len(documentos):
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))
    
    try:
        # Remove o arquivo físico
        doc = documentos[doc_idx]
        caminho_arquivo = os.path.join(app.static_folder, doc['caminho'])
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        # Remove o documento da lista
        documentos.pop(doc_idx)
        aluno.documentos = json.dumps(documentos)
        db.session.commit()
        flash('Documento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir documento: {str(e)}', 'danger')
    
    return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))

@app.route('/usuario/<int:usuario_id>/instrutor/<int:instrutor_id>/documento/<int:doc_idx>/excluir', methods=['POST'])
@admin_required
def excluir_documento_instrutor_admin(usuario_id, instrutor_id, doc_idx):
    usuario = db.session.get(Usuario, instrutor_id)
    if usuario.tipo != 'instrutor':
        flash('Usuário não é um instrutor')
        return redirect(url_for('listar_instrutores'))
    
    documentos = usuario.certificados.split(';') if usuario.certificados else []
    
    if doc_idx >= len(documentos):
        flash('Documento não encontrado.', 'danger')
        return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))
    
    try:
        # Remove o arquivo físico
        doc = documentos[doc_idx]
        caminho_arquivo = os.path.join(app.static_folder, doc)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        # Remove o documento da lista
        documentos.pop(doc_idx)
        usuario.certificados = ';'.join(documentos)
        db.session.commit()
        flash('Documento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir documento: {str(e)}', 'danger')
    
    return redirect(url_for('detalhes_instrutor', instrutor_id=instrutor_id))

@app.route('/documento/<int:documento_id>/editar', methods=['POST'])
@login_required
def editar_documento(documento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    aluno_id = request.args.get('aluno_id')
    if not aluno_id:
        flash('ID do aluno não fornecido', 'error')
        return redirect(url_for('listar_alunos'))
        
    aluno = Aluno.query.get_or_404(aluno_id)
    documentos = json.loads(aluno.documentos) if aluno.documentos else []
    
    if documento_id >= len(documentos):
        flash('Documento não encontrado', 'error')
        return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))
    
    nome_identificador = request.form.get('nome_identificador')
    if nome_identificador:
        documentos[documento_id]['nome_identificador'] = nome_identificador
        aluno.documentos = json.dumps(documentos)
        db.session.commit()
        flash('Documento atualizado com sucesso!', 'success')
    
    return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))

@app.route('/documento/<int:documento_id>/excluir', methods=['POST'])
@login_required
def excluir_documento(documento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    aluno_id = request.args.get('aluno_id')
    if not aluno_id:
        flash('ID do aluno não fornecido', 'error')
        return redirect(url_for('listar_alunos'))
        
    aluno = Aluno.query.get_or_404(aluno_id)
    documentos = json.loads(aluno.documentos) if aluno.documentos else []
    
    if documento_id >= len(documentos):
        flash('Documento não encontrado', 'error')
        return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))
    
    try:
        # Remove o arquivo físico
        doc = documentos[documento_id]
        caminho_arquivo = os.path.join(app.static_folder, doc['caminho'])
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        # Remove o documento da lista
        documentos.pop(documento_id)
        aluno.documentos = json.dumps(documentos)
        db.session.commit()
        flash('Documento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir documento: {str(e)}', 'error')
    
    return redirect(url_for('detalhes_aluno', aluno_id=aluno_id))



@app.route('/turma/<int:turma_id>/matricula/nova', methods=['POST'])
@login_required
def nova_matricula_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('matriculas_turma', turma_id=turma_id))
    
    try:
        aluno_id = request.form.get('aluno_id')
        if not aluno_id:
            flash('Selecione um aluno', 'error')
            return redirect(url_for('matriculas_turma', turma_id=turma_id))
            
        # Verifica se o aluno já está matriculado
        if Matricula.query.filter_by(aluno_id=aluno_id, turma_id=turma_id).first():
            flash('Aluno já matriculado nesta turma', 'error')
            return redirect(url_for('matriculas_turma', turma_id=turma_id))
            
        data_matricula = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d')
        matricula = Matricula(
            aluno_id=aluno_id,
            turma_id=turma_id,
            status=request.form.get('status'),
            data_matricula=data_matricula,
            observacoes=request.form.get('observacoes')
        )
        
        db.session.add(matricula)
        db.session.commit()
        flash('Matrícula realizada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao realizar matrícula: {str(e)}', 'error')
        
    return redirect(url_for('matriculas_turma', turma_id=turma_id))

@app.route('/matricula/<int:matricula_id>/atualizar', methods=['GET', 'POST'])
@login_required
def atualizar_matricula(matricula_id):
    matricula = Matricula.query.get_or_404(matricula_id)
    turma = matricula.turma
    
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('matriculas_turma', turma_id=turma.id))
    
    if request.method == 'POST':
        try:
            matricula.status = request.form.get('status')
            matricula.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d')
            if request.form.get('data_fim'):
                matricula.data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d')
            else:
                matricula.data_fim = None
            matricula.observacoes = request.form.get('observacoes')
            db.session.commit()
            flash('Matrícula atualizada com sucesso!', 'success')
            return redirect(url_for('matriculas_turma', turma_id=turma.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar matrícula: {str(e)}', 'error')
    
    return render_template('matriculas/atualizar.html', matricula=matricula)

@app.route('/turma/<int:turma_id>/diario')
@login_required
def diario_classe(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para acessar esta turma.', 'danger')
        return redirect(url_for('listar_todas_matriculas'))
    
    disciplina_id = request.args.get('disciplina_id', type=int)
    query = DiarioClasse.query.filter_by(turma_id=turma_id)
    
    if disciplina_id:
        query = query.filter_by(disciplina_id=disciplina_id)
    
    registros = query.order_by(DiarioClasse.data.desc()).all()
    disciplinas = Disciplina.query.all()
    
    return render_template('diario_classe.html',
                         turma=turma,
                         registros=registros,
                         disciplinas=disciplinas,
                         disciplina_id=disciplina_id)

@app.route('/turma/<int:turma_id>/diario/novo', methods=['POST'])
@login_required
def novo_registro_diario(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('diario_classe', turma_id=turma_id))
    
    registro = DiarioClasse(
        turma_id=turma_id,
        disciplina_id=request.form.get('disciplina_id'),
        data=datetime.strptime(request.form.get('data'), '%Y-%m-%d'),
        conteudo=request.form.get('conteudo'),
        observacoes=request.form.get('observacoes')
    )
    
    db.session.add(registro)
    db.session.commit()
    
    flash('Registro adicionado com sucesso!', 'success')
    return redirect(url_for('diario_classe', turma_id=turma_id))

@app.route('/diario/<int:diario_id>/presenca', methods=['POST'])
@login_required
def registrar_presenca_diario(diario_id):
    registro = DiarioClasse.query.get_or_404(diario_id)
    turma = registro.turma
    
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('diario_classe', turma_id=turma.id))
    
    # Remove presenças existentes
    Presenca.query.filter_by(diario_id=diario_id).delete()
    
    # Registra novas presenças
    for matricula in turma.matriculas:
        presente = request.form.get(f'presente_{matricula.id}') == 'on'
        justificativa = request.form.get(f'justificativa_{matricula.id}')
        
        presenca = Presenca(
            diario_id=diario_id,
            matricula_id=matricula.id,
            presente=presente,
            justificativa=justificativa if not presente else None
        )
        db.session.add(presenca)
    
    db.session.commit()
    
    flash('Presenças registradas com sucesso!', 'success')
    return redirect(url_for('diario_classe', turma_id=turma.id))

@app.route('/diario/<int:registro_id>/editar', methods=['POST'])
@login_required
def editar_registro_diario(registro_id):
    registro = DiarioClasse.query.get_or_404(registro_id)
    turma = registro.turma
    
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('diario_classe', turma_id=turma.id))
    
    registro.disciplina_id = request.form.get('disciplina_id')
    registro.data = datetime.strptime(request.form.get('data'), '%Y-%m-%d')
    registro.conteudo = request.form.get('conteudo')
    registro.observacoes = request.form.get('observacoes')
    
    db.session.commit()
    
    flash('Registro atualizado com sucesso!', 'success')
    return redirect(url_for('diario_classe', turma_id=turma.id))

@app.route('/matricula/<int:matricula_id>/avaliacao/nova', methods=['POST'])
@login_required
def nova_avaliacao(matricula_id):
    matricula = Matricula.query.get_or_404(matricula_id)
    try:
        avaliacao = Avaliacao(
            matricula_id=matricula_id,
            tipo=request.form.get('tipo'),
            titulo=request.form.get('titulo'),
            descricao=request.form.get('descricao'),
            nota=float(request.form.get('nota')) if request.form.get('nota') else None,
            data=datetime.strptime(request.form.get('data'), '%Y-%m-%d').date(),
            observacoes=request.form.get('observacoes')
        )
        
        db.session.add(avaliacao)
        db.session.commit()
        flash('Avaliação registrada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar avaliação: {str(e)}', 'error')
        
    return redirect(url_for('listar_matriculas', turma_id=matricula.turma_id))

@app.route('/avaliacao/<int:avaliacao_id>/atualizar', methods=['POST'])
@login_required
def atualizar_avaliacao(avaliacao_id):
    avaliacao = Avaliacao.query.get_or_404(avaliacao_id)
    try:
        avaliacao.tipo = request.form.get('tipo')
        avaliacao.titulo = request.form.get('titulo')
        avaliacao.descricao = request.form.get('descricao')
        avaliacao.nota = float(request.form.get('nota')) if request.form.get('nota') else None
        avaliacao.data = datetime.strptime(request.form.get('data'), '%Y-%m-%d').date()
        avaliacao.observacoes = request.form.get('observacoes')
        
        db.session.commit()
        flash('Avaliação atualizada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar avaliação: {str(e)}', 'error')
        
    return redirect(url_for('listar_matriculas', turma_id=avaliacao.matricula.turma_id))

@app.route('/matriculas')
@login_required
def listar_matriculas():
    if session.get('usuario_tipo') == 'instrutor':
        # Instrutores veem apenas suas turmas
        turmas = Turma.query.filter_by(instrutor_id=session.get('usuario_id')).all()
        turma_ids = [turma.id for turma in turmas]
        matriculas = Matricula.query.filter(Matricula.turma_id.in_(turma_ids)).all()
    else:
        # Administradores veem todas as matrículas
        matriculas = Matricula.query.all()
    return render_template('matriculas/listar.html', matriculas=matriculas)

@app.route('/matriculas/nova', methods=['GET', 'POST'])
@login_required
def nova_matricula():
    if request.method == 'POST':
        aluno_id = request.form.get('aluno_id')
        turma_id = request.form.get('turma_id')
        status = request.form.get('status')
        data_matricula = request.form.get('data_matricula')
        observacoes = request.form.get('observacoes')
        
        if not data_matricula:
            flash('A data de matrícula é obrigatória!', 'error')
            return redirect(url_for('nova_matricula'))
        
        try:
            nova_matricula = Matricula(
                aluno_id=aluno_id,
                turma_id=turma_id,
                status=status,
                data_matricula=datetime.strptime(data_matricula, '%Y-%m-%d'),
                observacoes=observacoes
            )
            db.session.add(nova_matricula)
            db.session.commit()
            flash('Matrícula criada com sucesso!', 'success')
            return redirect(url_for('listar_matriculas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar matrícula: {str(e)}', 'error')
            return redirect(url_for('nova_matricula'))
    
    turmas = Turma.query.all()
    alunos = Aluno.query.all()
    return render_template('matriculas/nova.html', turmas=turmas, alunos=alunos)

@app.route('/matriculas/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    
    if session.get('usuario_tipo') == 'instrutor':
        turma = Turma.query.get(matricula.turma_id)
        if turma.instrutor_id != session.get('usuario_id'):
            flash('Você não tem permissão para excluir esta matrícula.', 'error')
            return redirect(url_for('listar_matriculas'))
    
    try:
        # Atualiza as presenças relacionadas para remover a referência à matrícula
        Presenca.query.filter_by(matricula_id=matricula.id).update({Presenca.matricula_id: None})
        
        # Exclui a matrícula
        db.session.delete(matricula)
        db.session.commit()
        flash('Matrícula excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir matrícula: {str(e)}', 'error')
    
    return redirect(url_for('listar_matriculas'))

@app.route('/diario')
@login_required
def listar_diarios():
    if session.get('usuario_tipo') == 'instrutor':
        # Instrutores veem apenas seus diários
        turmas = Turma.query.filter_by(instrutor_id=session.get('usuario_id')).all()
        turma_ids = [turma.id for turma in turmas]
        diarios = DiarioClasse.query.filter(DiarioClasse.turma_id.in_(turma_ids)).all()
    else:
        # Administradores veem todos os diários
        diarios = DiarioClasse.query.all()
    return render_template('diario/listar.html', diarios=diarios)

@app.route('/diario/turma/<int:turma_id>')
@login_required
def diario_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    if current_user.tipo == 'instrutor' and turma.instrutor_id != current_user.id:
        flash('Você não tem permissão para acessar este diário.', 'error')
        return redirect(url_for('listar_diarios'))
    
    diarios = DiarioClasse.query.filter_by(turma_id=turma_id).order_by(DiarioClasse.data_aula).all()
    return render_template('diario/turma.html', diarios=diarios, turma=turma)

@app.route('/diario/novo', methods=['GET', 'POST'])
@login_required
def novo_diario():
    if session.get('usuario_tipo') != 'instrutor':
        flash('Apenas instrutores podem criar diários.', 'error')
        return redirect(url_for('listar_diarios'))
        
    if request.method == 'POST':
        turma_id = request.form.get('turma_id')
        disciplina_id = request.form.get('disciplina_id')
        data = request.form.get('data')
        conteudo = request.form.get('conteudo')
        observacoes = request.form.get('observacoes')
        
        try:
            novo_diario = DiarioClasse(
                turma_id=turma_id,
                disciplina_id=disciplina_id,
                data=datetime.strptime(data, '%Y-%m-%d'),
                conteudo=conteudo,
                observacoes=observacoes
            )
            db.session.add(novo_diario)
            db.session.commit()
            flash('Diário criado com sucesso!', 'success')
            return redirect(url_for('listar_diarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar diário: {str(e)}', 'error')
            return redirect(url_for('novo_diario'))
    
    turmas = Turma.query.all()
    disciplinas = Disciplina.query.all()
    return render_template('diario/novo.html', turmas=turmas, disciplinas=disciplinas)

@app.route('/diario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_diario(id):
    diario = DiarioClasse.query.get_or_404(id)
    
    if current_user.tipo == 'instrutor':
        turma = Turma.query.get(diario.turma_id)
        if turma.instrutor_id != current_user.id:
            flash('Você não tem permissão para editar este diário.', 'error')
            return redirect(url_for('listar_diarios'))
    
    if request.method == 'POST':
        diario.data_aula = datetime.strptime(request.form.get('data_aula'), '%Y-%m-%d')
        diario.conteudo = request.form.get('conteudo')
        diario.observacoes = request.form.get('observacoes')
        
        db.session.commit()
        flash('Diário de classe atualizado com sucesso!', 'success')
        return redirect(url_for('listar_diarios'))
    
    return render_template('diario/editar.html', diario=diario)

@app.route('/diario/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_diario(id):
    diario = DiarioClasse.query.get_or_404(id)
    
    if current_user.tipo == 'instrutor':
        turma = Turma.query.get(diario.turma_id)
        if turma.instrutor_id != current_user.id:
            flash('Você não tem permissão para excluir este diário.', 'error')
            return redirect(url_for('listar_diarios'))
    
    db.session.delete(diario)
    db.session.commit()
    flash('Diário de classe excluído com sucesso!', 'success')
    return redirect(url_for('listar_diarios'))

@app.route('/matriculas/importar', methods=['GET', 'POST'])
@login_required
def importar_matriculas():
    if session.get('usuario_tipo') != 'admin':
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('listar_matriculas'))
        
    if request.method == 'POST':
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)
            
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)
            
        if arquivo and arquivo.filename.endswith('.csv'):
            try:
                # Lê o arquivo CSV
                stream = StringIO(arquivo.read().decode('utf-8'))
                csv_reader = csv.DictReader(stream)
                
                for row in csv_reader:
                    # Verifica se o aluno e a turma existem
                    aluno = Aluno.query.filter_by(cpf=row['cpf_aluno']).first()
                    turma = Turma.query.filter_by(nome=row['nome_turma']).first()
                    
                    if not aluno or not turma:
                        continue
                        
                    # Verifica se já existe matrícula
                    if Matricula.query.filter_by(aluno_id=aluno.id, turma_id=turma.id).first():
                        continue
                        
                    data_matricula = datetime.strptime(row.get('data_inicio', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
                    matricula = Matricula(
                        aluno_id=aluno.id,
                        turma_id=turma.id,
                        status=row.get('status', 'ativa'),
                        data_matricula=data_matricula,
                        observacoes=row.get('observacoes', '')
                    )
                    db.session.add(matricula)
                db.session.commit()
                flash('Matrículas importadas com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao importar matrículas: {str(e)}', 'error')
        else:
            flash('Formato de arquivo inválido. Use apenas arquivos CSV.', 'error')
            
    return render_template('matriculas/importar.html')

@app.route('/matriculas/exportar', methods=['GET', 'POST'])
@login_required
def exportar_matriculas():
    if session.get('usuario_tipo') != 'admin':
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return redirect(url_for('listar_matriculas'))
        
    if request.method == 'POST':
        formato = request.form.get('formato', 'csv')
        matricula_id = request.form.get('matricula_id')
        
        if matricula_id:
            matriculas = Matricula.query.filter_by(id=matricula_id).all()
        else:
            matriculas = Matricula.query.all()
            
        if formato == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Cabeçalho
            writer.writerow(['ID', 'Aluno', 'CPF', 'Turma', 'Status', 'Data Início', 'Data Fim', 'Observações'])
            
            # Dados
            for matricula in matriculas:
                writer.writerow([
                    matricula.id,
                    matricula.aluno.nome,
                    matricula.aluno.cpf,
                    matricula.turma.nome,
                    matricula.status,
                    matricula.data_inicio.strftime('%Y-%m-%d'),
                    matricula.data_fim.strftime('%Y-%m-%d') if matricula.data_fim else '',
                    matricula.observacoes
                ])
                
            output.seek(0)
            return Response(
                output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=matriculas.csv'}
            )
            
        elif formato == 'excel':
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()
            
            # Formatação
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
            
            # Cabeçalho
            headers = ['ID', 'Aluno', 'CPF', 'Turma', 'Status', 'Data Início', 'Data Fim', 'Observações']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                
            # Dados
            for row, matricula in enumerate(matriculas, start=1):
                worksheet.write(row, 0, matricula.id)
                worksheet.write(row, 1, matricula.aluno.nome)
                worksheet.write(row, 2, matricula.aluno.cpf)
                worksheet.write(row, 3, matricula.turma.nome)
                worksheet.write(row, 4, matricula.status)
                worksheet.write(row, 5, matricula.data_inicio.strftime('%Y-%m-%d'))
                worksheet.write(row, 6, matricula.data_fim.strftime('%Y-%m-%d') if matricula.data_fim else '')
                worksheet.write(row, 7, matricula.observacoes)
                
            workbook.close()
            output.seek(0)
            
            return Response(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': 'attachment; filename=matriculas.xlsx'}
            )
            
        elif formato == 'pdf':
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            style_heading = styles['Heading1']
            
            # Título
            elements.append(Paragraph('Relatório de Matrículas', style_heading))
            elements.append(Spacer(1, 20))
            
            # Tabela
            data = [['ID', 'Aluno', 'CPF', 'Turma', 'Status', 'Data Início', 'Data Fim', 'Observações']]
            
            for matricula in matriculas:
                data.append([
                    str(matricula.id),
                    matricula.aluno.nome,
                    matricula.aluno.cpf,
                    matricula.turma.nome,
                    matricula.status,
                    matricula.data_inicio.strftime('%Y-%m-%d'),
                    matricula.data_fim.strftime('%Y-%m-%d') if matricula.data_fim else '',
                    matricula.observacoes
                ])
                
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            doc.build(elements)
            output.seek(0)
            
            return Response(
                output,
                mimetype='application/pdf',
                headers={'Content-Disposition': 'attachment; filename=matriculas.pdf'}
            )
            
    return render_template('matriculas/exportar.html')

# Rotas para Atividades
@app.route('/atividades')
def listar_atividades():
    atividades = Atividade.query.all()
    return render_template('atividades/listar.html', atividades=atividades)

@app.route('/presencas')
@login_required
def listar_presencas():
    presencas = Presenca.query.all()
    return render_template('presencas/listar.html', presencas=presencas)

@app.route('/avaliacoes')
@login_required
def listar_avaliacoes():
    avaliacoes = Avaliacao.query.all()
    return render_template('avaliacoes/listar.html', avaliacoes=avaliacoes)

@app.route('/certificados')
@login_required
def listar_certificados():
    certificados = Certificado.query.all() if 'Certificado' in globals() else []
    return render_template('certificados/listar.html', certificados=certificados)

@app.route('/relatorios')
@login_required
def listar_relatorios():
    return render_template('relatorios.html')

@app.route('/relatorios/novo')
@login_required
def novo_relatorio():
    return render_template('relatorios_novo.html')

@app.route('/turma/<int:turma_id>/disciplinas', methods=['GET', 'POST'])
@login_required
def get_disciplinas_turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    disciplinas = [{'id': d.id, 'nome': d.nome} for d in turma.disciplinas]
    return jsonify(disciplinas)

@app.route('/atividades/nova', methods=['GET', 'POST'])
@login_required
def nova_atividade():
    if session.get('usuario_tipo') not in ['admin', 'instrutor']:
        flash('Você não tem permissão para criar atividades.', 'error')
        return redirect(url_for('listar_atividades'))
    if request.method == 'POST':
        try:
            titulo = request.form.get('titulo')
            descricao = request.form.get('descricao')
            data = request.form.get('data')
            if not (titulo and descricao and data):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return redirect(url_for('nova_atividade'))
            atividade = Atividade(
                titulo=titulo,
                descricao=descricao,
                data=datetime.strptime(data, '%Y-%m-%d'),
                instrutor_id=session.get('usuario_id')
            )
            db.session.add(atividade)
            db.session.commit()
            flash('Atividade criada com sucesso!', 'success')
            return redirect(url_for('listar_atividades'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar atividade: {str(e)}', 'error')
            return redirect(url_for('nova_atividade'))
    return render_template('atividades/nova.html')

@app.route('/certificados/novo', methods=['GET', 'POST'])
@login_required
def novo_certificado():
    if request.method == 'POST':
        flash('Funcionalidade em desenvolvimento.', 'info')
        return redirect(url_for('listar_certificados'))
    return render_template('certificados/novo.html')

@app.route('/presencas/nova', methods=['GET', 'POST'])
@login_required
def nova_presenca():
    if request.method == 'POST':
        flash('Funcionalidade em desenvolvimento.', 'info')
        return redirect(url_for('listar_presencas'))
    return render_template('presencas/nova.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 