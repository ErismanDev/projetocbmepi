from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from ..models import Atividade, Presenca, Aluno, Turma
from ..extensions import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

atividades_bp = Blueprint('atividades', __name__)

UPLOAD_FOLDER = 'static/uploads/anexos'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@atividades_bp.route('/atividades')
@login_required
def listar_atividades():
    atividades = Atividade.query.all()
    categorias = CategoriaAtividade.query.all()
    return render_template('atividades/listar.html', atividades=atividades, categorias=categorias)

@atividades_bp.route('/atividades/nova', methods=['GET', 'POST'])
@login_required
def nova_atividade():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        turma_id = request.form['turma_id']
        data = datetime.strptime(request.form['data'], '%Y-%m-%d')
        categoria_id = request.form.get('categoria_id')
        recorrente = 'recorrente' in request.form
        
        atividade = Atividade(
            titulo=titulo,
            descricao=descricao,
            turma_id=turma_id,
            data=data,
            categoria_id=categoria_id,
            recorrente=recorrente
        )
        
        if recorrente:
            atividade.frequencia = request.form.get('frequencia')
            atividade.dias_semana = ','.join(request.form.getlist('dias_semana'))
            atividade.data_fim_recorrencia = datetime.strptime(request.form['data_fim_recorrencia'], '%Y-%m-%d')
        
        db.session.add(atividade)
        db.session.commit()
        
        # Processar anexos
        if 'anexos' in request.files:
            files = request.files.getlist('anexos')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    
                    anexo = AnexoAtividade(
                        atividade_id=atividade.id,
                        nome=filename,
                        arquivo=file_path
                    )
                    db.session.add(anexo)
            
            db.session.commit()
        
        flash('Atividade criada com sucesso!', 'success')
        return redirect(url_for('atividades.listar_atividades'))
    
    turmas = Turma.query.all()
    categorias = CategoriaAtividade.query.all()
    return render_template('atividades/nova.html', turmas=turmas, categorias=categorias)

@atividades_bp.route('/atividades/calendario')
@login_required
def calendario():
    return render_template('atividades/calendario.html')

@atividades_bp.route('/api/eventos')
@login_required
def get_eventos():
    atividades = Atividade.query.all()
    eventos = []
    
    for atividade in atividades:
        cor = atividade.categoria.cor if atividade.categoria else '#007bff'
        evento = {
            'id': atividade.id,
            'title': atividade.titulo,
            'start': atividade.data.isoformat(),
            'backgroundColor': cor,
            'extendedProps': {
                'descricao': atividade.descricao,
                'status': atividade.status
            }
        }
        eventos.append(evento)
    
    return jsonify(eventos)

@atividades_bp.route('/presenca/registrar/<int:turma_id>', methods=['GET', 'POST'])
@login_required
def registrar_presenca(turma_id):
    if request.method == 'POST':
        data = datetime.strptime(request.form['data'], '%Y-%m-%d')
        alunos = request.form.getlist('alunos[]')
        presencas = request.form.getlist('presencas[]')
        
        for aluno_id, status in zip(alunos, presencas):
            presenca = Presenca(
                aluno_id=aluno_id,
                turma_id=turma_id,
                data=data,
                status=status
            )
            db.session.add(presenca)
        
        db.session.commit()
        flash('Presenças registradas com sucesso!', 'success')
        return redirect(url_for('atividades.listar_presencas', turma_id=turma_id))
    
    turma = Turma.query.get_or_404(turma_id)
    alunos = Aluno.query.all()  # Ajuste conforme necessário para filtrar alunos da turma
    return render_template('atividades/registrar_presenca.html', turma=turma, alunos=alunos)

@atividades_bp.route('/presenca/justificar/<int:presenca_id>', methods=['POST'])
@login_required
def justificar_presenca(presenca_id):
    presenca = Presenca.query.get_or_404(presenca_id)
    
    justificativa = JustificativaPresenca(
        presenca_id=presenca_id,
        texto=request.form['justificativa']
    )
    
    if 'arquivo' in request.files:
        file = request.files['arquivo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/uploads/justificativas', filename)
            file.save(file_path)
            justificativa.arquivo = file_path
    
    presenca.status = 'justificado'
    db.session.add(justificativa)
    db.session.commit()
    
    flash('Justificativa registrada com sucesso!', 'success')
    return redirect(url_for('atividades.listar_presencas', turma_id=presenca.turma_id))

@atividades_bp.route('/relatorios/frequencia/<int:turma_id>')
@login_required
def relatorio_frequencia(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    alunos = Aluno.query.all()  # Ajuste conforme necessário
    
    # Calcular estatísticas de frequência
    estatisticas = []
    for aluno in alunos:
        total_presencas = Presenca.query.filter_by(
            aluno_id=aluno.id,
            turma_id=turma_id,
            status='presente'
        ).count()
        
        total_aulas = Presenca.query.filter_by(
            aluno_id=aluno.id,
            turma_id=turma_id
        ).count()
        
        if total_aulas > 0:
            frequencia = (total_presencas / total_aulas) * 100
        else:
            frequencia = 0
            
        estatisticas.append({
            'aluno': aluno,
            'presencas': total_presencas,
            'total_aulas': total_aulas,
            'frequencia': frequencia
        })
    
    return render_template('atividades/relatorio_frequencia.html', 
                         turma=turma, 
                         estatisticas=estatisticas) 