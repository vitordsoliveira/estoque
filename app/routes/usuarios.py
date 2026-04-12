from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app.auth import admin_required
from app.models import Departamento, Obra, PerfilFuncional, User, db

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


def resolver_cargo_por_perfil(perfil_funcional):
    if not perfil_funcional:
        return None
    return perfil_funcional.nome


def validar_gestor_para_cargo(gestor, perfil_funcional):
    if not gestor:
        return None

    if gestor.is_admin:
        return None

    if not gestor.perfil_funcional:
        return 'O gestor selecionado precisa ter um cargo hierárquico configurado.'

    if perfil_funcional and gestor.perfil_funcional.nivel_hierarquico <= perfil_funcional.nivel_hierarquico:
        return 'O gestor selecionado precisa ter nível hierárquico superior ao cargo escolhido.'

    return None


def carregar_referencias_usuario():
    departamentos = Departamento.query.order_by(Departamento.nome.asc()).all()
    obras = Obra.query.order_by(Obra.nome.asc()).all()
    perfis = PerfilFuncional.query.order_by(PerfilFuncional.nivel_hierarquico.desc(), PerfilFuncional.nome.asc()).all()
    gestores = User.query.filter(User.active.is_(True)).order_by(User.username.asc()).all()
    return departamentos, obras, perfis, gestores


def resolver_relacao(model_class, entity_id):
    if not entity_id:
        return None
    return db.session.get(model_class, entity_id)


@usuarios.route('/gerenciar', methods=['GET'])
@admin_required
def gerenciar_usuarios():
    usuarios_cadastrados = User.query.order_by(User.username.asc()).all()
    departamentos, obras, perfis, gestores = carregar_referencias_usuario()
    return render_template(
        'gerenciar_usuarios.html',
        usuarios=usuarios_cadastrados,
        departamentos=departamentos,
        obras=obras,
        perfis=perfis,
        gestores=gestores,
    )


@usuarios.route('/cadastrar', methods=['POST'])
@admin_required
def cadastrar_usuario():
    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    ramal = normalizar_campo(request.form.get('ramal'))
    numero_corporativo = normalizar_campo(request.form.get('numero_corporativo'))
    perfil_funcional_id = request.form.get('perfil_funcional_id', type=int)
    departamento_id = request.form.get('departamento_id', type=int)
    obra_id = request.form.get('obra_id', type=int)
    gestor_id = request.form.get('gestor_id', type=int)
    active = request.form.get('active') == 'on'

    perfil_funcional = resolver_relacao(PerfilFuncional, perfil_funcional_id)
    if perfil_funcional_id and not perfil_funcional:
        flash('Perfil funcional inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if not perfil_funcional:
        flash('Selecione um cargo hierárquico para o usuário.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    departamento = resolver_relacao(Departamento, departamento_id)
    if departamento_id and not departamento:
        flash('Departamento inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    obra = resolver_relacao(Obra, obra_id)
    if obra_id and not obra:
        flash('Obra inválida.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    gestor = resolver_relacao(User, gestor_id)
    if gestor_id and (not gestor or not gestor.active):
        flash('Gestor inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    erro_hierarquia = validar_gestor_para_cargo(gestor, perfil_funcional)
    if erro_hierarquia:
        flash(erro_hierarquia, 'warning')
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
            cargo=resolver_cargo_por_perfil(perfil_funcional),
            perfil_funcional_id=perfil_funcional.id if perfil_funcional else None,
            ramal=ramal,
            numero_corporativo=numero_corporativo,
            departamento_id=departamento.id if departamento else None,
            obra_id=obra.id if obra else None,
            gestor_id=gestor.id if gestor else None,
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
    ramal = normalizar_campo(request.form.get('ramal'))
    numero_corporativo = normalizar_campo(request.form.get('numero_corporativo'))
    perfil_funcional_id = request.form.get('perfil_funcional_id', type=int)
    departamento_id = request.form.get('departamento_id', type=int)
    obra_id = request.form.get('obra_id', type=int)
    gestor_id = request.form.get('gestor_id', type=int)
    active = request.form.get('active') == 'on'

    perfil_funcional = resolver_relacao(PerfilFuncional, perfil_funcional_id)
    if perfil_funcional_id and not perfil_funcional:
        flash('Perfil funcional inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if not perfil_funcional:
        flash('Selecione um cargo hierárquico para o usuário.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    departamento = resolver_relacao(Departamento, departamento_id)
    if departamento_id and not departamento:
        flash('Departamento inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    obra = resolver_relacao(Obra, obra_id)
    if obra_id and not obra:
        flash('Obra inválida.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    if gestor_id and gestor_id == usuario.id:
        flash('O usuário não pode ser gestor dele mesmo.', 'warning')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    gestor = resolver_relacao(User, gestor_id)
    if gestor_id and (not gestor or not gestor.active):
        flash('Gestor inválido.', 'danger')
        return redirect(url_for('usuarios.gerenciar_usuarios'))

    erro_hierarquia = validar_gestor_para_cargo(gestor, perfil_funcional)
    if erro_hierarquia:
        flash(erro_hierarquia, 'warning')
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
        usuario.cargo = resolver_cargo_por_perfil(perfil_funcional)
        usuario.perfil_funcional_id = perfil_funcional.id if perfil_funcional else None
        usuario.ramal = ramal
        usuario.numero_corporativo = numero_corporativo
        usuario.departamento_id = departamento.id if departamento else None
        usuario.obra_id = obra.id if obra else None
        usuario.gestor_id = gestor.id if gestor else None
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