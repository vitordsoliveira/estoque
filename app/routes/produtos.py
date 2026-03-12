from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Produto, Sku
from datetime import datetime

produtos = Blueprint(
    'produtos',
    __name__,
    url_prefix='/produtos'
)

@produtos.route('/gerenciar')
def gerenciar_produtos():
    # Buscar produtos existentes e SKUs para o formulário
    produtos_em_estoque = Produto.query.order_by(Produto.created_at.desc()).all()
    skus_disponiveis = Sku.query.order_by(Sku.nome).all()
    return render_template('gerenciar_produtos.html', produtos=produtos_em_estoque, skus=skus_disponiveis)

@produtos.route('/cadastrar', methods=['POST'])
def cadastrar_produto():
    sku_id = request.form.get('sku_id')
    quantidade_str = request.form.get('quantidade')
    preco_str = request.form.get('preco')
    corredor = request.form.get('corredor', '').strip()
    prateleira = request.form.get('prateleira', '').strip()
    data_validade_str = request.form.get('data_validade')

    if not all([sku_id, quantidade_str, preco_str]):
        flash('SKU, Quantidade e Preço são campos obrigatórios.', 'warning')
        return redirect(url_for('produtos.gerenciar_produtos'))

    try:
        quantidade = float(quantidade_str)
        preco = float(preco_str)
        data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date() if data_validade_str else None

        novo_produto = Produto(
            sku_id=int(sku_id),
            quantidade=quantidade,
            preco=preco,
            corredor=corredor,
            prateleira=prateleira,
            data_validade=data_validade
        )

        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado ao estoque com sucesso!', 'success')

    except ValueError:
        flash('Por favor, insira valores numéricos válidos!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao cadastrar o produto: {str(e)}', 'danger')

    return redirect(url_for('produtos.gerenciar_produtos'))