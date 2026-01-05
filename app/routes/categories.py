from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.models import Category
from app.forms import CategoryForm
from app import db

categories = Blueprint('categories', __name__, url_prefix='/categories')

@categories.route('/categories')
@login_required
def category_list():
    categories_list = Category.query.all()
    return render_template('categories/list.html', categories=categories_list)

@categories.route('/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        try:
            db.session.add(category)
            db.session.commit()
            flash('Categoria adicionada com sucesso')
            return redirect(url_for('categories.category_list'))
        except:
            db.session.rollback()
            flash('Erro: Esta categoria já existe')
    return render_template('categories/add.html', form=form)

@categories.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        try:
            category.name = form.name.data
            db.session.commit()
            flash('Categoria atualizada com sucesso')
            return redirect(url_for('categories.category_list'))
        except:
            db.session.rollback()
            flash('Erro: Esta categoria já existe')
    
    return render_template('categories/edit.html', form=form, category=category)

@categories.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.products:
        flash('Não é possível excluir: Existem produtos nesta categoria')
        return redirect(url_for('categories.category_list'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Categoria excluída com sucesso')
    return redirect(url_for('categories.category_list'))
