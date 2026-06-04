from datetime import datetime
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, redirect, render_template, request, url_for, flash

from app.audit import log
from app.auth import get_current_user
from app.models import db, Produto, Sku
from app.number_utils import parse_decimal_input

produtos = Blueprint(
    'produtos',
    __name__,
    url_prefix='/produtos'
)


def redirecionar_para_origem():
    destino = request.form.get('next') or request.args.get('next') or request.referrer

    if destino:
        url = urlsplit(destino)
        if not url.netloc or url.netloc == request.host:
            caminho = url.path or url_for('produtos.gerenciar_produtos')
            if url.query:
                caminho = f'{caminho}?{url.query}'
            return redirect(caminho)

    return redirect(url_for('produtos.gerenciar_produtos'))

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
        return redirecionar_para_origem()

    try:
        quantidade = parse_decimal_input(quantidade_str)
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
        sku_obj = db.session.get(Sku, int(sku_id))
        log(get_current_user(), 'Produtos', 'Cadastrou produto',
            f'SKU {sku_obj.codigo if sku_obj else sku_id} | qtd {quantidade} | R$ {preco:.2f}')
        flash('Produto adicionado ao estoque com sucesso!', 'success')

    except ValueError:
        flash('Por favor, insira valores numéricos válidos!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao cadastrar o produto: {str(e)}', 'danger')

    return redirecionar_para_origem()

@produtos.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    produto = Produto.query.get(id)
    
    if not produto:
        flash('Produto não encontrado!', 'danger')
        return redirecionar_para_origem()
    
    if request.method == 'POST':
        sku_id = request.form.get('sku_id')
        quantidade_str = request.form.get('quantidade')
        preco_str = request.form.get('preco')
        corredor = request.form.get('corredor', '').strip()
        prateleira = request.form.get('prateleira', '').strip()
        data_validade_str = request.form.get('data_validade')

        if not all([sku_id, quantidade_str, preco_str]):
            flash('SKU, Quantidade e Preço são campos obrigatórios.', 'warning')
            return redirecionar_para_origem()

        try:
            quantidade = parse_decimal_input(quantidade_str)
            preco = float(preco_str)
            data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date() if data_validade_str else None

            produto.sku_id = int(sku_id)
            produto.quantidade = quantidade
            produto.preco = preco
            produto.corredor = corredor
            produto.prateleira = prateleira
            produto.data_validade = data_validade

            db.session.commit()
            sku_obj = db.session.get(Sku, int(sku_id))
            log(get_current_user(), 'Produtos', 'Editou produto',
                f'#{id} SKU {sku_obj.codigo if sku_obj else sku_id} | qtd {quantidade} | R$ {preco:.2f}')
            flash('Produto atualizado com sucesso!', 'success')

        except ValueError:
            flash('Por favor, insira valores numéricos válidos!', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao atualizar o produto: {str(e)}', 'danger')

        return redirecionar_para_origem()
    
    return redirecionar_para_origem()

@produtos.route('/deletar/<int:id>', methods=['POST'])
def deletar_produto(id):
    produto = Produto.query.get(id)
    
    if not produto:
        flash('Produto não encontrado!', 'danger')
        return redirecionar_para_origem()
    
    try:
        sku_codigo = produto.sku.codigo if produto.sku else str(produto.sku_id)
        db.session.delete(produto)
        db.session.commit()
        log(get_current_user(), 'Produtos', 'Removeu produto', f'#{id} SKU {sku_codigo}')
        flash('Produto deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar produto: {str(e)}', 'danger')
    
    return redirecionar_para_origem()

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


@produtos.route('/detalhes/<int:id>')
def detalhes_produto(id):
    from app.models import TarefaBalanco, LoteRecebimento
    produto = db.session.get(Produto, id)
    if not produto:
        return jsonify({'error': 'Produto não encontrado'}), 404

    sku = produto.sku
    tarefas = (
        TarefaBalanco.query.filter_by(sku_id=produto.sku_id)
        .order_by(TarefaBalanco.created_at.desc())
        .limit(10).all()
    )
    lotes = (
        LoteRecebimento.query.filter_by(sku_id=produto.sku_id)
        .order_by(LoteRecebimento.created_at.desc())
        .limit(10).all()
    )

    return jsonify({
        'produto': {
            'id': produto.id,
            'sku_codigo': sku.codigo if sku else '-',
            'sku_nome': sku.nome if sku else '-',
            'familia': sku.familia.nome if sku and sku.familia else '-',
            'tipo': sku.tipo.nome if sku and sku.tipo else '-',
            'marca': sku.marca.nome if sku and sku.marca else '-',
            'quantidade': float(produto.quantidade or 0),
            'preco': float(produto.preco or 0),
            'corredor': produto.corredor or '-',
            'prateleira': produto.prateleira or '-',
            'data_validade': produto.data_validade.strftime('%d/%m/%Y') if produto.data_validade else '-',
            'criado_em': produto.created_at.strftime('%d/%m/%Y %H:%M') if produto.created_at else '-',
            'atualizado_em': produto.updated_at.strftime('%d/%m/%Y %H:%M') if produto.updated_at else '-',
        },
        'tarefas': [
            {
                'titulo': t.titulo,
                'tipo': t.tipo_operacao_label,
                'status': t.status_label,
                'responsavel': t.responsavel.username if t.responsavel else '-',
                'criado_em': t.created_at.strftime('%d/%m/%Y') if t.created_at else '-',
                'concluido_em': t.concluido_em.strftime('%d/%m/%Y') if t.concluido_em else '-',
                'qtd_esperada': float(t.quantidade_esperada or 0),
                'qtd_realizada': float(t.quantidade_realizada or 0) if t.quantidade_realizada is not None else None,
            }
            for t in tarefas
        ],
        'lotes': [
            {
                'codigo': l.codigo_lote,
                'status': l.status_label,
                'quantidade': float(l.quantidade_esperada or 0),
                'preco_custo': float(l.preco_custo or 0) if l.preco_custo else None,
                'criado_em': l.created_at.strftime('%d/%m/%Y') if l.created_at else '-',
                'confirmado_em': l.confirmado_em.strftime('%d/%m/%Y') if l.confirmado_em else '-',
                'criado_por': l.criado_por.username if l.criado_por else '-',
            }
            for l in lotes
        ],
    })