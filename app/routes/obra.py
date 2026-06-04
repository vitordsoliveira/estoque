from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app.auth import admin_required
from app.models import Obra, db

obra = Blueprint('obra', __name__, url_prefix='/obra')


def buscar_obra_por_nome(nome, exclude_id=None):
    query = Obra.query.filter(func.lower(Obra.nome) == nome.lower())
    if exclude_id is not None:
        query = query.filter(Obra.id != exclude_id)
    return query.first()


@obra.route('/gerenciar', methods=['GET'])
@admin_required
def gerenciar_obra():
    obras = Obra.query.order_by(Obra.nome.asc()).all()
    return render_template('gerenciar_obra.html', obras=obras)


@obra.route('/cadastrar', methods=['POST'])
@admin_required
def cadastrar_obra():
    nome = (request.form.get('nome') or '').strip()
    if not nome:
        flash('O nome da obra é obrigatório.', 'warning')
        return redirect(url_for('obra.gerenciar_obra'))

    if buscar_obra_por_nome(nome):
        flash('Já existe uma obra com esse nome.', 'danger')
        return redirect(url_for('obra.gerenciar_obra'))

    try:
        nova_obra = Obra(nome=nome)
        db.session.add(nova_obra)
        db.session.commit()
        flash('Obra cadastrada com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cadastrar obra: {exc}', 'danger')

    return redirect(url_for('obra.gerenciar_obra'))


@obra.route('/editar/<int:id>', methods=['POST'])
@admin_required
def editar_obra(id):
    obra_obj = db.session.get(Obra, id)
    if not obra_obj:
        flash('Obra não encontrada.', 'danger')
        return redirect(url_for('obra.gerenciar_obra'))

    nome = (request.form.get('nome') or '').strip()
    if not nome:
        flash('O nome da obra é obrigatório.', 'warning')
        return redirect(url_for('obra.gerenciar_obra'))

    if buscar_obra_por_nome(nome, exclude_id=id):
        flash('Já existe outra obra com esse nome.', 'danger')
        return redirect(url_for('obra.gerenciar_obra'))

    try:
        obra_obj.nome = nome
        db.session.commit()
        flash('Obra atualizada com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao atualizar obra: {exc}', 'danger')

    return redirect(url_for('obra.gerenciar_obra'))


@obra.route('/deletar/<int:id>', methods=['POST'])
@admin_required
def deletar_obra(id):
    obra_obj = db.session.get(Obra, id)
    if not obra_obj:
        flash('Obra não encontrada.', 'danger')
        return redirect(url_for('obra.gerenciar_obra'))

    if obra_obj.users:
        flash('Não é possível excluir uma obra com usuários vinculados.', 'warning')
        return redirect(url_for('obra.gerenciar_obra'))

    try:
        db.session.delete(obra_obj)
        db.session.commit()
        flash('Obra removida com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao remover obra: {exc}', 'danger')

    return redirect(url_for('obra.gerenciar_obra'))