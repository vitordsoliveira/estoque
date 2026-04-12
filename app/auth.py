from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlsplit

import jwt
from flask import current_app, flash, g, redirect, request, session, url_for

from app.models import User, db


def is_public_endpoint(endpoint):
    return endpoint == 'static' or endpoint.startswith('auth.')


def get_current_request_path():
    caminho = request.path or '/'
    if request.query_string:
        caminho = f"{caminho}?{request.query_string.decode('utf-8')}"
    return caminho


def resolve_safe_redirect_target(target):
    if not target:
        return None

    destino = urlsplit(target)
    if destino.netloc and destino.netloc != request.host:
        return None

    caminho = destino.path or url_for('main.index')
    if destino.query:
        caminho = f'{caminho}?{destino.query}'

    return caminho


def get_current_user():
    if hasattr(g, '_auth_user_loaded'):
        return g.current_user

    g._auth_user_loaded = True
    g.current_user = None

    user_id = session.get('user_id')
    if not user_id:
        return None

    user = db.session.get(User, user_id)
    if not user or not user.active:
        session.clear()
        return None

    g.current_user = user
    return user


def login_user(user):
    session.clear()
    session.permanent = True
    session['user_id'] = user.id
    session['user_email'] = user.email
    session['user_role'] = user.classe or 'user'


def logout_user():
    session.clear()


def create_access_token(user):
    if user.is_admin:
        return None

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=current_app.config['JWT_EXPIRE_MINUTES'])
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'username': user.username,
        'role': user.classe or 'user',
        'iat': int(issued_at.timestamp()),
        'exp': int(expires_at.timestamp())
    }

    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )


def decode_access_token(token):
    return jwt.decode(
        token,
        current_app.config['JWT_SECRET_KEY'],
        algorithms=[current_app.config['JWT_ALGORITHM']]
    )


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for('auth.login', next=get_current_request_path()))
        return view_func(*args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('auth.login', next=get_current_request_path()))

        if not current_user.is_admin:
            flash('Acesso restrito ao administrador.', 'danger')
            return redirect(url_for('main.index'))

        return view_func(*args, **kwargs)

    return wrapped_view


def register_auth_hooks(app):
    @app.before_request
    def enforce_login():
        endpoint = request.endpoint or ''
        if not endpoint:
            return None

        current_user = get_current_user()

        if endpoint == 'auth.login' and current_user:
            return redirect(url_for('main.index'))

        if is_public_endpoint(endpoint):
            return None

        if current_user:
            return None

        return redirect(url_for('auth.login', next=get_current_request_path()))

    @app.context_processor
    def inject_current_user():
        return {'current_user': get_current_user()}