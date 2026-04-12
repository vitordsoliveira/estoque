"""Hierarquia funcional e tarefas de balanco

Revision ID: 8a1b2c3d4e5f
Revises: 29dc89214c18
Create Date: 2026-04-12 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a1b2c3d4e5f'
down_revision = '29dc89214c18'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'perfil_funcional',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('nivel_hierarquico', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('pode_atribuir_balanco', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('pode_executar_balanco', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('pode_validar_balanco', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('perfil_funcional_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('gestor_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_user_perfil_funcional', 'perfil_funcional', ['perfil_funcional_id'], ['id'])
        batch_op.create_foreign_key('fk_user_gestor', 'user', ['gestor_id'], ['id'])

    op.create_table(
        'tarefa_balanco',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=150), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('contexto', sa.String(length=80), nullable=True),
        sa.Column('tipo_operacao', sa.String(length=30), nullable=False, server_default='conferencia'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pendente'),
        sa.Column('data_referencia', sa.Date(), nullable=True),
        sa.Column('quantidade_esperada', sa.Float(), nullable=False, server_default='0'),
        sa.Column('quantidade_realizada', sa.Float(), nullable=True),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('responsavel_id', sa.Integer(), nullable=False),
        sa.Column('criado_por_id', sa.Integer(), nullable=False),
        sa.Column('corredor_destino', sa.String(length=50), nullable=True),
        sa.Column('prateleira_destino', sa.String(length=50), nullable=True),
        sa.Column('observacoes_execucao', sa.Text(), nullable=True),
        sa.Column('concluido_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['criado_por_id'], ['user.id']),
        sa.ForeignKeyConstraint(['responsavel_id'], ['user.id']),
        sa.ForeignKeyConstraint(['sku_id'], ['sku.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('tarefa_balanco')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_gestor', type_='foreignkey')
        batch_op.drop_constraint('fk_user_perfil_funcional', type_='foreignkey')
        batch_op.drop_column('gestor_id')
        batch_op.drop_column('perfil_funcional_id')

    op.drop_table('perfil_funcional')