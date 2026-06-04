from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app.auth import admin_required
from app.models import Departamento, db

departamento = Blueprint('departamento', __name__, url_prefix='/departamento')


def buscar_departamento_por_nome(nome, exclude_id=None):
    query = Departamento.query.filter(func.lower(Departamento.nome) == nome.lower())
    if exclude_id is not None:
        query = query.filter(Departamento.id != exclude_id)
    return query.first()


@departamento.route('/gerenciar', methods=['GET'])
@admin_required
def gerenciar_departamento():
    departamentos = Departamento.query.order_by(Departamento.nome.asc()).all()
    return render_template('gerenciar_departamento.html', departamentos=departamentos)


@departamento.route('/cadastrar', methods=['POST'])
@admin_required
def cadastrar_departamento():
    nome = (request.form.get('nome') or '').strip()
    if not nome:
        flash('O nome do departamento é obrigatório.', 'warning')
        return redirect(url_for('departamento.gerenciar_departamento'))

    if buscar_departamento_por_nome(nome):
        flash('Já existe um departamento com esse nome.', 'danger')
        return redirect(url_for('departamento.gerenciar_departamento'))

    try:
        novo_departamento = Departamento(nome=nome)
        db.session.add(novo_departamento)
        db.session.commit()
        flash('Departamento cadastrado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cadastrar departamento: {exc}', 'danger')

    return redirect(url_for('departamento.gerenciar_departamento'))


@departamento.route('/editar/<int:id>', methods=['POST'])
@admin_required
def editar_departamento(id):
    departamento_obj = db.session.get(Departamento, id)
    if not departamento_obj:
        flash('Departamento não encontrado.', 'danger')
        return redirect(url_for('departamento.gerenciar_departamento'))

    nome = (request.form.get('nome') or '').strip()
    if not nome:
        flash('O nome do departamento é obrigatório.', 'warning')
        return redirect(url_for('departamento.gerenciar_departamento'))

    if buscar_departamento_por_nome(nome, exclude_id=id):
        flash('Já existe outro departamento com esse nome.', 'danger')
        return redirect(url_for('departamento.gerenciar_departamento'))

    try:
        departamento_obj.nome = nome
        db.session.commit()
        flash('Departamento atualizado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao atualizar departamento: {exc}', 'danger')

    return redirect(url_for('departamento.gerenciar_departamento'))


@departamento.route('/deletar/<int:id>', methods=['POST'])
@admin_required
def deletar_departamento(id):
    departamento_obj = db.session.get(Departamento, id)
    if not departamento_obj:
        flash('Departamento não encontrado.', 'danger')
        return redirect(url_for('departamento.gerenciar_departamento'))

    if departamento_obj.users:
        flash('Não é possível excluir um departamento com usuários vinculados.', 'warning')
        return redirect(url_for('departamento.gerenciar_departamento'))

    try:
        db.session.delete(departamento_obj)
        db.session.commit()
        flash('Departamento removido com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao remover departamento: {exc}', 'danger')

    return redirect(url_for('departamento.gerenciar_departamento'))