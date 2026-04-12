import json
from collections import defaultdict

from flask import Blueprint, flash, render_template, request

from app.models import Produto, Sku, db

balanco = Blueprint(
    'balanco',
    __name__,
    url_prefix='/balanco'
)


def normalizar_quantidade(valor):
    return float(valor or 0)


def produto_esta_enderecado(produto):
    return bool((produto.corredor or '').strip() or (produto.prateleira or '').strip())


def formatar_localizacao(produto):
    corredor = (produto.corredor or '').strip()
    prateleira = (produto.prateleira or '').strip()

    if corredor or prateleira:
        return f'{corredor or "-"} / {prateleira or "-"}'

    return 'Recebimento / sem endereço'


def resolver_sku_por_payload(leitura):
    texto = (leitura or '').strip()
    if not texto:
        raise ValueError('Leia um QR Code ou informe um código de SKU para iniciar o balanço.')

    payload = None
    codigo = texto

    if texto.startswith('{'):
        try:
            payload = json.loads(texto)
        except json.JSONDecodeError as exc:
            raise ValueError('O conteúdo lido do QR Code não está em um formato JSON válido.') from exc

    if payload is not None:
        if not isinstance(payload, dict):
            raise ValueError('O QR Code lido não possui um payload válido para SKU.')

        payload_type = (payload.get('type') or '').strip().lower()
        if payload_type and payload_type != 'sku':
            raise ValueError('O QR Code lido não pertence a um SKU válido.')

        sku_id = payload.get('id')
        codigo = (payload.get('codigo') or '').strip()

        sku = None
        if sku_id is not None:
            try:
                sku = db.session.get(Sku, int(sku_id))
            except (TypeError, ValueError):
                sku = None

        if not sku and codigo:
            sku = Sku.query.filter_by(codigo=codigo).first()

        if not sku:
            raise LookupError('Nenhum SKU vinculado ao QR Code foi encontrado.')

        return sku, 'qrcode'

    sku = Sku.query.filter_by(codigo=codigo).first()
    if not sku:
        raise LookupError('Nenhum SKU encontrado para o código informado.')

    return sku, 'codigo'


def resolver_sku_para_balanco(sku_id=None, leitura=None):
    if sku_id:
        sku = db.session.get(Sku, sku_id)
        if not sku:
            raise LookupError('O SKU selecionado para o balanço não foi encontrado.')
        return sku, 'atalho'

    return resolver_sku_por_payload(leitura)


def montar_resumo_balanco(sku):
    produtos = Produto.query.filter_by(sku_id=sku.id).order_by(Produto.created_at.desc(), Produto.id.desc()).all()

    quantidade_total = sum(normalizar_quantidade(produto.quantidade) for produto in produtos)
    quantidade_prateleira = sum(
        normalizar_quantidade(produto.quantidade)
        for produto in produtos
        if produto_esta_enderecado(produto)
    )
    quantidade_recebida = quantidade_total - quantidade_prateleira

    resumo_localizacoes = defaultdict(lambda: {'localizacao': '', 'quantidade': 0.0, 'registros': 0, 'enderecado': False})
    for produto in produtos:
        localizacao = formatar_localizacao(produto)
        acumulado = resumo_localizacoes[localizacao]
        acumulado['localizacao'] = localizacao
        acumulado['quantidade'] += normalizar_quantidade(produto.quantidade)
        acumulado['registros'] += 1
        acumulado['enderecado'] = produto_esta_enderecado(produto)

    mapa_localizacoes = sorted(
        resumo_localizacoes.values(),
        key=lambda item: (
            0 if item['enderecado'] else 1,
            item['localizacao'].lower()
        )
    )

    return {
        'produtos_relacionados': produtos,
        'quantidade_total': quantidade_total,
        'quantidade_prateleira': quantidade_prateleira,
        'quantidade_recebida': quantidade_recebida,
        'total_registros': len(produtos),
        'mapa_localizacoes': mapa_localizacoes,
    }


@balanco.route('/gerenciar')
def gerenciar_balanco():
    leitura = (request.args.get('leitura') or '').strip()
    sku_id = request.args.get('sku_id', type=int)

    sku = None
    origem_leitura = None
    contexto_balanco = {
        'produtos_relacionados': [],
        'quantidade_total': 0.0,
        'quantidade_prateleira': 0.0,
        'quantidade_recebida': 0.0,
        'total_registros': 0,
        'mapa_localizacoes': [],
    }

    if sku_id or leitura:
        try:
            sku, origem_leitura = resolver_sku_para_balanco(sku_id=sku_id, leitura=leitura)
            contexto_balanco = montar_resumo_balanco(sku)
            if not leitura and sku:
                leitura = sku.codigo
        except ValueError as exc:
            flash(str(exc), 'warning')
        except LookupError as exc:
            flash(str(exc), 'danger')

    return render_template(
        'gerenciar_balanco.html',
        leitura=leitura,
        sku=sku,
        origem_leitura=origem_leitura,
        **contexto_balanco,
    )