from datetime import datetime
from urllib.parse import urlsplit
import unicodedata

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func

from app.auth import admin_required
from app.models import Patrimonio, Sku, db
from app.number_utils import parse_decimal_input

patrimonios = Blueprint('patrimonios', __name__, url_prefix='/patrimonios')

STATUS_PATRIMONIO = [
    'Disponível',
    'Em Uso',
    'Em Manutenção',
    'Furtado',
    'Descartado',
]

STATUS_PATRIMONIO_MAP = {
    ''.join(caractere for caractere in unicodedata.normalize('NFD', status.lower()) if unicodedata.category(caractere) != 'Mn'): status
    for status in STATUS_PATRIMONIO
}


def redirecionar_para_origem():
    destino = request.form.get('next') or request.args.get('next') or request.referrer

    if destino:
        url = urlsplit(destino)
        if not url.netloc or url.netloc == request.host:
            caminho = url.path or url_for('patrimonios.gerenciar_patrimonios')
            if url.query:
                caminho = f'{caminho}?{url.query}'
            return redirect(caminho)

    return redirect(url_for('patrimonios.gerenciar_patrimonios'))


def normalizar_texto(valor):
    texto = (valor or '').strip()
    return texto or None


def normalizar_status_patrimonio(valor):
    texto = (valor or '').strip()
    if not texto:
        return None

    chave = ''.join(
        caractere for caractere in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(caractere) != 'Mn'
    )
    return STATUS_PATRIMONIO_MAP.get(chave)


def parse_data(raw_value):
    valor = (raw_value or '').strip()
    if not valor:
        return None
    return datetime.strptime(valor, '%Y-%m-%d').date()


def buscar_patrimonio_por_codigo(codigo, exclude_id=None):
    query = Patrimonio.query.filter(func.lower(Patrimonio.codigo_patrimonio) == codigo.lower())
    if exclude_id is not None:
        query = query.filter(Patrimonio.id != exclude_id)
    return query.first()


def buscar_patrimonio_por_numero_serie(numero_serie, exclude_id=None):
    query = Patrimonio.query.filter(func.lower(Patrimonio.numero_serie) == numero_serie.lower())
    if exclude_id is not None:
        query = query.filter(Patrimonio.id != exclude_id)
    return query.first()


def validar_campos_patrimonio(codigo_patrimonio, sku_id, status):
    if not codigo_patrimonio or not sku_id:
        flash('Código do patrimônio e SKU são obrigatórios.', 'warning')
        return False

    if status not in STATUS_PATRIMONIO:
        flash('Status do patrimônio inválido.', 'danger')
        return False

    return True


@patrimonios.route('/gerenciar')
@admin_required
def gerenciar_patrimonios():
    patrimonios_cadastrados = Patrimonio.query.order_by(Patrimonio.created_at.desc(), Patrimonio.id.desc()).all()
    skus = Sku.query.order_by(Sku.nome.asc()).all()
    return render_template(
        'gerenciar_patrimonios.html',
        patrimonios=patrimonios_cadastrados,
        skus=skus,
        status_opcoes=STATUS_PATRIMONIO,
    )


@patrimonios.route('/cadastrar', methods=['POST'])
@admin_required
def cadastrar_patrimonio():
    codigo_patrimonio = (request.form.get('codigo_patrimonio') or '').strip().upper()
    numero_serie = normalizar_texto(request.form.get('numero_serie'))
    sku_id = request.form.get('sku_id', type=int)
    status = normalizar_status_patrimonio(request.form.get('status')) or 'Disponível'
    observacoes = normalizar_texto(request.form.get('observacoes'))

    if not validar_campos_patrimonio(codigo_patrimonio, sku_id, status):
        return redirecionar_para_origem()

    if buscar_patrimonio_por_codigo(codigo_patrimonio):
        flash('Já existe um patrimônio com esse código.', 'danger')
        return redirecionar_para_origem()

    if numero_serie and buscar_patrimonio_por_numero_serie(numero_serie):
        flash('Já existe um patrimônio com esse número de série.', 'danger')
        return redirecionar_para_origem()

    sku = db.session.get(Sku, sku_id)
    if not sku:
        flash('SKU inválido para o patrimônio.', 'danger')
        return redirecionar_para_origem()

    try:
        data_compra = parse_data(request.form.get('data_compra'))
        fim_garantia = parse_data(request.form.get('fim_garantia'))
        valor_compra = parse_decimal_input(request.form.get('valor_compra')) if request.form.get('valor_compra') else None

        patrimonio = Patrimonio(
            codigo_patrimonio=codigo_patrimonio,
            numero_serie=numero_serie,
            sku_id=sku.id,
            status=status,
            data_compra=data_compra,
            fim_garantia=fim_garantia,
            valor_compra=valor_compra,
            observacoes=observacoes,
        )
        db.session.add(patrimonio)
        db.session.commit()
        flash('Patrimônio cadastrado com sucesso.', 'success')
    except ValueError as exc:
        db.session.rollback()
        flash(f'Erro ao interpretar os dados do patrimônio: {exc}', 'danger')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cadastrar patrimônio: {exc}', 'danger')

    return redirecionar_para_origem()


@patrimonios.route('/editar/<int:id>', methods=['POST'])
@admin_required
def editar_patrimonio(id):
    patrimonio = Patrimonio.query.get(id)
    if not patrimonio:
        flash('Patrimônio não encontrado.', 'danger')
        return redirecionar_para_origem()

    codigo_patrimonio = (request.form.get('codigo_patrimonio') or '').strip().upper()
    numero_serie = normalizar_texto(request.form.get('numero_serie'))
    sku_id = request.form.get('sku_id', type=int)
    status = normalizar_status_patrimonio(request.form.get('status')) or 'Disponível'
    observacoes = normalizar_texto(request.form.get('observacoes'))

    if not validar_campos_patrimonio(codigo_patrimonio, sku_id, status):
        return redirecionar_para_origem()

    if buscar_patrimonio_por_codigo(codigo_patrimonio, exclude_id=patrimonio.id):
        flash('Já existe outro patrimônio com esse código.', 'danger')
        return redirecionar_para_origem()

    if numero_serie and buscar_patrimonio_por_numero_serie(numero_serie, exclude_id=patrimonio.id):
        flash('Já existe outro patrimônio com esse número de série.', 'danger')
        return redirecionar_para_origem()

    sku = db.session.get(Sku, sku_id)
    if not sku:
        flash('SKU inválido para o patrimônio.', 'danger')
        return redirecionar_para_origem()

    try:
        patrimonio.codigo_patrimonio = codigo_patrimonio
        patrimonio.numero_serie = numero_serie
        patrimonio.sku_id = sku.id
        patrimonio.status = status
        patrimonio.data_compra = parse_data(request.form.get('data_compra'))
        patrimonio.fim_garantia = parse_data(request.form.get('fim_garantia'))
        patrimonio.valor_compra = parse_decimal_input(request.form.get('valor_compra')) if request.form.get('valor_compra') else None
        patrimonio.observacoes = observacoes
        db.session.commit()
        flash('Patrimônio atualizado com sucesso.', 'success')
    except ValueError as exc:
        db.session.rollback()
        flash(f'Erro ao interpretar os dados do patrimônio: {exc}', 'danger')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao atualizar patrimônio: {exc}', 'danger')

    return redirecionar_para_origem()


@patrimonios.route('/deletar/<int:id>', methods=['POST'])
@admin_required
def deletar_patrimonio(id):
    patrimonio = Patrimonio.query.get(id)
    if not patrimonio:
        flash('Patrimônio não encontrado.', 'danger')
        return redirecionar_para_origem()

    if patrimonio.user_id:
        flash('Não é possível excluir um patrimônio que já esteja vinculado a um responsável.', 'warning')
        return redirecionar_para_origem()

    try:
        db.session.delete(patrimonio)
        db.session.commit()
        flash('Patrimônio removido com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao remover patrimônio: {exc}', 'danger')

    return redirecionar_para_origem()


@patrimonios.route('/get/<int:id>')
@admin_required
def get_patrimonio(id):
    patrimonio = Patrimonio.query.get(id)
    if not patrimonio:
        return jsonify({'error': 'Patrimônio não encontrado'}), 404

    return jsonify({
        'id': patrimonio.id,
        'codigo_patrimonio': patrimonio.codigo_patrimonio,
        'numero_serie': patrimonio.numero_serie or '',
        'sku_id': patrimonio.sku_id,
        'status': patrimonio.status,
        'data_compra': patrimonio.data_compra.strftime('%Y-%m-%d') if patrimonio.data_compra else '',
        'fim_garantia': patrimonio.fim_garantia.strftime('%Y-%m-%d') if patrimonio.fim_garantia else '',
        'valor_compra': patrimonio.valor_compra,
        'observacoes': patrimonio.observacoes or '',
    })