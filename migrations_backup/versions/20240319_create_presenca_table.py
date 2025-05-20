"""create presenca table

Revision ID: 20240319_create_presenca_table
Revises: create_diario_classe_table
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20240319_create_presenca_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('presenca',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aula_id', sa.Integer(), nullable=False),
        sa.Column('aluno_id', sa.Integer(), nullable=False),
        sa.Column('matricula_id', sa.Integer(), nullable=True),
        sa.Column('diario_id', sa.Integer(), nullable=False),
        sa.Column('presente', sa.Boolean(), nullable=False, default=False),
        sa.Column('justificativa', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['aula_id'], ['aula.id'], ),
        sa.ForeignKeyConstraint(['aluno_id'], ['aluno.id'], ),
        sa.ForeignKeyConstraint(['matricula_id'], ['matricula.id'], ),
        sa.ForeignKeyConstraint(['diario_id'], ['diario_classe.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('presenca') 