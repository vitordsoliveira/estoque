import io
from datetime import datetime

import qrcode
from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from qrcode.image.svg import SvgPathImage

from app.auth import functional_permission_required, get_current_user, login_required
from app.models import LoteRecebimento, Produto, Sku, db
from app.number_utils import parse_decimal_input

recebimento = Blueprint('recebimento', __name__, url_prefix='/recebimento')


def _normalizar(valor):
    texto = (valor or '').strip()
    return texto or None


def gerar_codigo_lote():
    from datetime import date
    hoje = date.today().strftime('%Y%m%d')
    prefixo = f'LOTE-{hoje}-'
    ultimo = (
        LoteRecebimento.query
        .filter(LoteRecebimento.codigo_lote.like(f'{prefixo}%'))
        .order_by(LoteRecebimento.id.desc())
        .first()
    )
    seq = 1
    if ultimo:
        try:
            seq = int(ultimo.codigo_lote.rsplit('-', 1)[-1]) + 1
        except ValueError:
            pass
    return f'{prefixo}{seq:04d}'


def gerar_svg_qrcode_lote(lote):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(lote.codigo_lote)
    qr.make(fit=True)
    imagem = qr.make_image(image_factory=SvgPathImage)
    buf = io.BytesIO()
    imagem.save(buf)
    return buf.getvalue()


def _redirect(codigo_lote=None):
    if codigo_lote:
        return redirect(url_for('recebimento.gerenciar_recebimento', lote=codigo_lote))
    return redirect(url_for('recebimento.gerenciar_recebimento'))


@recebimento.route('/gerenciar')
@login_required
def gerenciar_recebimento():
    current_user = get_current_user()
    codigo_lote = (request.args.get('lote') or '').strip().upper()

    lote_lido = None
    if codigo_lote:
        lote_lido = LoteRecebimento.query.filter_by(codigo_lote=codigo_lote).first()
        if not lote_lido:
            flash(f'Lote "{codigo_lote}" não encontrado.', 'danger')

    lotes_pendentes = (
        LoteRecebimento.query
        .filter_by(status='aguardando')
        .order_by(LoteRecebimento.created_at.desc())
        .all()
    )
    skus_disponiveis = Sku.query.order_by(Sku.codigo).all()

    from datetime import date
    hoje = date.today()
    confirmados_hoje = LoteRecebimento.query.filter(
        LoteRecebimento.status == 'confirmado',
        db.func.date(LoteRecebimento.confirmado_em) == hoje,
    ).count()

    return render_template(
        'gerenciar_recebimento.html',
        current_user=current_user,
        lote_lido=lote_lido,
        lotes_pendentes=lotes_pendentes,
        skus_disponiveis=skus_disponiveis,
        codigo_lote=codigo_lote,
        total_aguardando=len(lotes_pendentes),
        confirmados_hoje=confirmados_hoje,
    )


@recebimento.route('/cadastrar', methods=['POST'])
@functional_permission_required('can_assign_balanco', 'Seu papel não permite criar provisões de lote.')
def cadastrar_lote():
    current_user = get_current_user()
    sku_id = request.form.get('sku_id', type=int)
    sku = db.session.get(Sku, sku_id)
    if not sku:
        flash('Selecione um SKU válido.', 'warning')
        return _redirect()

    try:
        quantidade_esperada = parse_decimal_input(request.form.get('quantidade_esperada'))
        preco_raw = request.form.get('preco_custo')
        preco_custo = parse_decimal_input(preco_raw) if preco_raw else None
        data_raw = (request.form.get('data_prevista') or '').strip()
        data_prevista = datetime.strptime(data_raw, '%Y-%m-%d').date() if data_raw else None
    except ValueError as exc:
        flash(str(exc), 'danger')
        return _redirect()

    if not quantidade_esperada or quantidade_esperada <= 0:
        flash('A quantidade esperada precisa ser maior que zero.', 'warning')
        return _redirect()

    observacoes = _normalizar(request.form.get('observacoes'))

    try:
        lote = LoteRecebimento(
            codigo_lote=gerar_codigo_lote(),
            sku_id=sku.id,
            quantidade_esperada=quantidade_esperada,
            preco_custo=preco_custo,
            data_prevista=data_prevista,
            observacoes=observacoes,
            status='aguardando',
            criado_por_id=current_user.id,
        )
        db.session.add(lote)
        db.session.commit()
        flash(f'Lote {lote.codigo_lote} criado — {quantidade_esperada:g} unidades de {sku.codigo} aguardando chegada.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao criar lote: {exc}', 'danger')

    return _redirect()


@recebimento.route('/<int:id>/confirmar', methods=['POST'])
@login_required
def confirmar_lote(id):
    current_user = get_current_user()
    lote = db.session.get(LoteRecebimento, id)
    if not lote:
        flash('Lote não encontrado.', 'danger')
        return _redirect()

    if not lote.is_pending:
        flash(f'Este lote já foi {lote.status_label.lower()}.', 'warning')
        return _redirect(lote.codigo_lote)

    preco_raw = request.form.get('preco_custo')
    try:
        preco_custo = parse_decimal_input(preco_raw) if preco_raw else lote.preco_custo
    except ValueError as exc:
        flash(str(exc), 'danger')
        return _redirect(lote.codigo_lote)

    if not preco_custo or preco_custo <= 0:
        flash('Informe o preço de custo para confirmar o recebimento.', 'warning')
        return _redirect(lote.codigo_lote)

    try:
        db.session.add(Produto(
            sku_id=lote.sku_id,
            quantidade=lote.quantidade_esperada,
            preco=float(preco_custo),
        ))
        lote.status = 'confirmado'
        lote.confirmado_por_id = current_user.id if current_user else None
        lote.confirmado_em = datetime.utcnow()
        lote.preco_custo = float(preco_custo)
        db.session.commit()
        flash(
            f'Lote {lote.codigo_lote} confirmado — {lote.quantidade_esperada:g} unidades de '
            f'{lote.sku.codigo} entradas em recebimento. Crie uma tarefa de endereçamento para levá-las à prateleira.',
            'success',
        )
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao confirmar lote: {exc}', 'danger')
        return _redirect(lote.codigo_lote)

    return redirect(url_for('balanco.gerenciar_balanco', sku_id=lote.sku_id))


@recebimento.route('/<int:id>/cancelar', methods=['POST'])
@functional_permission_required('can_assign_balanco', 'Seu papel não permite cancelar lotes.')
def cancelar_lote(id):
    lote = db.session.get(LoteRecebimento, id)
    if not lote:
        flash('Lote não encontrado.', 'danger')
        return _redirect()

    if not lote.is_pending:
        flash(f'Este lote já foi {lote.status_label.lower()}.', 'warning')
        return _redirect()

    try:
        lote.status = 'cancelado'
        db.session.commit()
        flash(f'Lote {lote.codigo_lote} cancelado.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cancelar lote: {exc}', 'danger')

    return _redirect()


@recebimento.route('/<int:id>/qrcode')
@login_required
def qrcode_lote_svg(id):
    lote = db.session.get(LoteRecebimento, id)
    if not lote:
        abort(404)
    return Response(gerar_svg_qrcode_lote(lote), mimetype='image/svg+xml')


@recebimento.route('/<int:id>/qrcode/download')
@login_required
def download_qrcode_lote(id):
    lote = db.session.get(LoteRecebimento, id)
    if not lote:
        abort(404)
    return Response(
        gerar_svg_qrcode_lote(lote),
        mimetype='image/svg+xml',
        headers={'Content-Disposition': f'attachment; filename="{lote.codigo_lote}.svg"'},
    )
