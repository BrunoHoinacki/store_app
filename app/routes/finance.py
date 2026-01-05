from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app.models import Sale, SaleItem, Product
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from decimal import Decimal

finance = Blueprint('finance', __name__, url_prefix='/finance')

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
        total_sales = sum((Decimal(str(sale.total_amount)) for sale in sales), start=Decimal('0.00'))
        total_items = sum((item.quantity for sale in sales for item in sale.items), start=0)
        total_cost = sum((Decimal(str(item.quantity)) * Decimal(str(item.product.cost_price)) for sale in sales for item in sale.items), start=Decimal('0.00'))
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
                    revenue = Decimal(str(revenue or 0))
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
