from app import app
from migrations.add_status_to_disciplina import upgrade, downgrade

def main():
    with app.app_context():
        print("Iniciando migração do banco de dados...")
        try:
            upgrade()
            print("Migração concluída com sucesso!")
        except Exception as e:
            print(f"Erro durante a migração: {str(e)}")
            print("Tentando fazer rollback...")
            try:
                downgrade()
                print("Rollback concluído com sucesso!")
            except Exception as e2:
                print(f"Erro durante o rollback: {str(e2)}")
                print("ATENÇÃO: O banco de dados pode estar em um estado inconsistente!")
                print("Por favor, faça um backup e restaure o banco de dados manualmente.")

if __name__ == '__main__':
    main() 