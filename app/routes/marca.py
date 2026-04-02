from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from app.models import Marca, db

marca = Blueprint(
    'marca',
    __name__,
    url_prefix='/marca' 
)

@marca.route('/gerenciar_marca', methods=['GET'])
def gerenciar_marca():
    marcas = Marca.query.order_by(Marca.nome).all()
    return render_template('gerenciar_marca.html', marcas=marcas)

@marca.route('/cadastrar_marca', methods=['POST'])
def cadastrar_marca():
    nome_marca = request.form.get('nome').strip()

    if not nome_marca:
        flash('O nome da marca é obrigatório!', 'warning')
        return redirect(url_for('marca.gerenciar_marca'))

    try:
        marca_existente = Marca.query.filter_by(nome=nome_marca).first()
        if marca_existente:
            flash(f'A marca "{nome_marca}" já está cadastrada.', 'danger')
            return redirect(url_for('marca.gerenciar_marca'))

        nova_marca = Marca(nome=nome_marca)
        db.session.add(nova_marca)
        db.session.commit()

        flash('Marca cadastrada com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar marca: {str(e)}', 'danger')

    return redirect(url_for('marca.gerenciar_marca'))

@marca.route('/editar_marca/<int:id>', methods=['GET', 'POST'])
def editar_marca(id):
    marca = Marca.query.get(id)
    
    if not marca:
        flash('Marca não encontrada!', 'danger')
        return redirect(url_for('marca.gerenciar_marca'))
    
    if request.method == 'POST':
        nome_marca = request.form.get('nome').strip()
        
        if not nome_marca:
            flash('O nome da marca é obrigatório!', 'warning')
            return redirect(url_for('marca.gerenciar_marca'))
        
        try:
            marca_existente = Marca.query.filter_by(nome=nome_marca).filter(Marca.id != id).first()
            if marca_existente:
                flash(f'Já existe uma marca com o nome "{nome_marca}".', 'danger')
                return redirect(url_for('marca.gerenciar_marca'))
            
            marca.nome = nome_marca
            db.session.commit()
            flash('Marca atualizada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar marca: {str(e)}', 'danger')
        
        return redirect(url_for('marca.gerenciar_marca'))
    
    return redirect(url_for('marca.gerenciar_marca'))

@marca.route('/deletar_marca/<int:id>', methods=['POST'])
def deletar_marca(id):
    marca = Marca.query.get(id)
    
    if not marca:
        flash('Marca não encontrada!', 'danger')
        return redirect(url_for('marca.gerenciar_marca'))
    
    try:
        db.session.delete(marca)
        db.session.commit()
        flash('Marca deletada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar marca: {str(e)}', 'danger')
    
    return redirect(url_for('marca.gerenciar_marca'))