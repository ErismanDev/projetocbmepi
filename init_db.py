from app import app, db
from models import Usuario, Aluno, Atividade, Participacao, Curso, Turma, Disciplina, Presenca, Avaliacao, Certificado
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
import json
import sqlite3

def init_db():
    with app.app_context():
        # Cria todas as tabelas
        db.create_all()

        # Cria ou atualiza usuário admin
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
        else:
            admin.senha_hash = generate_password_hash('admin123')
            admin.tipo = 'admin'
            admin.nome = 'Administrador'

        # Cria um instrutor de exemplo
        if not Usuario.query.filter_by(email='instrutor@bombeiromirim.com').first():
            instrutor = Usuario(
                nome='Instrutor Exemplo',
                email='instrutor@bombeiromirim.com',
                senha_hash=generate_password_hash('instrutor123'),
                tipo='instrutor'
            )
            db.session.add(instrutor)

        # Cria um curso de exemplo
        if not Curso.query.filter_by(nome='Bombeiro Mirim - Turma 2024').first():
            curso = Curso(
                nome='Bombeiro Mirim - Turma 2024',
                descricao='Curso básico de formação de Bombeiro Mirim',
                carga_horaria=120,
                duracao=6,  # Duração em meses
                status='ativo'
            )
            db.session.add(curso)

        # Commit das alterações
        db.session.commit()
        print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()

# Migração manual de campos extras
def migrate_db():
    db_path = 'bombeiro_mirim.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Adiciona o campo para alunos, se não existir
    try:
        c.execute("ALTER TABLE aluno ADD COLUMN documentos TEXT DEFAULT '[]'")
        print("Campo 'documentos' adicionado na tabela 'aluno'.")
    except Exception as e:
        print("Campo 'documentos' já existe em 'aluno' ou erro:", e)

    # Adiciona o campo para instrutores/usuários, se não existir
    try:
        c.execute("ALTER TABLE usuario ADD COLUMN documentos TEXT DEFAULT '[]'")
        print("Campo 'documentos' adicionado na tabela 'usuario'.")
    except Exception as e:
        print("Campo 'documentos' já existe em 'usuario' ou erro:", e)

    conn.commit()
    conn.close()
    print("Migração concluída! Seu banco está pronto para os novos recursos de documentos.")

if __name__ == '__main__':
    init_db()
    migrate_db()

conn = sqlite3.connect('bombeiro_mirim.db')
c = conn.cursor()
c.execute("PRAGMA table_info(aluno)")
print(c.fetchall())
conn.close()

print(Usuario.query.all()) 