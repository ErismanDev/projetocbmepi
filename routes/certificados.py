import logging
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Certificado, ModeloCertificado, Aluno, Turma
from extensions import db
from datetime import datetime
import qrcode
import io
import json
from PIL import Image, ImageDraw, ImageFont
import os
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

certificados_bp = Blueprint('certificados', __name__)

@certificados_bp.route('/certificados')
@login_required
def listar_certificados():
    try:
        page = request.args.get('page', 1, type=int)
        certificados = Certificado.query.options(
            joinedload(Certificado.aluno),
            joinedload(Certificado.turma)
        ).order_by(Certificado.data_emissao.desc()).paginate(page=page, per_page=20)
        return render_template('certificados/listar.html', certificados=certificados)
    except Exception as e:
        logging.exception('Erro ao listar certificados')
        flash('Erro ao carregar certificados.', 'danger')
        return render_template('certificados/listar.html', certificados=None)

@certificados_bp.route('/certificados/modelos')
@login_required
def listar_modelos():
    modelos = ModeloCertificado.query.all()
    return render_template('certificados/modelos.html', modelos=modelos)

@certificados_bp.route('/certificados/modelo/novo', methods=['GET', 'POST'])
@login_required
def novo_modelo():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        conteudo = request.form['conteudo']
        
        modelo = ModeloCertificado(
            nome=nome,
            descricao=descricao,
            conteudo=conteudo,
            fonte=request.form.get('fonte', 'Arial'),
            tamanho_fonte=int(request.form.get('tamanho_fonte', 24)),
            cor_texto=request.form.get('cor_texto', '#000000')
        )
        
        if 'imagem_fundo' in request.files:
            file = request.files['imagem_fundo']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/uploads/certificados', filename)
                file.save(file_path)
                modelo.imagem_fundo = file_path
        
        db.session.add(modelo)
        db.session.commit()
        
        flash('Modelo de certificado criado com sucesso!', 'success')
        return redirect(url_for('certificados.listar_modelos'))
    
    return render_template('certificados/novo_modelo.html')

@certificados_bp.route('/certificados/novo', methods=['GET', 'POST'])
@login_required
def novo_certificado():
    if request.method == 'POST':
        aluno_id = request.form.get('aluno_id')
        turma_id = request.form.get('turma_id')
        modelo_id = request.form.get('modelo_id')
        data_conclusao = request.form.get('data_conclusao')
        carga_horaria = request.form.get('carga_horaria')
        # Validação básica
        if not (aluno_id and turma_id and modelo_id and data_conclusao and carga_horaria):
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('certificados.novo_certificado'))
        try:
            aluno_id = int(aluno_id)
            turma_id = int(turma_id)
            modelo_id = int(modelo_id)
            carga_horaria = int(carga_horaria)
            data_conclusao = datetime.strptime(data_conclusao, '%Y-%m-%d')
        except Exception:
            flash('Dados inválidos.', 'danger')
            return redirect(url_for('certificados.novo_certificado'))
        certificado = Certificado(
            aluno_id=aluno_id,
            turma_id=turma_id,
            modelo_id=modelo_id,
            data_conclusao=data_conclusao,
            carga_horaria=carga_horaria
        )
        certificado.codigo = certificado.gerar_codigo()
        certificado.assinatura_digital = certificado.assinar_digitalmente()
        db.session.add(certificado)
        db.session.commit()
        # Gerar QR Code
        qr = certificado.gerar_qr_code()
        qr_path = os.path.join('static/uploads/certificados/qr', f'qr_{certificado.codigo}.png')
        qr.save(qr_path)
        flash('Certificado emitido com sucesso!', 'success')
        return redirect(url_for('certificados.listar_certificados'))
    alunos = Aluno.query.all()
    turmas = Turma.query.all()
    modelos = ModeloCertificado.query.filter_by(ativo=True).all()
    return render_template('certificados/novo.html', alunos=alunos, turmas=turmas, modelos=modelos)

@certificados_bp.route('/certificados/<int:certificado_id>/visualizar')
@login_required
def visualizar_certificado(certificado_id):
    certificado = Certificado.query.get_or_404(certificado_id)
    return render_template('certificados/visualizar.html', certificado=certificado)

@certificados_bp.route('/certificados/<int:certificado_id>/download')
@login_required
def download_certificado(certificado_id):
    certificado = Certificado.query.get_or_404(certificado_id)
    
    # Gerar imagem do certificado
    img = Image.new('RGB', (2480, 3508), color='white')
    draw = ImageDraw.Draw(img)
    
    # Carregar imagem de fundo se existir
    if certificado.modelo.imagem_fundo:
        bg = Image.open(certificado.modelo.imagem_fundo)
        img.paste(bg, (0, 0))
    
    # Adicionar texto
    font = ImageFont.truetype(certificado.modelo.fonte, certificado.modelo.tamanho_fonte)
    texto = certificado.modelo.conteudo.format(
        aluno=certificado.aluno.nome,
        turma=certificado.turma.nome,
        data=certificado.data_conclusao.strftime('%d/%m/%Y'),
        carga_horaria=certificado.carga_horaria
    )
    
    # Adicionar QR Code
    qr = certificado.gerar_qr_code()
    qr_path = os.path.join('static/uploads/certificados/qr', f'qr_{certificado.codigo}.png')
    qr_img = Image.open(qr_path)
    img.paste(qr_img, (2000, 3000))
    
    # Salvar em buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PDF')
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'certificado_{certificado.codigo}.pdf'
    )

@certificados_bp.route('/certificados/verificar/<codigo>')
def verificar_certificado(codigo):
    certificado = Certificado.query.filter_by(codigo=codigo).first_or_404()
    return render_template('certificados/verificar.html', certificado=certificado)

@certificados_bp.route('/certificados/turma/<int:turma_id>/emitir_lote', methods=['POST'])
@login_required
def emitir_lote_certificados(turma_id):
    turma = Turma.query.get_or_404(turma_id)
    modelo_id = request.form['modelo_id']
    data_conclusao = datetime.strptime(request.form['data_conclusao'], '%Y-%m-%d')
    carga_horaria = int(request.form['carga_horaria'])
    
    for aluno in turma.alunos:
        certificado = Certificado(
            aluno_id=aluno.id,
            turma_id=turma_id,
            modelo_id=modelo_id,
            data_conclusao=data_conclusao,
            carga_horaria=carga_horaria
        )
        
        certificado.codigo = certificado.gerar_codigo()
        certificado.assinatura_digital = certificado.assinar_digitalmente()
        
        db.session.add(certificado)
        
        # Gerar QR Code
        qr = certificado.gerar_qr_code()
        qr_path = os.path.join('static/uploads/certificados/qr', f'qr_{certificado.codigo}.png')
        qr.save(qr_path)
    
    db.session.commit()
    flash('Certificados emitidos em lote com sucesso!', 'success')
    return redirect(url_for('certificados.listar_certificados'))

@certificados_bp.route('/certificados/<int:certificado_id>/reenviar', methods=['POST'])
@login_required
def reenviar_certificado(certificado_id):
    certificado = Certificado.query.get_or_404(certificado_id)
    
    # Aqui você pode implementar o envio por e-mail
    # Por exemplo, usando Flask-Mail
    
    flash('Certificado reenviado com sucesso!', 'success')
    return redirect(url_for('certificados.listar_certificados')) 