import pytest
from app.models import Product, Sale, Category, Customer
from app import db
from datetime import datetime, timedelta

def test_sale_cancellation_flow(auth_client, app):
    """
    Testa o fluxo completo de cancelamento de venda:
    1. Cria produto e venda
    2. Cancela a venda
    3. Verifica se o estoque foi devolvido
    4. Verifica status da venda
    """
    # 1. Setup Data
    with app.app_context():
        # Create category
        cat = Category(name='Cancel Test Cat')
        db.session.add(cat)
        db.session.commit()
        
        # Create product with 10 stock
        prod = Product(name='Cancel Prod', cost_price=10, sale_price=20, stock=10, category_id=cat.id)
        db.session.add(prod)
        db.session.commit()
        prod_id = prod.id

    # 2. Make Sale (reduces stock to 8)
    auth_client.post('/sales/add-item', data={'product_id': prod_id, 'quantity': 2})
    auth_client.post('/sales/new', data={
        'customer_id': '0',
        'payment_method': 'money',
        'has_interest': 'n'
    }, follow_redirects=True)

    # Verify Stock is 8
    with app.app_context():
        p = Product.query.get(prod_id)
        assert p.stock == 8
        sale = Sale.query.filter_by(status='active').first()
        sale_id = sale.id

    # 3. Cancel Sale
    response = auth_client.post(f'/sales/cancel/{sale_id}', data={
        'reason': 'Customer changed mind'
    }, follow_redirects=True)
    
    assert 'Venda cancelada com sucesso' in response.get_data(as_text=True)

    # 4. Verify Stock Returned to 10
    with app.app_context():
        p = Product.query.get(prod_id)
        assert p.stock == 10
        
        s = Sale.query.get(sale_id)
        assert s.status == 'cancelled'
        assert s.cancellation_reason == 'Customer changed mind'

def test_finance_dashboard_filtering(auth_client, app):
    """
    Testa os filtros do dashboard financeiro.
    Cria vendas em diferentes datas e verifica se o filtro funciona.
    """
    with app.app_context():
        cat = Category(name='Finance Cat')
        db.session.add(cat)
        db.session.commit()
        
        p = Product(name='Finance Prod', cost_price=10, sale_price=100, stock=100, category_id=cat.id)
        db.session.add(p)
        db.session.commit()
        
        user_id = 1 # Admin from fixture
        
        # Sale 1: Today (Money)
        s1 = Sale(
            date=datetime.now(), 
            subtotal=100, total_amount=100, 
            payment_method='money', 
            user_id=user_id,
            status='active'
        )
        # Sale 2: 8 days ago (Credit)
        s2 = Sale(
            date=datetime.now() - timedelta(days=8), 
            subtotal=200, total_amount=200, 
            payment_method='credit_card', 
            user_id=user_id,
            status='active'
        )
        
        db.session.add_all([s1, s2])
        db.session.commit()

    # Filter: Today
    response = auth_client.get('/finance/?period=today')
    html = response.get_data(as_text=True)
    assert 'R$ 100.00' in html # Total sales (template uses %.2f which outputs dot)
    assert 'Dinheiro' in html
    # Should NOT satisfy checks for s2 logic if we were parsing strictly, 
    # but simplest check is seeing the today total.

    # Filter: All Time (or 30 days)
    response = auth_client.get('/finance/?period=30days')
    html = response.get_data(as_text=True)
    # Total should be roughly 300 (100 + 200)
    # Note: formatting might be "300.00"
    assert 'R$ 300.00' in html

def test_manual_stock_adjustment(auth_client, app):
    """
    Testa o ajuste manual de estoque pela rota de produtos.
    """
    with app.app_context():
        cat = Category(name='Stock Cat')
        db.session.add(cat)
        db.session.commit()
        p = Product(name='Stock Prod', cost_price=10, sale_price=20, stock=50, category_id=cat.id)
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # Add 10 stock
    response = auth_client.post(f'/products/products/adjust-stock/{pid}', data={
        'adjustment': '10'
    }, follow_redirects=True)
    
    assert 'Estoque atualizado com sucesso' in response.get_data(as_text=True)
    assert '60' in response.get_data(as_text=True) # New stock visible in list

    # Remove 5 stock
    response = auth_client.post(f'/products/products/adjust-stock/{pid}', data={
        'adjustment': '-5'
    }, follow_redirects=True)
    
    with app.app_context():
        p = Product.query.get(pid)
        assert p.stock == 55
