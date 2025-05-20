from datetime import datetime
import random
import string
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from extensions import db
import qrcode
import json
import hashlib

# Tabelas associativas
aluno_turma = db.Table('aluno_turma',
    db.Column('aluno_id', db.Integer, db.ForeignKey('aluno.id'), primary_key=True),
    db.Column('turma_id', db.Integer, db.ForeignKey('turma.id'), primary_key=True),
    db.Column('data_matricula', db.DateTime, default=datetime.now)
)

turma_disciplina = db.Table('turma_disciplina',
    db.Column('turma_id', db.Integer, db.ForeignKey('turma.id'), primary_key=True),
    db.Column('disciplina_id', db.Integer, db.ForeignKey('disciplina.id'), primary_key=True),
    db.Column('data_inicio', db.Date),
    db.Column('data_fim', db.Date)
)

# MODELOS PRINCIPAIS
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # admin, instrutor
    status = db.Column(db.String(20), default='ativo')
    foto = db.Column(db.String(200))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime)
    ultimo_acesso = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    documentos = db.Column(db.Text, default='[]')
    # Relacionamentos
    turmas = db.relationship('Turma', backref='instrutor', lazy=True)
    disciplinas_lecionadas = db.relationship('Disciplina', backref='instrutor', lazy=True)
    aulas_ministradas = db.relationship('Aula', backref='instrutor', lazy=True)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def gerar_senha(self):
        senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.senha_hash = generate_password_hash(senha)
        return senha

class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    idade = db.Column(db.Integer)
    responsavel = db.Column(db.String(100), nullable=False)
    contato = db.Column(db.String(20), nullable=False)
    contato_emergencia = db.Column(db.String(20), nullable=False)
    tipo_sanguineo = db.Column(db.String(5))
    status = db.Column(db.String(20), default='ativo')
    foto = db.Column(db.String(200))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime)
    ultimo_acesso = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    documentos = db.Column(db.Text, default='[]')
    # Relacionamentos
    turmas = db.relationship('Turma', secondary=aluno_turma, backref=db.backref('alunos', lazy='dynamic'))
    presencas = db.relationship('Presenca', backref='aluno', lazy=True)
    matriculas = db.relationship('Matricula', backref='aluno', lazy=True)
    participacoes = db.relationship('Participacao', backref='aluno', lazy=True)
    certificados = db.relationship('Certificado', backref='aluno', lazy=True)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def gerar_senha(self):
        senha = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.senha_hash = generate_password_hash(senha)
        return senha

class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    horario_inicio_manha = db.Column(db.String(5), nullable=True)
    horario_fim_manha = db.Column(db.String(5), nullable=True)
    horario_inicio_tarde = db.Column(db.String(5), nullable=True)
    horario_fim_tarde = db.Column(db.String(5), nullable=True)
    turno = db.Column(db.String(20), nullable=False, default='manha')
    local = db.Column(db.String(200), nullable=False)
    vagas = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ativa')
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    disciplinas = db.relationship('Disciplina', secondary=turma_disciplina, backref=db.backref('turmas', lazy='dynamic'))
    atividades = db.relationship('Atividade', backref='turma', lazy=True)
    aulas = db.relationship('Aula', backref='turma', lazy=True)
    matriculas = db.relationship('Matricula', backref='turma', lazy=True)
    certificados = db.relationship('Certificado', backref='turma', lazy=True)

class Disciplina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    carga_horaria = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ativa')
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=True)
    aulas = db.relationship('Aula', backref='disciplina', lazy=True, cascade='all, delete-orphan')

class Aula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    disciplina_id = db.Column(db.Integer, db.ForeignKey('disciplina.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='realizada')
    created_at = db.Column(db.DateTime, default=datetime.now)
    presencas = db.relationship('Presenca', backref='aula', cascade='all, delete-orphan')

class Matricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    data_matricula = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='ativa')
    observacoes = db.Column(db.Text)
    presencas = db.relationship('Presenca', backref='matricula', lazy=True)
    avaliacoes = db.relationship('Avaliacao', backref='matricula', lazy=True)

class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    matricula_id = db.Column(db.Integer, db.ForeignKey('matricula.id'), nullable=True)
    presente = db.Column(db.Boolean, default=False)
    justificativa = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pendente')
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    participacoes = db.relationship('Participacao', backref='atividade', lazy=True)

class Participacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividade.id'), nullable=False)
    presente = db.Column(db.Boolean, default=False)
    observacao = db.Column(db.Text)

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula_id = db.Column(db.Integer, db.ForeignKey('matricula.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    nota = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    observacoes = db.Column(db.Text)

class ModeloCertificado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    conteudo = db.Column(db.Text, nullable=False)
    imagem_fundo = db.Column(db.String(255))
    posicao_texto = db.Column(db.String(50))
    fonte = db.Column(db.String(50))
    tamanho_fonte = db.Column(db.Integer)
    cor_texto = db.Column(db.String(7))
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    certificados = db.relationship('Certificado', backref='modelo', lazy=True)

class Certificado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    modelo_id = db.Column(db.Integer, db.ForeignKey('modelo_certificado.id'), nullable=False)
    data_emissao = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_conclusao = db.Column(db.Date, nullable=False)
    carga_horaria = db.Column(db.Integer, nullable=False)
    assinatura_digital = db.Column(db.String(255))
    status = db.Column(db.String(20), default='emitido')
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def gerar_codigo(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"CERT-{timestamp}-{random_str}"

    def gerar_qr_code(self):
        dados = {
            'id': self.id,
            'codigo': self.codigo,
            'aluno': self.aluno.nome,
            'turma': self.turma.nome,
            'data_emissao': self.data_emissao.isoformat(),
            'assinatura': self.assinatura_digital
        }
        return qrcode.make(json.dumps(dados))

    def assinar_digitalmente(self):
        dados = f"{self.id}{self.codigo}{self.aluno_id}{self.turma_id}{self.data_emissao}"
        return hashlib.sha256(dados.encode()).hexdigest()

class Curso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    carga_horaria = db.Column(db.Integer, nullable=False)
    duracao = db.Column(db.Integer, nullable=False)
    requisitos = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativo')
    observacoes = db.Column(db.Text)
    turmas = db.relationship('Turma', backref='curso', lazy=True)
    disciplinas = db.relationship('Disciplina', backref='curso', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# Outras classes auxiliares (CategoriaAtividade, AnexoAtividade, JustificativaPresenca, etc) podem ser adicionadas conforme necessário. 