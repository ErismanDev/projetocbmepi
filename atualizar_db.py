from app import app, db

with app.app_context():
    # Remover todas as tabelas existentes
    db.drop_all()
    # Criar todas as tabelas novamente
    db.create_all()
    print("Banco de dados atualizado com sucesso!") 