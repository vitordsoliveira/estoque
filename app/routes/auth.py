from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func

from app.auth import create_access_token, get_current_user, login_user, logout_user, resolve_safe_redirect_target
from app.models import User

auth = Blueprint('auth', __name__, url_prefix='/auth')


def buscar_usuario_por_email(email):
    return User.query.filter(func.lower(User.email) == email.lower()).first()


@auth.route('/login', methods=['GET', 'POST'])
def login():
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('main.index'))

    next_target = resolve_safe_redirect_target(request.values.get('next')) or ''
    email = request.form.get('email', '').strip() if request.method == 'POST' else ''

    if request.method == 'POST':
        password = request.form.get('password', '')

        if not email or not password:
            flash('Informe e-mail e senha para entrar no sistema.', 'warning')
            return render_template('login.html', next=next_target, email=email)

        user = buscar_usuario_por_email(email)
        if not user or not user.active or not user.check_password(password):
            flash('E-mail ou senha inválidos.', 'danger')
            return render_template('login.html', next=next_target, email=email)

        login_user(user)

        if not user.is_admin:
            token = create_access_token(user)
            if token:
                session['access_token'] = token

        flash('Login realizado com sucesso.', 'success')
        return redirect(next_target or url_for('main.index'))

    return render_template('login.html', next=next_target, email=email)


@auth.route('/logout', methods=['POST'])
def logout():
    logout_user()
    flash('Sessão encerrada com sucesso.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/token', methods=['POST'])
def issue_token():
    payload = request.get_json(silent=True) or request.form
    email = str(payload.get('email', '')).strip()
    password = str(payload.get('password', ''))

    if not email or not password:
        return jsonify({'error': 'E-mail e senha são obrigatórios.'}), 400

    user = buscar_usuario_por_email(email)
    if not user or not user.active or not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas.'}), 401

    if user.is_admin:
        return jsonify({'error': 'O usuário admin utiliza autenticação por sessão e não recebe JWT.'}), 400

    token = create_access_token(user)
    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_EXPIRE_MINUTES'] * 60,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'classe': user.classe
        }
    })