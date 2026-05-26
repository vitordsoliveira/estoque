"""Adicionar tabela lote_recebimento

Revision ID: b2c3d4e5f6a7
Revises: 48271f5dfe1f
Create Date: 2026-05-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = '48271f5dfe1f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lote_recebimento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo_lote', sa.String(length=50), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('quantidade_esperada', sa.Float(), nullable=False),
        sa.Column('preco_custo', sa.Float(), nullable=True),
        sa.Column('data_prevista', sa.Date(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='aguardando'),
        sa.Column('criado_por_id', sa.Integer(), nullable=False),
        sa.Column('confirmado_por_id', sa.Integer(), nullable=True),
        sa.Column('confirmado_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['sku_id'], ['sku.id']),
        sa.ForeignKeyConstraint(['criado_por_id'], ['user.id']),
        sa.ForeignKeyConstraint(['confirmado_por_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo_lote'),
    )


def downgrade():
    op.drop_table('lote_recebimento')
