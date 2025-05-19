# Sistema Bombeiro Mirim

Sistema de gerenciamento para o programa Bombeiro Mirim.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/projeto_bombeiro_mirim.git
cd projeto_bombeiro_mirim
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente:
- Crie um arquivo `.env` na raiz do projeto
- Adicione as seguintes variáveis:
```
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///bombeiro_mirim.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
```

## Executando o Sistema

1. Inicie o servidor:
```bash
python run.py
```

2. Acesse o sistema no navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

```
projeto_bombeiro_mirim/
├── app.py              # Arquivo principal da aplicação
├── config.py           # Configurações do sistema
├── requirements.txt    # Dependências do projeto
├── run.py             # Script para iniciar a aplicação
├── static/            # Arquivos estáticos (CSS, JS, imagens)
│   └── uploads/       # Pasta para uploads de arquivos
├── templates/         # Templates HTML
└── logs/             # Logs do sistema
```

## Funcionalidades

- Cadastro e gerenciamento de alunos
- Cadastro e gerenciamento de instrutores
- Cadastro e gerenciamento de cursos
- Cadastro e gerenciamento de turmas
- Registro de presença
- Gerenciamento de atividades
- Relatórios e estatísticas

## Suporte

Para suporte, entre em contato através do email: seu-email@dominio.com 