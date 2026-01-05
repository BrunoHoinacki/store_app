from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem, TempSaleItem, Customer
from app.forms import SaleForm
from app import db
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import uuid

sales = Blueprint('sales', __name__, url_prefix='/sales')

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
                        subtotal=subtotal,
                        total_amount=total_amount,
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
    sales_list = Sale.query.order_by(Sale.date.desc()).all()
    return render_template('sales/sale_history.html', sales=sales_list)

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
                'price': float(product.sale_price),
                'subtotal': float(temp_item.subtotal)
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
            'subtotal': float(temp_item.subtotal)
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
        'price': float(item.price),
        'subtotal': float(item.subtotal)
    } for item in items])

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
        'price': float(p.sale_price)
    } for p in products])
