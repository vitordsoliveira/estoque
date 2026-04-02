from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Produto, Sku
from datetime import datetime
from flask import jsonify

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

@produtos.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    produto = Produto.query.get(id)
    
    if not produto:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('produtos.gerenciar_produtos'))
    
    if request.method == 'POST':
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

            produto.sku_id = int(sku_id)
            produto.quantidade = quantidade
            produto.preco = preco
            produto.corredor = corredor
            produto.prateleira = prateleira
            produto.data_validade = data_validade

            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')

        except ValueError:
            flash('Por favor, insira valores numéricos válidos!', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao atualizar o produto: {str(e)}', 'danger')

        return redirect(url_for('produtos.gerenciar_produtos'))
    
    return redirect(url_for('produtos.gerenciar_produtos'))

@produtos.route('/deletar/<int:id>', methods=['POST'])
def deletar_produto(id):
    produto = Produto.query.get(id)
    
    if not produto:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('produtos.gerenciar_produtos'))
    
    try:
        db.session.delete(produto)
        db.session.commit()
        flash('Produto deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar produto: {str(e)}', 'danger')
    
    return redirect(url_for('produtos.gerenciar_produtos'))

@produtos.route('/get/<int:id>')
def get_produto(id):
    produto = Produto.query.get(id)
    
    if not produto:
        return jsonify({'error': 'Produto não encontrado'}), 404
    
    return jsonify({
        'id': produto.id,
        'sku_id': produto.sku_id,
        'quantidade': produto.quantidade,
        'preco': produto.preco,
        'corredor': produto.corredor,
        'prateleira': produto.prateleira,
        'data_validade': produto.data_validade.strftime('%Y-%m-%d') if produto.data_validade else ''
    })