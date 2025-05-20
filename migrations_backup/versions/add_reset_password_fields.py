"""add reset password fields

Revision ID: add_reset_password_fields
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_reset_password_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar campos à tabela usuario
    op.add_column('usuario', sa.Column('reset_token', sa.String(100), unique=True))
    op.add_column('usuario', sa.Column('reset_token_expires', sa.DateTime))
    op.add_column('usuario', sa.Column('ultimo_acesso', sa.DateTime))
    op.add_column('usuario', sa.Column('data_criacao', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('usuario', sa.Column('data_atualizacao', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Adicionar campos à tabela aluno
    op.add_column('aluno', sa.Column('reset_token', sa.String(100), unique=True))
    op.add_column('aluno', sa.Column('reset_token_expires', sa.DateTime))
    op.add_column('aluno', sa.Column('ultimo_acesso', sa.DateTime))
    op.add_column('aluno', sa.Column('data_criacao', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('aluno', sa.Column('data_atualizacao', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')))

def downgrade():
    # Remover campos da tabela usuario
    op.drop_column('usuario', 'reset_token')
    op.drop_column('usuario', 'reset_token_expires')
    op.drop_column('usuario', 'ultimo_acesso')
    op.drop_column('usuario', 'data_criacao')
    op.drop_column('usuario', 'data_atualizacao')

    # Remover campos da tabela aluno
    op.drop_column('aluno', 'reset_token')
    op.drop_column('aluno', 'reset_token_expires')
    op.drop_column('aluno', 'ultimo_acesso')
    op.drop_column('aluno', 'data_criacao')
    op.drop_column('aluno', 'data_atualizacao') 