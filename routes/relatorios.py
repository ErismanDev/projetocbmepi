import logging
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Aluno, Turma, Presenca, Certificado, Atividade, Matricula, Avaliacao
from extensions import db
from datetime import datetime, timedelta
import pandas as pd
import io
from sqlalchemy.orm import joinedload
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import os

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/relatorios')
def listar_relatorios():
    return "Lista de Relatórios"

@relatorios_bp.route('/relatorios/frequencia')
@login_required
def relatorio_frequencia():
    turma_id = request.args.get('turma_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    formato = request.args.get('formato', 'html')
    turmas = Turma.query.all()
    query = Presenca.query
    if turma_id:
        query = query.join(Aula).filter(Aula.turma_id == turma_id)
    if data_inicio:
        query = query.filter(Presenca.created_at >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        query = query.filter(Presenca.created_at <= datetime.strptime(data_fim, '%Y-%m-%d'))
    presencas = query.all()
    dados = {}
    for presenca in presencas:
        aluno = presenca.aluno
        if aluno.id not in dados:
            dados[aluno.id] = {
                'aluno': aluno.nome,
                'total_aulas': 0,
                'presencas': 0,
                'faltas': 0,
                'justificadas': 0
            }
        dados[aluno.id]['total_aulas'] += 1
        if presenca.presente:
            dados[aluno.id]['presencas'] += 1
        elif presenca.justificativa:
            dados[aluno.id]['justificadas'] += 1
        else:
            dados[aluno.id]['faltas'] += 1
    for aluno_id in dados:
        total = dados[aluno_id]['total_aulas']
        if total > 0:
            dados[aluno_id]['frequencia'] = (dados[aluno_id]['presencas'] / total) * 100
        else:
            dados[aluno_id]['frequencia'] = 0
    if formato == 'pdf':
        return gerar_pdf_frequencia(dados)
    elif formato == 'excel':
        return gerar_excel_frequencia(dados)
    elif formato == 'csv':
        return gerar_csv_frequencia(dados)
    return render_template('relatorios/frequencia.html', dados=dados, turmas=turmas)

@relatorios_bp.route('/relatorios/desempenho')
@login_required
def relatorio_desempenho():
    turma_id = request.args.get('turma_id')
    formato = request.args.get('formato', 'html')
    turmas = Turma.query.all()
    if turma_id:
        turma = Turma.query.get(turma_id)
        alunos = turma.alunos
    else:
        alunos = Aluno.query.all()
    dados = []
    for aluno in alunos:
        matriculas = Matricula.query.filter_by(aluno_id=aluno.id)
        notas = []
        for m in matriculas:
            notas += [a.nota for a in m.avaliacoes]
        media = sum(notas) / len(notas) if notas else 0
        presencas = Presenca.query.filter_by(aluno_id=aluno.id).all()
        total_aulas = len(presencas)
        presencas_count = sum(1 for p in presencas if p.presente)
        frequencia = (presencas_count / total_aulas * 100) if total_aulas > 0 else 0
        dados.append({
            'aluno': aluno.nome,
            'media': media,
            'frequencia': frequencia,
            'total_avaliacoes': len(notas),
            'status': 'Aprovado' if media >= 7 and frequencia >= 75 else 'Reprovado'
        })
    if formato == 'pdf':
        return gerar_pdf_desempenho(dados)
    elif formato == 'excel':
        return gerar_excel_desempenho(dados)
    elif formato == 'csv':
        return gerar_csv_desempenho(dados)
    return render_template('relatorios/desempenho.html', dados=dados, turmas=turmas)

@relatorios_bp.route('/relatorios/atividades')
@login_required
def relatorio_atividades():
    turma_id = request.args.get('turma_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    formato = request.args.get('formato', 'html')
    turmas = Turma.query.all()
    query = Atividade.query
    if turma_id:
        query = query.filter_by(turma_id=turma_id)
    if data_inicio:
        query = query.filter(Atividade.created_at >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        query = query.filter(Atividade.created_at <= datetime.strptime(data_fim, '%Y-%m-%d'))
    atividades = query.all()
    dados = []
    for atividade in atividades:
        dados.append({
            'titulo': atividade.titulo,
            'data': atividade.data.strftime('%d/%m/%Y'),
            'turma': atividade.turma.nome,
            'status': atividade.status,
            'participantes': len(atividade.participacoes)
        })
    if formato == 'pdf':
        return gerar_pdf_atividades(dados)
    elif formato == 'excel':
        return gerar_excel_atividades(dados)
    elif formato == 'csv':
        return gerar_csv_atividades(dados)
    return render_template('relatorios/atividades.html', dados=dados, turmas=turmas)

@relatorios_bp.route('/relatorios/certificados')
@login_required
def relatorio_certificados():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    formato = request.args.get('formato', 'html')
    query = Certificado.query
    if data_inicio:
        query = query.filter(Certificado.data_emissao >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        query = query.filter(Certificado.data_emissao <= datetime.strptime(data_fim, '%Y-%m-%d'))
    certificados = query.all()
    dados = []
    for certificado in certificados:
        dados.append({
            'codigo': certificado.codigo,
            'aluno': certificado.aluno.nome,
            'turma': certificado.turma.nome,
            'data_emissao': certificado.data_emissao.strftime('%d/%m/%Y'),
            'data_conclusao': certificado.data_conclusao.strftime('%d/%m/%Y'),
            'status': certificado.status
        })
    if formato == 'pdf':
        return gerar_pdf_certificados(dados)
    elif formato == 'excel':
        return gerar_excel_certificados(dados)
    elif formato == 'csv':
        return gerar_csv_certificados(dados)
    return render_template('relatorios/certificados.html', dados=dados)

@relatorios_bp.route('/relatorios/dashboard')
@login_required
def dashboard():
    total_alunos = Aluno.query.count()
    total_turmas = Turma.query.count()
    total_atividades = Atividade.query.count()
    total_certificados = Certificado.query.count()
    presencas = Presenca.query.all()
    total_aulas = len(presencas)
    presencas_count = sum(1 for p in presencas if p.presente)
    frequencia_media = (presencas_count / total_aulas * 100) if total_aulas > 0 else 0
    avaliacoes = [a.nota for a in Avaliacao.query.all()]
    media_geral = sum(avaliacoes) / len(avaliacoes) if avaliacoes else 0
    turmas = Turma.query.all()
    dados_turmas = []
    for turma in turmas:
        alunos_turma = len(turma.alunos)
        atividades_turma = len(turma.atividades)
        dados_turmas.append({
            'nome': turma.nome,
            'alunos': alunos_turma,
            'atividades': atividades_turma
        })
    return render_template('relatorios/dashboard.html',
                         total_alunos=total_alunos,
                         total_turmas=total_turmas,
                         total_atividades=total_atividades,
                         total_certificados=total_certificados,
                         frequencia_media=frequencia_media,
                         media_geral=media_geral,
                         dados_turmas=dados_turmas)

# Funções auxiliares para gerar relatórios em diferentes formatos
def gerar_pdf_frequencia(dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Título
    elements.append(Paragraph("Relatório de Frequência", styles['Title']))
    
    # Tabela
    data = [['Aluno', 'Total Aulas', 'Presenças', 'Faltas', 'Justificadas', 'Frequência (%)']]
    for aluno_id, info in dados.items():
        data.append([
            info['aluno'],
            str(info['total_aulas']),
            str(info['presencas']),
            str(info['faltas']),
            str(info['justificadas']),
            f"{info['frequencia']:.2f}%"
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
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='relatorio_frequencia.pdf'
    )

def gerar_excel_frequencia(dados):
    df = pd.DataFrame.from_dict(dados, orient='index')
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Frequência')
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_frequencia.xlsx'
    )

def gerar_csv_frequencia(dados):
    df = pd.DataFrame.from_dict(dados, orient='index')
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='relatorio_frequencia.csv'
    )

# Funções similares para outros tipos de relatórios... 