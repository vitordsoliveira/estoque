from flask import Blueprint, render_template, request

from app.auth import admin_required
from app.models import LogAudit

admin_logs = Blueprint('admin_logs', __name__, url_prefix='/admin')


@admin_logs.route('/logs')
@admin_required
def ver_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 50

    q_aba = (request.args.get('aba') or '').strip()
    q_usuario = (request.args.get('usuario') or '').strip()
    q_acao = (request.args.get('acao') or '').strip()

    query = LogAudit.query

    if q_aba:
        query = query.filter(LogAudit.aba.ilike(f'%{q_aba}%'))
    if q_usuario:
        query = query.filter(LogAudit.usuario.ilike(f'%{q_usuario}%'))
    if q_acao:
        query = query.filter(LogAudit.acao.ilike(f'%{q_acao}%'))

    paginacao = query.order_by(LogAudit.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    abas_distintas = (
        LogAudit.query
        .with_entities(LogAudit.aba)
        .distinct()
        .order_by(LogAudit.aba)
        .all()
    )
    abas = [a[0] for a in abas_distintas if a[0]]

    return render_template(
        'logs.html',
        paginacao=paginacao,
        logs=paginacao.items,
        abas=abas,
        q_aba=q_aba,
        q_usuario=q_usuario,
        q_acao=q_acao,
    )
