# Funções utilitárias para o sistema Bombeiro Mirim
# Não importar db ou app diretamente para evitar importação circular
# Se necessário, importar modelos localmente dentro das funções

# Exemplo de função utilitária sem importação circular

def verificar_duplicidade_aluno(email, cpf, rg, db_session, AlunoModel):
    """
    Verifica se já existe um aluno com o mesmo email, cpf ou rg.
    Recebe a sessão do banco e o modelo Aluno como parâmetros.
    """
    return db_session.session.query(AlunoModel).filter(
        (AlunoModel.email == email) | (AlunoModel.cpf == cpf) | (AlunoModel.rg == rg)
    ).first() is not None

# Outras funções utilitárias devem seguir o mesmo padrão.

def validar_cpf(cpf):
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
        
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
        
    # Validação do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if int(cpf[9]) != digito1:
        return False
        
    # Validação do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    if int(cpf[10]) != digito2:
        return False
        
    return True

def formatar_cpf(cpf):
    """Formata CPF para o padrão XXX.XXX.XXX-XX"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

def formatar_telefone(telefone):
    """Formata telefone para o padrão (XX) XXXXX-XXXX"""
    telefone = re.sub(r'[^0-9]', '', telefone)
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    return telefone 