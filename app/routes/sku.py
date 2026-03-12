from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Sku, Marca, Tipo, Familia, Especificacao

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