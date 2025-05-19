from flask import request, render_template, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from app.models import Matricula, Turma, Aluno
from app import db

@app.route('/matriculas/nova', methods=['GET', 'POST'])
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