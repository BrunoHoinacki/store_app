from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models import Product, Category
from app.forms import ProductForm
from app import db
import logging

products = Blueprint('products', __name__, url_prefix='/products')

@products.route('/products')
@login_required
def product_list():
    products_list = Product.query.all()
    return render_template('products/list.html', products=products_list)

@products.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    # Log do status da validação do formulário
    if form.validate_on_submit():
        # Verificando se o formulário passou pela validação
        logging.debug("Formulário validado com sucesso.")
        
        # Log dos dados do formulário
        logging.debug(f"Dados do formulário: {{"
                      f"'name': {form.name.data}, "
                      f"'description': {form.description.data}, "
                      f"'cost_price': {form.cost_price.data}, "
                      f"'sale_price': {form.sale_price.data}, "
                      f"'stock': {form.stock.data}, "
                      f"'category_id': {form.category_id.data} }}")

        try:
            product = Product(
                name=form.name.data,
                description=form.description.data,
                cost_price=float(form.cost_price.data),
                sale_price=float(form.sale_price.data),
                stock=form.stock.data,
                category_id=form.category_id.data
            )
            db.session.add(product)
            db.session.commit()

            # Log após o commit
            logging.debug(f"Produto '{form.name.data}' adicionado com sucesso.")
            
            flash('Produto adicionado com sucesso')
            return redirect(url_for('products.product_list'))
        
        except Exception as e:
            # Log de erro no commit
            logging.error(f"Erro ao salvar produto: {str(e)}")
            flash('Ocorreu um erro ao adicionar o produto. Tente novamente.')
    
    # Se o formulário não for válido, exibe os erros
    if form.errors:
        logging.error(f"Erros no formulário: {form.errors}")
        flash('Por favor, corrija os erros no formulário e tente novamente.')

    return render_template('products/add.html', form=form)

@products.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.cost_price = form.cost_price.data
        product.sale_price = form.sale_price.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data
        
        db.session.commit()
        flash('Produto atualizado com sucesso')
        return redirect(url_for('products.product_list'))
    
    return render_template('products/edit.html', form=form, product=product)

@products.route('/products/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso')
    return redirect(url_for('products.product_list'))

@products.route('/products/adjust-stock/<int:id>', methods=['POST'])
@login_required
def adjust_stock(id):
    product = Product.query.get_or_404(id)
    try:
        adjustment = int(request.form.get('adjustment', 0))
        if adjustment != 0:
            new_stock = product.stock + adjustment
            if new_stock < 0:
                flash('Erro: Estoque não pode ser negativo')
            else:
                product.stock = new_stock
                db.session.commit()
                flash(f'Estoque atualizado com sucesso. Novo estoque: {new_stock}')
    except ValueError:
        flash('Erro: Valor inválido')
    return redirect(url_for('products.product_list'))
