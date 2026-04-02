from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Sku, Marca, Tipo, Familia, Especificacao, Produto, Patrimonio
from app.number_utils import parse_scaled_input
from flask import jsonify
import re

sku = Blueprint(
    'sku',
    __name__,
    url_prefix='/sku' 
)


def gerar_prefixo_familia(familia_id):
    if familia_id > 999:
        raise ValueError('A família excede o limite suportado para geração automática de SKU.')

    return f'{familia_id:03d}'


def gerar_codigo_sku_para_familia(familia):
    prefixo = gerar_prefixo_familia(familia.id)
    skus_existentes = Sku.query.filter(Sku.codigo.like(f'{prefixo}%')).all()
    maior_sequencia = 0

    for sku_existente in skus_existentes:
        correspondencia = re.fullmatch(rf'{prefixo}(\d{{5}})', sku_existente.codigo or '')
        if correspondencia:
            maior_sequencia = max(maior_sequencia, int(correspondencia.group(1)))

    proxima_sequencia = maior_sequencia + 1
    if proxima_sequencia > 99999:
        raise ValueError(f'A família "{familia.nome}" atingiu o limite de códigos disponíveis.')

    return f'{prefixo}{proxima_sequencia:05d}'

@sku.route('/gerenciar')
def gerenciar_sku():
    skus = Sku.query.order_by(Sku.created_at.desc()).all()
    marcas = Marca.query.order_by(Marca.nome).all()
    tipos = Tipo.query.order_by(Tipo.nome).all()
    
    return render_template('gerenciar_sku.html', skus=skus, marcas=marcas, tipos=tipos)

@sku.route('/cadastrar_sku', methods=['POST'])
def cadastrar_sku():
    nome = request.form.get('nome', '').strip()
    marca_id = request.form.get('marca_id')
    tipo_id = request.form.get('tipo_id')
    familia_id = request.form.get('familia_id')
    peso_str = request.form.get('peso')
    valor_peso_str = request.form.get('valorPeso')
    especificacao_nome = request.form.get('especificacao_nome', '').strip()

    if not all([nome, marca_id, tipo_id, familia_id]):
        flash('Nome, Marca, Tipo e Família são campos obrigatórios.', 'warning')
        return redirect(url_for('sku.gerenciar_sku'))

    try:
        familia = Familia.query.get(int(familia_id))
        if not familia:
            flash('Família inválida para geração do SKU.', 'danger')
            return redirect(url_for('sku.gerenciar_sku'))

        codigo = gerar_codigo_sku_para_familia(familia)

        especificacao_id = None
        if especificacao_nome:
            espec = Especificacao.query.filter_by(nome=especificacao_nome).first()
            if not espec:
                espec = Especificacao(nome=especificacao_nome)
                db.session.add(espec)
                db.session.flush()
            especificacao_id = espec.id

        peso = parse_scaled_input(peso_str) if peso_str else None
        valor_peso = float(valor_peso_str) if valor_peso_str else None

        novo_sku = Sku(codigo=codigo, nome=nome, marca_id=int(marca_id), tipo_id=int(tipo_id), familia_id=int(familia_id), especificacao_id=especificacao_id, peso=peso, valorPeso=valor_peso)

        db.session.add(novo_sku)
        db.session.commit()
        flash(f'SKU "{codigo}" criado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao salvar o SKU: {str(e)}', 'danger')

    return redirect(url_for('sku.gerenciar_sku'))


@sku.route('/gerar_codigo')
def gerar_codigo_sku():
    familia_id = request.args.get('familia_id', type=int)

    if not familia_id:
        return jsonify({'error': 'Família é obrigatória para gerar o código do SKU.'}), 400

    familia = Familia.query.get(familia_id)
    if not familia:
        return jsonify({'error': 'Família não encontrada.'}), 404

    try:
        codigo = gerar_codigo_sku_para_familia(familia)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    return jsonify({'codigo': codigo})

@sku.route('/editar_sku/<int:id>', methods=['GET', 'POST'])
def editar_sku(id):
    sku_obj = Sku.query.get(id)
    
    if not sku_obj:
        flash('SKU não encontrado!', 'danger')
        return redirect(url_for('sku.gerenciar_sku'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        marca_id = request.form.get('marca_id')
        tipo_id = request.form.get('tipo_id')
        familia_id = request.form.get('familia_id')
        peso_str = request.form.get('peso')
        valor_peso_str = request.form.get('valorPeso')
        especificacao_nome = request.form.get('especificacao_nome', '').strip()

        if not all([nome, marca_id, tipo_id, familia_id]):
            flash('Nome, Marca, Tipo e Família são campos obrigatórios.', 'warning')
            return redirect(url_for('sku.gerenciar_sku'))

        try:
            especificacao_id = None
            if especificacao_nome:
                espec = Especificacao.query.filter_by(nome=especificacao_nome).first()
                if not espec:
                    espec = Especificacao(nome=especificacao_nome)
                    db.session.add(espec)
                    db.session.flush()
                especificacao_id = espec.id

            peso = parse_scaled_input(peso_str) if peso_str else None
            valor_peso = float(valor_peso_str) if valor_peso_str else None

            sku_obj.nome = nome
            sku_obj.marca_id = int(marca_id)
            sku_obj.tipo_id = int(tipo_id)
            sku_obj.familia_id = int(familia_id)
            sku_obj.especificacao_id = especificacao_id
            sku_obj.peso = peso
            sku_obj.valorPeso = valor_peso

            db.session.commit()
            flash(f'SKU "{sku_obj.codigo}" atualizado com sucesso!', 'success')

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

    produtos_vinculados = Produto.query.filter_by(sku_id=id).all()
    possui_estoque = any((produto.quantidade or 0) > 0 for produto in produtos_vinculados)

    if possui_estoque:
        flash('Não é possível excluir o SKU enquanto houver produtos com estoque vinculado a ele.', 'warning')
        return redirect(url_for('sku.gerenciar_sku'))

    patrimonios_vinculados = Patrimonio.query.filter_by(sku_id=id).count()
    if patrimonios_vinculados:
        flash('Não é possível excluir o SKU enquanto houver patrimônios vinculados a ele.', 'warning')
        return redirect(url_for('sku.gerenciar_sku'))
    
    try:
        for produto in produtos_vinculados:
            db.session.delete(produto)

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