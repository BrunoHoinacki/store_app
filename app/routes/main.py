from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Product, Sale, SaleItem, Customer
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
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
