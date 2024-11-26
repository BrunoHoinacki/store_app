from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Product, Category, Sale, SaleItem, TempSaleItem, Customer
from app.forms import LoginForm, ProductForm, SaleForm, CategoryForm, CustomerForm
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, or_
import uuid
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# Create blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
products = Blueprint('products', __name__, url_prefix='/products')
sales = Blueprint('sales', __name__, url_prefix='/sales')
categories = Blueprint('categories', __name__, url_prefix='/categories')
finance = Blueprint('finance', __name__, url_prefix='/finance')
customers = Blueprint('customers', __name__, url_prefix='/customers')

# Auth routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Usuário ou senha inválidos')
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Main routes
@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Informações de produtos
    products_count = Product.query.count()
    low_stock = Product.query.filter(Product.stock < 10).count()
    out_of_stock = Product.query.filter(Product.stock == 0).count()
    
    # Vendas recentes
    recent_sales = Sale.query.filter_by(status='active').order_by(Sale.date.desc()).limit(5).all()
    
    # Vendas de hoje
    today = datetime.now().date()
    today_sales = Sale.query.filter(
        func.date(Sale.date) == today,
        Sale.status == 'active'
    ).all()
    today_total = sum(sale.total_amount for sale in today_sales)
    today_count = len(today_sales)
    
    # Vendas dos últimos 7 dias
    last_week = today - timedelta(days=7)
    week_sales = Sale.query.filter(
        func.date(Sale.date) >= last_week,
        Sale.status == 'active'
    ).all()
    week_total = sum(sale.total_amount for sale in week_sales)
    week_count = len(week_sales)
    
    # Produtos mais vendidos (últimos 30 dias)
    last_month = today - timedelta(days=30)
    top_products = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity'),
        func.sum(SaleItem.quantity * SaleItem.price).label('total_revenue')
    ).join(SaleItem).join(Sale).filter(
        func.date(Sale.date) >= last_month,
        Sale.status == 'active'
    ).group_by(Product.id).order_by(
        func.sum(SaleItem.quantity).desc()
    ).limit(5).all()
    
    # Total de clientes
    customers_count = Customer.query.filter_by(active=True).count()
    
    return render_template('dashboard.html',
                         products_count=products_count,
                         low_stock=low_stock,
                         out_of_stock=out_of_stock,
                         recent_sales=recent_sales,
                         today_total=today_total,
                         today_count=today_count,
                         week_total=week_total,
                         week_count=week_count,
                         top_products=top_products,
                         customers_count=customers_count)

# Product routes
@products.route('/products')
@login_required
def product_list():
    products = Product.query.all()
    return render_template('products/list.html', products=products)

@products.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            cost_price=form.cost_price.data,
            sale_price=form.sale_price.data,
            stock=form.stock.data,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Produto adicionado com sucesso')
        return redirect(url_for('products.product_list'))
    
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

# Sales routes
@sales.route('/new', methods=['GET', 'POST'])
@login_required
def new_sale():
    form = SaleForm()
    products = Product.query.order_by(Product.name).all()
    
    if 'sale_session_id' not in session:
        session['sale_session_id'] = str(uuid.uuid4())
    
    if request.method == 'POST':
        try:
            # Buscar itens temporários antes de validar o formulário
            items = TempSaleItem.query.filter_by(session_id=session['sale_session_id']).all()
            if not items:
                flash('Adicione pelo menos um produto à venda', 'error')
                return render_template('sales/new_sale.html', form=form, products=products)
            
            if form.validate_on_submit():
                try:
                    # Verificar estoque antes de prosseguir
                    for item in items:
                        if item.product.stock < item.quantity:
                            flash(f'Estoque insuficiente para o produto {item.product.name}. Disponível: {item.product.stock}', 'error')
                            return render_template('sales/new_sale.html', form=form, products=products)

                    # Calcular valores usando Decimal para maior precisão
                    subtotal = Decimal('0.0')
                    for item in items:
                        item_subtotal = Decimal(str(item.price)) * Decimal(str(item.quantity))
                        subtotal += item_subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    total_amount = subtotal
                    
                    if form.has_interest.data and form.interest_rate.data > 0:
                        interest_rate = Decimal(str(form.interest_rate.data)) / Decimal('100')
                        total_amount = (subtotal * (Decimal('1.0') + interest_rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    # Mapear método de pagamento para o valor correto
                    payment_method_map = {
                        'money': 'money',
                        'credit_card': 'credit_card',
                        'debit_card': 'debit_card',
                        'pix': 'pix'
                    }
                    payment_method = payment_method_map.get(form.payment_method.data, form.payment_method.data)
                    
                    # Criar nova venda
                    sale = Sale(
                        date=datetime.now(),
                        customer_id=form.customer_id.data if form.customer_id.data and form.customer_id.data != '0' else None,
                        payment_method=payment_method,
                        installments=form.installments.data if form.installments.data else 1,
                        has_interest=form.has_interest.data,
                        interest_rate=float(form.interest_rate.data) if form.has_interest.data else 0,
                        subtotal=float(subtotal),
                        total_amount=float(total_amount),
                        notes=form.notes.data,
                        user_id=current_user.id
                    )
                    
                    # Processar cada item
                    for temp_item in items:
                        try:
                            sale_item = SaleItem(
                                product=temp_item.product,
                                quantity=temp_item.quantity,
                                price=temp_item.price
                            )
                            temp_item.product.remove_from_stock(temp_item.quantity)
                            sale.items.append(sale_item)
                            db.session.delete(temp_item)
                        except ValueError as e:
                            db.session.rollback()
                            flash(f'Erro ao processar o produto {temp_item.product.name}: {str(e)}', 'error')
                            return render_template('sales/new_sale.html', form=form, products=products)
                    
                    try:
                        # Salvar no banco de dados
                        db.session.add(sale)
                        db.session.commit()
                        
                        # Limpar a sessão
                        session.pop('sale_session_id', None)
                        flash('Venda realizada com sucesso', 'success')
                        return redirect(url_for('sales.sale_history'))
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f'Erro ao processar venda: {str(e)}')
                        flash(f'Erro ao salvar a venda no banco de dados: {str(e)}', 'error')
                        return render_template('sales/new_sale.html', form=form, products=products)
                        
                except (ValueError, TypeError, InvalidOperation) as e:
                    flash(f'Erro ao processar os valores da venda: {str(e)}', 'error')
                    return render_template('sales/new_sale.html', form=form, products=products)
            else:
                for field, errors in form.errors.items():
                    if isinstance(errors, (list, tuple)):
                        error_messages = [str(error) for error in errors]
                        flash(f"Erro no campo {field}: {', '.join(error_messages)}", 'error')
                    else:
                        flash(f"Erro no campo {field}: {str(errors)}", 'error')
        except Exception as e:
            flash(f'Erro inesperado ao processar a venda: {str(e)}', 'error')
            current_app.logger.error(f'Erro inesperado ao processar a venda: {str(e)}')
            return render_template('sales/new_sale.html', form=form, products=products)
    
    return render_template('sales/new_sale.html', form=form, products=products)

@sales.route('/history')
@login_required
def sale_history():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return render_template('sales/sale_history.html', sales=sales)

@sales.route('/cancel/<int:id>', methods=['POST'])
@login_required
def cancel_sale(id):
    sale = Sale.query.get_or_404(id)
    reason = request.form.get('reason', '')
    
    if sale.is_cancelled:
        flash('Esta venda já está cancelada')
        return redirect(url_for('sales.sale_history'))
    
    try:
        print(f"Iniciando cancelamento da venda {id}")
        # Guarda informações para verificação
        items_info = [(item.product.id, item.product.stock, item.quantity) 
                     for item in sale.items]
        
        sale.cancel(reason)
        
        # Verifica se os estoques foram atualizados corretamente
        for prod_id, old_stock, qty in items_info:
            product = Product.query.get(prod_id)
            expected_stock = old_stock + qty
            if product.stock != expected_stock:
                raise Exception(f"Erro na atualização do estoque do produto {product.name}")
        
        db.session.commit()
        print(f"Venda {id} cancelada com sucesso")
        flash('Venda cancelada com sucesso')
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao cancelar venda: {str(e)}")
        flash(f'Erro ao cancelar venda: {str(e)}')
    
    return redirect(url_for('sales.sale_history'))

@sales.route('/add-item', methods=['POST'])
@login_required
def add_sale_item():
    try:
        if 'sale_session_id' not in session:
            session['sale_session_id'] = str(uuid.uuid4())

        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        
        product = Product.query.get_or_404(product_id)
        
        if product.stock < quantity:
            return jsonify({'success': False, 'message': f'Estoque insuficiente para o produto {product.name}'}), 400
            
        temp_item = TempSaleItem(
            session_id=session['sale_session_id'],
            product_id=product_id,
            quantity=quantity,
            price=product.sale_price
        )
        
        db.session.add(temp_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'item': {
                'id': temp_item.id,
                'product_name': product.name,
                'quantity': quantity,
                'price': product.sale_price,
                'subtotal': temp_item.subtotal
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@sales.route('/remove-item/<int:item_id>', methods=['POST'])
@login_required
def remove_sale_item(item_id):
    try:
        temp_item = TempSaleItem.query.get_or_404(item_id)
        if temp_item.session_id != session.get('sale_session_id'):
            return jsonify({'success': False, 'message': 'Item não pertence a esta sessão'}), 403
            
        db.session.delete(temp_item)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@sales.route('/update-item/<int:item_id>', methods=['POST'])
@login_required
def update_sale_item(item_id):
    try:
        quantity = int(request.form.get('quantity', 1))
        temp_item = TempSaleItem.query.get_or_404(item_id)
        
        if temp_item.session_id != session.get('sale_session_id'):
            return jsonify({'success': False, 'message': 'Item não pertence a esta sessão'}), 403
            
        if temp_item.product.stock < quantity:
            return jsonify({'success': False, 'message': f'Estoque insuficiente para o produto {temp_item.product.name}'}), 400
            
        temp_item.quantity = quantity
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subtotal': temp_item.subtotal
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@sales.route('/get-items', methods=['GET'])
@login_required
def get_sale_items():
    if 'sale_session_id' not in session:
        return jsonify([])
        
    items = TempSaleItem.query.filter_by(session_id=session['sale_session_id']).all()
    return jsonify([{
        'id': item.id,
        'product_name': item.product.name,
        'quantity': item.quantity,
        'price': item.price,
        'subtotal': item.subtotal
    } for item in items])

@sales.route('/customers/search')
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

# Finance routes
@finance.route('/')
@login_required
def finance_dashboard():
    try:
        # Obter parâmetros dos filtros
        period = request.args.get('period', 'today')
        payment_method = request.args.get('payment_method', '')
        min_value = request.args.get('min_value', type=float)
        max_value = request.args.get('max_value', type=float)
        
        # Definir o período de datas
        today = datetime.now()
        if period == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif period == '7days':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == '30days':
            start_date = today - timedelta(days=30)
            end_date = today
        elif period == 'custom':
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except (ValueError, TypeError):
                start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = today
        else:  # all
            start_date = datetime.min
            end_date = today
        
        # Construir a query base
        query = Sale.query.filter(Sale.status == 'active')
        
        # Aplicar filtros
        if period != 'all':
            query = query.filter(Sale.date.between(start_date, end_date))
        
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        
        if min_value is not None:
            query = query.filter(Sale.total_amount >= min_value)
        
        if max_value is not None:
            query = query.filter(Sale.total_amount <= max_value)
        
        # Executar a query
        sales = query.order_by(Sale.date.desc()).all()
        
        # Calcular totais
        total_sales = sum(sale.total_amount for sale in sales)
        total_items = sum(item.quantity for sale in sales for item in sale.items)
        total_cost = sum(item.quantity * item.product.cost_price for sale in sales for item in sale.items)
        total_profit = total_sales - total_cost

        # Calcular totais por método de pagamento
        payment_methods = {}
        for sale in sales:
            method = sale.payment_method
            if method not in payment_methods:
                payment_methods[method] = {'count': 0, 'total': 0}
            payment_methods[method]['count'] += 1
            payment_methods[method]['total'] += sale.total_amount

        # Obter produtos mais vendidos
        top_products_list = []
        try:
            top_products_query = db.session.query(
                Product,
                func.sum(SaleItem.quantity).label('total_quantity'),
                func.sum(SaleItem.price * SaleItem.quantity).label('total_revenue')
            ).join(SaleItem).join(Sale).filter(
                Sale.status == 'active'
            )
            
            if period != 'all':
                top_products_query = top_products_query.filter(Sale.date.between(start_date, end_date))
            
            top_products_data = top_products_query.group_by(Product).order_by(
                func.sum(SaleItem.quantity * SaleItem.price).desc()
            ).limit(5).all()

            for product, quantity, revenue in top_products_data:
                if product:  # Garantir que o produto existe
                    quantity = int(quantity or 0)
                    revenue = float(revenue or 0)
                    top_products_list.append({
                        'product': product,
                        'quantity': quantity,
                        'revenue': revenue
                    })
        except Exception as e:
            current_app.logger.error(f"Erro ao obter produtos mais vendidos: {str(e)}")

        return render_template('finance/dashboard.html',
            sales=sales,
            total_sales=total_sales,
            total_items=total_items,
            total_cost=total_cost,
            total_profit=total_profit,
            payment_methods=payment_methods,
            top_products_list=top_products_list,
            period=period,
            payment_method=payment_method,
            min_value=min_value,
            max_value=max_value,
            start_date=start_date if period == 'custom' else None,
            end_date=end_date if period == 'custom' else None
        )
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard financeiro: {str(e)}")
        flash('Erro ao carregar o dashboard financeiro: ' + str(e), 'error')
        return redirect(url_for('main.dashboard'))

# Categories routes
@categories.route('/categories')
@login_required
def category_list():
    categories = Category.query.all()
    return render_template('categories/list.html', categories=categories)

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

# Rotas para Clientes
@customers.route('/')
@login_required
def customer_list():
    active = request.args.get('active', 'true').lower() == 'true'
    customers = Customer.query.filter_by(active=active).order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers, active=active)

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
    sales = Sale.query.filter_by(customer_id=id).order_by(Sale.date.desc()).all()
    return render_template('customers/view.html', customer=customer, sales=sales)

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
            'email': customer.email or ''
        } for customer in paginated_customers.items],
        'has_next': paginated_customers.has_next
    })

@sales.route('/api/products')
@login_required
def get_products():
    search = request.args.get('search', '')
    products = Product.query.filter(
        Product.name.ilike(f'%{search}%')
    ).all()
    return jsonify([{
        'id': p.id,
        'text': f'{p.name} (R$ {p.sale_price:.2f}) - Estoque: {p.stock}',
        'stock': p.stock,
        'price': p.sale_price
    } for p in products])