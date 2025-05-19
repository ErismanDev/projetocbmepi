from datetime import datetime

class Disciplina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    carga_horaria = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ativa')  # ativa, concluída, cancelada
    
    # Relacionamentos
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=False)
    curso = db.relationship('Curso', backref=db.backref('disciplinas', lazy=True))
    
    instrutor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    instrutor = db.relationship('Usuario', backref=db.backref('disciplinas_lecionadas', lazy=True))
    
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    turma = db.relationship('Turma', backref=db.backref('disciplinas', lazy=True))
    
    aulas = db.relationship('Aula', backref='disciplina', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Disciplina {self.nome}>'

class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, concluida, cancelada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    turma = db.relationship('Turma', backref=db.backref('atividades', lazy=True))

class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # presente, ausente, justificado
    observacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aluno = db.relationship('Aluno', backref=db.backref('presencas', lazy=True))
    turma = db.relationship('Turma', backref=db.backref('presencas', lazy=True))

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    nota = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aluno = db.relationship('Aluno', backref=db.backref('avaliacoes', lazy=True))
    turma = db.relationship('Turma', backref=db.backref('avaliacoes', lazy=True))

class Certificado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'), nullable=False)
    data_emissao = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, emitido, cancelado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aluno = db.relationship('Aluno', backref=db.backref('certificados', lazy=True))
    curso = db.relationship('Curso', backref=db.backref('certificados', lazy=True)) 