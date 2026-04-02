from flask import Blueprint, render_template
from sqlalchemy import func

from app.models import Familia, Produto, Sku, db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    total_em_estoque = db.session.query(func.coalesce(func.sum(Produto.quantidade), 0)).scalar() or 0
    total_baixo_estoque = Produto.query.filter(Produto.quantidade > 0, Produto.quantidade <= 5).count()
    total_familias = Familia.query.count()

    produtos = Produto.query.order_by(Produto.updated_at.desc(), Produto.created_at.desc()).all()
    skus = Sku.query.order_by(Sku.nome).all()
    familias = Familia.query.order_by(Familia.nome).all()

    return render_template(
        'index.html',
        total_em_estoque=total_em_estoque,
        total_baixo_estoque=total_baixo_estoque,
        total_familias=total_familias,
        produtos=produtos,
        skus=skus,
        familias=familias
    )
