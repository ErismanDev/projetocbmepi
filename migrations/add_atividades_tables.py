"""Adiciona tabelas para atividades e presenças

Revision ID: add_atividades_tables
Revises: None
Create Date: 2024-03-19
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Criar tabela categoria_atividade
    op.create_table(
        'categoria_atividade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(50), nullable=False),
        sa.Column('cor', sa.String(7), default="#007bff"),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )

    # Criar tabela atividade
    op.create_table(
        'atividade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(100), nullable=False),
        sa.Column('descricao', sa.Text),
        sa.Column('turma_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(20), default='pendente'),
        sa.Column('categoria_id', sa.Integer()),
        sa.Column('recorrente', sa.Boolean, default=False),
        sa.Column('frequencia', sa.String(20)),
        sa.Column('dias_semana', sa.String(20)),
        sa.Column('data_fim_recorrencia', sa.DateTime),
        sa.Column('notificacao_data', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['turma_id'], ['turma.id']),
        sa.ForeignKeyConstraint(['categoria_id'], ['categoria_atividade.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Criar tabela anexo_atividade
    op.create_table(
        'anexo_atividade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('atividade_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(100)),
        sa.Column('arquivo', sa.String(255)),
        sa.Column('data_upload', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['atividade_id'], ['atividade.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Criar tabela presenca
    op.create_table(
        'presenca',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aluno_id', sa.Integer(), nullable=False),
        sa.Column('turma_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('observacao', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['aluno_id'], ['aluno.id']),
        sa.ForeignKeyConstraint(['turma_id'], ['turma.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Criar tabela justificativa_presenca
    op.create_table(
        'justificativa_presenca',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('presenca_id', sa.Integer(), nullable=False),
        sa.Column('texto', sa.Text),
        sa.Column('arquivo', sa.String(255)),
        sa.Column('data_envio', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['presenca_id'], ['presenca.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('justificativa_presenca')
    op.drop_table('presenca')
    op.drop_table('anexo_atividade')
    op.drop_table('atividade')
    op.drop_table('categoria_atividade') 