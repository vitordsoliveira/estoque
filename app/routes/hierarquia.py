from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import admin_required
from app.models import PerfilFuncional, User, db

hierarquia = Blueprint('hierarquia', __name__, url_prefix='/hierarquia')


def normalizar_texto(valor):
    texto = (valor or '').strip()
    return texto or None


def carregar_visao_hierarquia():
    perfis = PerfilFuncional.query.order_by(PerfilFuncional.nivel_hierarquico.desc(), PerfilFuncional.nome.asc()).all()
    usuarios = User.query.order_by(User.username.asc()).all()
    return perfis, usuarios


@hierarquia.route('/gerenciar')
@admin_required
def gerenciar_hierarquia():
    perfis, usuarios = carregar_visao_hierarquia()

    totais = {
        'perfis': len(perfis),
        'executores': sum(1 for usuario in usuarios if usuario.active and usuario.can_execute_balanco and not usuario.is_admin),
        'atribuidores': sum(1 for usuario in usuarios if usuario.active and usuario.can_assign_balanco and not usuario.is_admin),
    }

    return render_template('gerenciar_hierarquia.html', perfis=perfis, usuarios=usuarios, totais=totais)


@hierarquia.route('/perfis/cadastrar', methods=['POST'])
@admin_required
def cadastrar_perfil():
    nome = normalizar_texto(request.form.get('nome'))
    descricao = normalizar_texto(request.form.get('descricao'))
    nivel_hierarquico = request.form.get('nivel_hierarquico', type=int)
    pode_atribuir_balanco = request.form.get('pode_atribuir_balanco') == 'on'
    pode_executar_balanco = request.form.get('pode_executar_balanco') == 'on'
    pode_validar_balanco = request.form.get('pode_validar_balanco') == 'on'

    if not nome or nivel_hierarquico is None:
        flash('Nome e nível hierárquico são obrigatórios para o perfil funcional.', 'warning')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    if PerfilFuncional.query.filter(db.func.lower(PerfilFuncional.nome) == nome.lower()).first():
        flash('Já existe um perfil funcional com esse nome.', 'danger')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    try:
        perfil = PerfilFuncional(
            nome=nome,
            descricao=descricao,
            nivel_hierarquico=nivel_hierarquico,
            pode_atribuir_balanco=pode_atribuir_balanco,
            pode_executar_balanco=pode_executar_balanco,
            pode_validar_balanco=pode_validar_balanco,
        )
        db.session.add(perfil)
        db.session.commit()
        flash('Perfil funcional cadastrado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cadastrar perfil funcional: {exc}', 'danger')

    return redirect(url_for('hierarquia.gerenciar_hierarquia'))


@hierarquia.route('/perfis/editar/<int:id>', methods=['POST'])
@admin_required
def editar_perfil(id):
    perfil = PerfilFuncional.query.get(id)
    if not perfil:
        flash('Perfil funcional não encontrado.', 'danger')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    nome = normalizar_texto(request.form.get('nome'))
    descricao = normalizar_texto(request.form.get('descricao'))
    nivel_hierarquico = request.form.get('nivel_hierarquico', type=int)
    pode_atribuir_balanco = request.form.get('pode_atribuir_balanco') == 'on'
    pode_executar_balanco = request.form.get('pode_executar_balanco') == 'on'
    pode_validar_balanco = request.form.get('pode_validar_balanco') == 'on'

    if not nome or nivel_hierarquico is None:
        flash('Nome e nível hierárquico são obrigatórios para o perfil funcional.', 'warning')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    perfil_existente = PerfilFuncional.query.filter(
        db.func.lower(PerfilFuncional.nome) == nome.lower(),
        PerfilFuncional.id != perfil.id,
    ).first()
    if perfil_existente:
        flash('Já existe outro perfil funcional com esse nome.', 'danger')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    try:
        perfil.nome = nome
        perfil.descricao = descricao
        perfil.nivel_hierarquico = nivel_hierarquico
        perfil.pode_atribuir_balanco = pode_atribuir_balanco
        perfil.pode_executar_balanco = pode_executar_balanco
        perfil.pode_validar_balanco = pode_validar_balanco
        db.session.commit()
        flash('Perfil funcional atualizado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil funcional: {exc}', 'danger')

    return redirect(url_for('hierarquia.gerenciar_hierarquia'))


@hierarquia.route('/perfis/deletar/<int:id>', methods=['POST'])
@admin_required
def deletar_perfil(id):
    perfil = PerfilFuncional.query.get(id)
    if not perfil:
        flash('Perfil funcional não encontrado.', 'danger')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    if perfil.users:
        flash('Não é possível excluir um perfil funcional que já está vinculado a usuários.', 'warning')
        return redirect(url_for('hierarquia.gerenciar_hierarquia'))

    try:
        db.session.delete(perfil)
        db.session.commit()
        flash('Perfil funcional removido com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao remover perfil funcional: {exc}', 'danger')

    return redirect(url_for('hierarquia.gerenciar_hierarquia'))