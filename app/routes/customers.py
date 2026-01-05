from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.models import Customer, Sale
from app.forms import CustomerForm
from app import db
from sqlalchemy import or_

customers = Blueprint('customers', __name__, url_prefix='/customers')

@customers.route('/')
@login_required
def customer_list():
    active = request.args.get('active', 'true').lower() == 'true'
    customers_list = Customer.query.filter_by(active=active).order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers_list, active=active)

@customers.route('/inactivate/<int:id>', methods=['POST'])
@login_required
def inactivate_customer(id):
    customer = Customer.query.get_or_404(id)
    reason = request.form.get('reason', '')
    
    if customer.sales:
        customer.inactivate(reason)
        db.session.commit()
        flash('Cliente inativado com sucesso.', 'success')
    else:
        flash('Não é possível inativar um cliente sem histórico de compras.', 'error')
    
    return redirect(url_for('customers.customer_list', active=True))

@customers.route('/reactivate/<int:id>', methods=['POST'])
@login_required
def reactivate_customer(id):
    customer = Customer.query.get_or_404(id)
    customer.reactivate()
    db.session.commit()
    flash('Cliente reativado com sucesso.', 'success')
    return redirect(url_for('customers.customer_list', active=False))

@customers.route('/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            notes=form.notes.data
        )
        db.session.add(customer)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('customers.customer_list'))
    return render_template('customers/form.html', form=form, title='Novo Cliente')

@customers.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(obj=customer)
    form.id.data = str(customer.id)
    
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        customer.notes = form.notes.data
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('customers.customer_list'))
    
    return render_template('customers/form.html', form=form, title='Editar Cliente')

@customers.route('/view/<int:id>')
@login_required
def view_customer(id):
    customer = Customer.query.get_or_404(id)
    customer_sales = Sale.query.filter_by(customer_id=id).order_by(Sale.date.desc()).all()
    return render_template('customers/view.html', customer=customer, sales=customer_sales)

@customers.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    if customer.sales:
        flash('Não é possível excluir um cliente que possui vendas!', 'error')
        return redirect(url_for('customers.customer_list'))
    
    db.session.delete(customer)
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('customers.customer_list'))

@customers.route('/search')
def search_customers():
    """Endpoint para busca de clientes via AJAX para o Select2"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Customer.query
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )

    paginated_customers = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [{
            'id': customer.id,
            'name': customer.name,
            'email': customer.email
        } for customer in paginated_customers.items],
        'has_next': paginated_customers.has_next
    })
