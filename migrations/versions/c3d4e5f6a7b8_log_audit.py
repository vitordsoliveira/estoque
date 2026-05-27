"""Criar tabela log_audit

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'log_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('usuario', sa.String(150), nullable=True),
        sa.Column('papel', sa.String(100), nullable=True),
        sa.Column('ip', sa.String(60), nullable=True),
        sa.Column('so', sa.String(60), nullable=True),
        sa.Column('navegador', sa.String(80), nullable=True),
        sa.Column('aba', sa.String(100), nullable=True),
        sa.Column('acao', sa.String(150), nullable=True),
        sa.Column('detalhes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('log_audit')
