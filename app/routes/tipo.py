from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from app.models import Familia, Tipo, db

tipo = Blueprint(
    'tipo',
    __name__,
    url_prefix='/tipo' 
)

@tipo.route('/gerenciar_tipo', methods=['GET'])
def gerenciar_tipo():
    # Busca todos os tipos e todas as famílias para preencher o SELECT
    tipos = Tipo.query.order_by(Tipo.nome).all()
    familias = Familia.query.order_by(Familia.nome).all()
    
    return render_template('gerenciar_tipo.html', tipos=tipos, familias=familias)

@tipo.route('/cadastrar_tipo', methods=['POST'])
def cadastrar_tipo():
    nome_tipo = request.form.get('nome').strip()
    familia_id = request.form.get('familia_id') # Captura o ID do select

    if not nome_tipo or not familia_id:
        flash('O nome do tipo e a família são obrigatórios!', 'warning')
        return redirect(url_for('tipo.gerenciar_tipo'))

    try:
        # Verifica se já existe esse tipo NAQUELA família específica
        tipo_existente = Tipo.query.filter_by(nome=nome_tipo, familia_id=familia_id).first()
        
        if tipo_existente:
            flash(f'O tipo "{nome_tipo}" já está cadastrado nesta família.', 'danger')
            return redirect(url_for('tipo.gerenciar_tipo'))

        # CRIAÇÃO: Passamos o familia_id aqui
        nova_tipo = Tipo(nome=nome_tipo, familia_id=int(familia_id))
        
        db.session.add(nova_tipo)
        db.session.commit()

        flash('Tipo cadastrado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar tipo: {str(e)}', 'danger')

    return redirect(url_for('tipo.gerenciar_tipo'))

@tipo.route('/editar_tipo/<int:id>', methods=['GET', 'POST'])
def editar_tipo(id):
    tipo_obj = Tipo.query.get(id)
    
    if not tipo_obj:
        flash('Tipo não encontrado!', 'danger')
        return redirect(url_for('tipo.gerenciar_tipo'))
    
    if request.method == 'POST':
        nome_tipo = request.form.get('nome').strip()
        familia_id = request.form.get('familia_id')
        
        if not nome_tipo or not familia_id:
            flash('O nome do tipo e a família são obrigatórios!', 'warning')
            return redirect(url_for('tipo.gerenciar_tipo'))
        
        try:
            tipo_existente = Tipo.query.filter_by(nome=nome_tipo, familia_id=familia_id).filter(Tipo.id != id).first()
            if tipo_existente:
                flash(f'Já existe um tipo com o nome "{nome_tipo}" nesta família.', 'danger')
                return redirect(url_for('tipo.gerenciar_tipo'))
            
            tipo_obj.nome = nome_tipo
            tipo_obj.familia_id = int(familia_id)
            db.session.commit()
            flash('Tipo atualizado com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tipo: {str(e)}', 'danger')
        
        return redirect(url_for('tipo.gerenciar_tipo'))
    
    return redirect(url_for('tipo.gerenciar_tipo'))

@tipo.route('/deletar_tipo/<int:id>', methods=['POST'])
def deletar_tipo(id):
    tipo_obj = Tipo.query.get(id)
    
    if not tipo_obj:
        flash('Tipo não encontrada!', 'danger')
        return redirect(url_for('tipo.gerenciar_tipo'))

    if tipo_obj.skus:
        flash('Não é possível excluir o tipo enquanto houver SKUs vinculados a ele.', 'warning')
        return redirect(url_for('tipo.gerenciar_tipo'))
    
    try:
        db.session.delete(tipo_obj)
        db.session.commit()
        flash('Tipo deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar tipo: {str(e)}', 'danger')
    
    return redirect(url_for('tipo.gerenciar_tipo'))