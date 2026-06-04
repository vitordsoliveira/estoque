from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from app.models import Familia, db

familia = Blueprint(
    'familia',
    __name__,
    url_prefix='/familia' 
)

@familia.route('/gerenciar_familia', methods=['GET'])
def gerenciar_familia():
    familias = Familia.query.order_by(Familia.nome).all()
    return render_template('gerenciar_familia.html', familias=familias)

@familia.route('/cadastrar_familia', methods=['POST'])
def cadastrar_familia():
    nome_familia = request.form.get('nome').strip()

    if not nome_familia:
        flash('O nome da familia é obrigatório!', 'warning')
        return redirect(url_for('familia.gerenciar_familia'))

    try:
        familia_existente = Familia.query.filter_by(nome=nome_familia).first()
        if familia_existente:
            flash(f'A familia "{nome_familia}" já está cadastrada.', 'danger')
            return redirect(url_for('familia.gerenciar_familia'))

        nova_familia = Familia(nome=nome_familia)
        db.session.add(nova_familia)
        db.session.commit()

        flash('familia cadastrada com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar familia: {str(e)}', 'danger')

    return redirect(url_for('familia.gerenciar_familia'))

@familia.route('/editar_familia/<int:id>', methods=['GET', 'POST'])
def editar_familia(id):
    familia = Familia.query.get(id)
    
    if not familia:
        flash('Familia não encontrada!', 'danger')
        return redirect(url_for('familia.gerenciar_familia'))
    
    if request.method == 'POST':
        nome_familia = request.form.get('nome').strip()
        
        if not nome_familia:
            flash('O nome da familia é obrigatório!', 'warning')
            return redirect(url_for('familia.gerenciar_familia'))
        
        try:
            # Verifica se já existe outra familia com esse nome
            familia_existente = Familia.query.filter_by(nome=nome_familia).filter(Familia.id != id).first()
            if familia_existente:
                flash(f'Já existe uma familia com o nome "{nome_familia}".', 'danger')
                return redirect(url_for('familia.gerenciar_familia'))
            
            familia.nome = nome_familia
            db.session.commit()
            flash('Familia atualizada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar familia: {str(e)}', 'danger')
        
        return redirect(url_for('familia.gerenciar_familia'))
    
    return redirect(url_for('familia.gerenciar_familia'))

@familia.route('/deletar_familia/<int:id>', methods=['POST'])
def deletar_familia(id):
    familia = Familia.query.get(id)
    
    if not familia:
        flash('Familia não encontrada!', 'danger')
        return redirect(url_for('familia.gerenciar_familia'))

    if familia.tipos:
        flash('Não é possível excluir a família enquanto houver tipos vinculados a ela.', 'warning')
        return redirect(url_for('familia.gerenciar_familia'))

    if familia.skus:
        flash('Não é possível excluir a família enquanto houver SKUs vinculados a ela.', 'warning')
        return redirect(url_for('familia.gerenciar_familia'))
    
    try:
        db.session.delete(familia)
        db.session.commit()
        flash('Familia deletada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar familia: {str(e)}', 'danger')
    
    return redirect(url_for('familia.gerenciar_familia'))