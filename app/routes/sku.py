from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Sku, Marca, Tipo, Familia, Especificacao
from flask import jsonify

sku = Blueprint(
    'sku',
    __name__,
    url_prefix='/sku' 
)

@sku.route('/gerenciar')
def gerenciar_sku():
    skus = Sku.query.order_by(Sku.created_at.desc()).all()
    marcas = Marca.query.order_by(Marca.nome).all()
    tipos = Tipo.query.order_by(Tipo.nome).all()
    
    return render_template('gerenciar_sku.html', skus=skus, marcas=marcas, tipos=tipos)

@sku.route('/cadastrar_sku', methods=['POST'])
def cadastrar_sku():
    codigo = request.form.get('codigo', '').strip()
    nome = request.form.get('nome', '').strip()
    marca_id = request.form.get('marca_id')
    tipo_id = request.form.get('tipo_id')
    familia_id = request.form.get('familia_id')
    peso_str = request.form.get('peso')
    valor_peso_str = request.form.get('valorPeso')
    especificacao_nome = request.form.get('especificacao_nome', '').strip()

    if not all([codigo, nome, marca_id, tipo_id, familia_id]):
        flash('Código SKU, Nome, Marca, Tipo e Família são campos obrigatórios.', 'warning')
        return redirect(url_for('sku.gerenciar_sku'))

    try:
        if Sku.query.filter_by(codigo=codigo).first():
            flash(f'O código SKU "{codigo}" já está em uso!', 'danger')
            return redirect(url_for('sku.gerenciar_sku'))

        especificacao_id = None
        if especificacao_nome:
            espec = Especificacao.query.filter_by(nome=especificacao_nome).first()
            if not espec:
                espec = Especificacao(nome=especificacao_nome)
                db.session.add(espec)
                db.session.flush()
            especificacao_id = espec.id

        peso = float(peso_str) if peso_str else None
        valor_peso = float(valor_peso_str) if valor_peso_str else None

        novo_sku = Sku(codigo=codigo, nome=nome, marca_id=int(marca_id), tipo_id=int(tipo_id), familia_id=int(familia_id), especificacao_id=especificacao_id, peso=peso, valorPeso=valor_peso)

        db.session.add(novo_sku)
        db.session.commit()
        flash(f'SKU "{codigo}" criado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao salvar o SKU: {str(e)}', 'danger')

    return redirect(url_for('sku.gerenciar_sku'))

@sku.route('/editar_sku/<int:id>', methods=['GET', 'POST'])
def editar_sku(id):
    sku_obj = Sku.query.get(id)
    
    if not sku_obj:
        flash('SKU não encontrado!', 'danger')
        return redirect(url_for('sku.gerenciar_sku'))
    
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        nome = request.form.get('nome', '').strip()
        marca_id = request.form.get('marca_id')
        tipo_id = request.form.get('tipo_id')
        familia_id = request.form.get('familia_id')
        peso_str = request.form.get('peso')
        valor_peso_str = request.form.get('valorPeso')
        especificacao_nome = request.form.get('especificacao_nome', '').strip()

        if not all([codigo, nome, marca_id, tipo_id, familia_id]):
            flash('Código SKU, Nome, Marca, Tipo e Família são campos obrigatórios.', 'warning')
            return redirect(url_for('sku.gerenciar_sku'))

        try:
            if Sku.query.filter_by(codigo=codigo).filter(Sku.id != id).first():
                flash(f'O código SKU "{codigo}" já está em uso!', 'danger')
                return redirect(url_for('sku.gerenciar_sku'))

            especificacao_id = None
            if especificacao_nome:
                espec = Especificacao.query.filter_by(nome=especificacao_nome).first()
                if not espec:
                    espec = Especificacao(nome=especificacao_nome)
                    db.session.add(espec)
                    db.session.flush()
                especificacao_id = espec.id

            peso = float(peso_str) if peso_str else None
            valor_peso = float(valor_peso_str) if valor_peso_str else None

            sku_obj.codigo = codigo
            sku_obj.nome = nome
            sku_obj.marca_id = int(marca_id)
            sku_obj.tipo_id = int(tipo_id)
            sku_obj.familia_id = int(familia_id)
            sku_obj.especificacao_id = especificacao_id
            sku_obj.peso = peso
            sku_obj.valorPeso = valor_peso

            db.session.commit()
            flash(f'SKU "{codigo}" atualizado com sucesso!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao atualizar o SKU: {str(e)}', 'danger')

        return redirect(url_for('sku.gerenciar_sku'))
    
    return redirect(url_for('sku.gerenciar_sku'))

@sku.route('/deletar_sku/<int:id>', methods=['POST'])
def deletar_sku(id):
    sku_obj = Sku.query.get(id)
    
    if not sku_obj:
        flash('SKU não encontrado!', 'danger')
        return redirect(url_for('sku.gerenciar_sku'))
    
    try:
        db.session.delete(sku_obj)
        db.session.commit()
        flash('SKU deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar SKU: {str(e)}', 'danger')
    
    return redirect(url_for('sku.gerenciar_sku'))

@sku.route('/get/<int:id>')
def get_sku(id):
    sku_obj = Sku.query.get(id)
    
    if not sku_obj:
        return jsonify({'error': 'SKU não encontrado'}), 404
    
    return jsonify({
        'id': sku_obj.id,
        'codigo': sku_obj.codigo,
        'nome': sku_obj.nome,
        'marca_id': sku_obj.marca_id,
        'tipo_id': sku_obj.tipo_id,
        'familia_id': sku_obj.familia_id,
        'familia_nome': sku_obj.familia.nome if sku_obj.familia else '',
        'peso': sku_obj.peso,
        'valorPeso': sku_obj.valorPeso,
        'especificacao_nome': sku_obj.especificacao.nome if sku_obj.especificacao_id and sku_obj.especificacao else ''
    })