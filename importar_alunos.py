import pandas as pd
from app import app, db
from models import Aluno
from utils import verificar_duplicidade_aluno, formatar_cpf, formatar_telefone
from datetime import datetime
import json
from flask_mail import Message
from app import mail

def importar_alunos(arquivo_excel):
    """
    Importa alunos de um arquivo Excel
    O arquivo deve ter as seguintes colunas:
    - nome
    - email
    - cpf
    - rg
    - data_nascimento (formato: DD/MM/YYYY)
    - responsavel
    - contato
    - contato_emergencia
    - tipo_sanguineo
    """
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(arquivo_excel)
        
        # Lista para armazenar erros
        erros = []
        alunos_importados = []
        
        # Processa cada linha
        for index, row in df.iterrows():
            try:
                # Verifica duplicidade
                erros_duplicidade = verificar_duplicidade_aluno(
                    cpf=row['cpf'],
                    email=row['email'],
                    rg=row['rg']
                )
                
                if erros_duplicidade:
                    erros.append(f"Linha {index + 2}: {'; '.join(erros_duplicidade)}")
                    continue
                
                # Formata data de nascimento
                try:
                    data_nascimento = datetime.strptime(row['data_nascimento'], '%d/%m/%Y')
                except:
                    erros.append(f"Linha {index + 2}: Data de nascimento inválida")
                    continue
                
                # Cria novo aluno
                aluno = Aluno(
                    nome=row['nome'],
                    email=row['email'],
                    cpf=formatar_cpf(row['cpf']),
                    rg=row['rg'],
                    data_nascimento=data_nascimento,
                    responsavel=row['responsavel'],
                    contato=formatar_telefone(row['contato']),
                    contato_emergencia=formatar_telefone(row['contato_emergencia']),
                    tipo_sanguineo=row.get('tipo_sanguineo', '')
                )
                
                # Gera senha aleatória
                senha = aluno.gerar_senha()
                
                # Adiciona à lista de alunos importados
                alunos_importados.append({
                    'aluno': aluno,
                    'senha': senha
                })
                
            except Exception as e:
                erros.append(f"Linha {index + 2}: {str(e)}")
        
        # Se não houver erros, salva os alunos
        if not erros:
            for item in alunos_importados:
                db.session.add(item['aluno'])
            db.session.commit()
            
            # Envia emails com senhas
            for item in alunos_importados:
                msg = Message(
                    'Bem-vindo ao Sistema Bombeiro Mirim',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[item['aluno'].email]
                )
                msg.body = f"""
                Olá {item['aluno'].nome},
                
                Seu cadastro foi realizado com sucesso!
                
                Suas credenciais de acesso são:
                Email: {item['aluno'].email}
                Senha: {item['senha']}
                
                Por favor, altere sua senha no primeiro acesso.
                
                Atenciosamente,
                Equipe Bombeiro Mirim
                """
                mail.send(msg)
            
            return True, f"{len(alunos_importados)} alunos importados com sucesso!"
        else:
            return False, "\n".join(erros)
            
    except Exception as e:
        return False, f"Erro ao processar arquivo: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        sucesso, mensagem = importar_alunos('alunos.xlsx')
        print(mensagem) 