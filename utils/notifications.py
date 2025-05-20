from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Message
from models import Atividade, Presenca, Aluno, Turma
from extensions import db, mail

def verificar_atividades_proximas():
    """Verifica atividades próximas do prazo e envia notificações"""
    hoje = datetime.now()
    amanha = hoje + timedelta(days=1)
    proxima_semana = hoje + timedelta(days=7)
    
    # Buscar atividades próximas
    atividades = Atividade.query.filter(
        Atividade.data.between(amanha, proxima_semana),
        Atividade.status == 'pendente'
    ).all()
    
    for atividade in atividades:
        # Se a data de notificação ainda não foi definida ou já passou
        if not atividade.notificacao_data or atividade.notificacao_data < hoje:
            enviar_notificacao_atividade(atividade)
            atividade.notificacao_data = hoje
            db.session.commit()

def verificar_baixa_frequencia():
    """Verifica alunos com baixa frequência e envia alertas"""
    turmas = Turma.query.all()
    
    for turma in turmas:
        alunos = Aluno.query.all()  # Ajustar para pegar apenas alunos da turma
        
        for aluno in alunos:
            # Calcular frequência
            total_presencas = Presenca.query.filter_by(
                aluno_id=aluno.id,
                turma_id=turma.id,
                status='presente'
            ).count()
            
            total_aulas = Presenca.query.filter_by(
                aluno_id=aluno.id,
                turma_id=turma.id
            ).count()
            
            if total_aulas > 0:
                frequencia = (total_presencas / total_aulas) * 100
                
                # Se frequência abaixo de 75%, enviar alerta
                if frequencia < 75:
                    enviar_alerta_frequencia(aluno, turma, frequencia)

def enviar_notificacao_atividade(atividade):
    """Envia notificação sobre atividade próxima"""
    assunto = f'Lembrete: Atividade {atividade.titulo}'
    corpo = f"""
    Olá!

    A atividade "{atividade.titulo}" está programada para {atividade.data.strftime('%d/%m/%Y')}.

    Descrição: {atividade.descricao}

    Não se esqueça de participar!

    Atenciosamente,
    Equipe Bombeiro Mirim
    """
    
    # Enviar para todos os alunos da turma
    alunos = Aluno.query.all()  # Ajustar para pegar apenas alunos da turma
    
    for aluno in alunos:
        msg = Message(
            assunto,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[aluno.email]
        )
        msg.body = corpo
        mail.send(msg)

def enviar_alerta_frequencia(aluno, turma, frequencia):
    """Envia alerta sobre baixa frequência"""
    assunto = f'Alerta de Frequência - {turma.nome}'
    corpo = f"""
    Prezado(a) {aluno.responsavel},

    Informamos que o(a) aluno(a) {aluno.nome} está com frequência abaixo do mínimo exigido 
    na turma {turma.nome}.

    Frequência atual: {frequencia:.2f}%
    Frequência mínima exigida: 75%

    Por favor, entre em contato com a coordenação para regularizar a situação.

    Atenciosamente,
    Equipe Bombeiro Mirim
    """
    
    # Enviar para o responsável
    msg = Message(
        assunto,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[aluno.email]  # Considerar adicionar campo email_responsavel
    )
    msg.body = corpo
    mail.send(msg)

def agendar_verificacoes():
    """
    Agenda verificações periódicas para o sistema
    """
    pass 