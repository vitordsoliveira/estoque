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

