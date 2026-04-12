from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app.auth import admin_required
from app.models import Departamento, Obra, User, db

usuarios = Blueprint('usuarios', __name__, url_prefix='/usuarios')


def buscar_usuario_por_email(email, exclude_id=None):
    query = User.query.filter(func.lower(User.email) == email.lower())
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first()


def buscar_usuario_por_username(username, exclude_id=None):
    query = User.query.filter(func.lower(User.username) == username.lower())
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first()


def normalizar_campo(value):
    value = (value or '').strip()
    return value or None


def carregar_referencias_usuario():
    departamentos = Departamento.query.order_by(Departamento.nome.asc()).all()
    obras = Obra.query.order_by(Obra.nome.asc()).all()
    return departamentos, obras


def resolver_relacao(model_class, entity_id):
    if not entity_id:
        return None
    return db.session.get(model_class, entity_id)


@usuarios.route('/gerenciar', methods=['GET'])
@admin_required
def gerenciar_usuarios():
    usuarios_cadastrados = User.query.order_by(User.username.asc()).all()
    departamentos, obras = carregar_referencias_usuario()
    return render_template(
        'gerenciar_usuarios.html',
        usuarios=usuarios_cadastrados,
        departamentos=departamentos,
        obras=obras,
    )


@usuarios.route('/cadastrar', methods=['POST'])
@admin_required
def cadastrar_usuario():
    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    cargo = normalizar_campo(request.form.get('cargo'))
    ramal = normalizar_campo(request.form.get('ramal'))
    numero_corporativo = normalizar_campo(request.form.get('numero_corporativo'))
    departamento_id = request.form.get('departamento_id', type=int)
    obra_id = request.form.get('obra_id', type=int)
    active = request.form.get('active') == 'on'

    departamento = resolver_relacao(Departamento, departamento_id)
    if departamento_id and not departamento:
        flash('Departamento inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    obra = resolver_relacao(Obra, obra_id)
    if obra_id and not obra:
        flash('Obra inválida.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if not username or not email or not password:
        flash('Nome, e-mail e senha são obrigatórios.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if len(password) < 8:
        flash('A senha do usuário deve ter ao menos 8 caracteres.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if buscar_usuario_por_username(username):
        flash('Já existe um usuário com esse nome.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if buscar_usuario_por_email(email):
        flash('Já existe um usuário com esse e-mail.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    try:
        novo_usuario = User(
            username=username,
            email=email,
            classe='user',
            cargo=cargo,
            ramal=ramal,
            numero_corporativo=numero_corporativo,
            departamento_id=departamento.id if departamento else None,
            obra_id=obra.id if obra else None,
            active=active,
            first_login_completed=True
        )
        novo_usuario.set_password(password)

        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cadastrar usuário: {exc}', 'danger')

    return redirect(url_for('usuarios.gerenciar_usuarios'))


@usuarios.route('/editar/<int:id>', methods=['POST'])
@admin_required
def editar_usuario(id):
    usuario = User.query.get(id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if usuario.is_admin:
        flash('O usuário admin fixo é gerenciado pela seed e não pode ser alterado aqui.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    cargo = normalizar_campo(request.form.get('cargo'))
    ramal = normalizar_campo(request.form.get('ramal'))
    numero_corporativo = normalizar_campo(request.form.get('numero_corporativo'))
    departamento_id = request.form.get('departamento_id', type=int)
    obra_id = request.form.get('obra_id', type=int)
    active = request.form.get('active') == 'on'

    departamento = resolver_relacao(Departamento, departamento_id)
    if departamento_id and not departamento:
        flash('Departamento inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    obra = resolver_relacao(Obra, obra_id)
    if obra_id and not obra:
        flash('Obra inválida.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if not username or not email:
        flash('Nome e e-mail são obrigatórios.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if password and len(password) < 8:
        flash('A nova senha deve ter ao menos 8 caracteres.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if buscar_usuario_por_username(username, exclude_id=usuario.id):
        flash('Já existe outro usuário com esse nome.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if buscar_usuario_por_email(email, exclude_id=usuario.id):
        flash('Já existe outro usuário com esse e-mail.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    try:
        usuario.username = username
        usuario.email = email
        usuario.cargo = cargo
        usuario.ramal = ramal
        usuario.numero_corporativo = numero_corporativo
        usuario.departamento_id = departamento.id if departamento else None
        usuario.obra_id = obra.id if obra else None
        usuario.active = active
        usuario.first_login_completed = True

        if password:
            usuario.set_password(password)

        db.session.commit()
        flash('Usuário atualizado com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao atualizar usuário: {exc}', 'danger')

    return redirect(url_for('usuarios.gerenciar_usuarios'))