from flask import url_for
from app.models import Product, Category, Customer

def test_login_logout(client):
    """Testa fluxo de login e logout."""
    # Login
    response = client.post('/login', data={
        'username': 'test_user',
        'password': 'password123'
    }, follow_redirects=True)
    assert 'Dashboard' in response.get_data(as_text=True)

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert 'Login' in response.get_data(as_text=True)

def test_product_crud(auth_client, app):
    """Testa criação e listagem de produtos."""
    # Create
    response = auth_client.post('/products/products/add', data={
        'name': 'New Product',
        'description': 'Desc',
        'cost_price': '10.00',
        'sale_price': '20.00',
        'stock': '50',
        'category_id': '1'  # Assuming ID 1 exists from fixture
    }, follow_redirects=True)
    assert 'Produto adicionado com sucesso' in response.get_data(as_text=True)

    # List
    response = auth_client.get('/products/products')
    assert 'New Product' in response.get_data(as_text=True)

    # Edit
    with app.app_context():
        product = Product.query.filter_by(name='New Product').first()
        prod_id = product.id

    response = auth_client.post(f'/products/products/edit/{prod_id}', data={
        'name': 'Updated Product',
        'description': 'Desc',
        'cost_price': '10.00',
        'sale_price': '25.00',
        'stock': '50',
        'category_id': '1'
    }, follow_redirects=True)
    assert 'Produto atualizado com sucesso' in response.get_data(as_text=True)
    assert 'Updated Product' in response.get_data(as_text=True)

def test_customer_creation(auth_client):
    """Testa cadastro de clientes."""
    response = auth_client.post('/customers/new', data={
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123456789',
        'address': 'Test Address'
    }, follow_redirects=True)
    assert 'Cliente cadastrado com sucesso' in response.get_data(as_text=True)
    
    response = auth_client.get('/customers/')
    assert 'John Doe' in response.get_data(as_text=True)

def test_sales_flow(auth_client, app):
    """Testa o fluxo de venda (adicionar item, finalizar)."""
    # 1. Create a product first
    auth_client.post('/products/products/add', data={
        'name': 'Sale Product',
        'description': 'Desc',
        'cost_price': '50.00',
        'sale_price': '100.00',
        'stock': '10',
        'category_id': '1'
    }, follow_redirects=True)
    
    with app.app_context():
        product = Product.query.filter_by(name='Sale Product').first()
        product_id = product.id

    # 2. Add item to sale (AJAX)
    response = auth_client.post('/sales/add-item', data={
        'product_id': product_id,
        'quantity': 2
    })
    assert response.status_code == 200
    assert response.json['success'] == True
    
    # 3. Finalize sale
    response = auth_client.post('/sales/new', data={
        'customer_id': '0', # Optional
        'payment_method': 'money',
        'has_interest': 'n', # unchecked
        'notes': 'Test sale'
    }, follow_redirects=True)
    
    assert 'Venda realizada com sucesso' in response.get_data(as_text=True)
    # Verify stock reduction
    with app.app_context():
        p = Product.query.get(product_id)
        assert p.stock == 8 # 10 - 2
