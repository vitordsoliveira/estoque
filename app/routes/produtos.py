from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models import Produto, Sku, db

produtos = Blueprint(
    'produtos',
    __name__,
    url_prefix='/produtos'
)


@produtos.route('/gerenciar')
def gerenciar_produtos():
    produtos_em_estoque = Produto.query.order_by(Produto.created_at.desc()).all()
    skus_disponiveis = Sku.query.order_by(Sku.nome).all()
    return render_template('gerenciar_produtos.html', produtos=produtos_em_estoque, skus=skus_disponiveis)


def sku_tem_preco_por_peso(sku):
    return bool(sku and sku.peso and sku.peso > 0 and sku.valorPeso and sku.valorPeso > 0)


@produtos.route('/cadastrar', methods=['POST'])
def cadastrar_produto():
    sku_id = request.form.get('sku_id')
    quantidade_str = request.form.get('quantidade')
    preco_str = request.form.get('preco')
    corredor = request.form.get('corredor', '').strip()
    prateleira = request.form.get('prateleira', '').strip()
    data_validade_str = request.form.get('data_validade')

    if not all([sku_id, quantidade_str]):
        flash('SKU e Quantidade são campos obrigatórios.', 'warning')
        return redirect(url_for('produtos.gerenciar_produtos'))

    try:
        sku = db.session.get(Sku, int(sku_id))
        if not sku:
            flash('SKU não encontrado.', 'danger')
            return redirect(url_for('produtos.gerenciar_produtos'))

        quantidade = float(quantidade_str)
        if sku_tem_preco_por_peso(sku):
            preco = float(sku.valorPeso)
        else:
            if not preco_str:
                flash('Preço é obrigatório para SKUs sem preço por peso.', 'warning')
                return redirect(url_for('produtos.gerenciar_produtos'))
            preco = float(preco_str)

        data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date() if data_validade_str else None

        novo_produto = Produto(
            sku_id=sku.id,
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
