from app.models import Product, Sale, SaleItem, User, Category
from app import db
from datetime import datetime

def test_user_password_hashing(app):
    """Testa o hash de senha do usuário."""
    with app.app_context():
        u = User(username='susan')
        u.set_password('cat')
        assert u.check_password('cat')
        assert not u.check_password('dog')

def test_product_stock_management(app):
    """Testa a lógica de estoque do produto."""
    with app.app_context():
        category = Category.query.first()
        p = Product(name='Test Product', cost_price=10.0, sale_price=20.0, stock=100, category=category)
        db.session.add(p)
        db.session.commit()

        # Test remove stock
        p.remove_from_stock(10)
        assert p.stock == 90

        # Test add stock
        p.add_to_stock(20)
        assert p.stock == 110

        # Test adjust stock negative error
        try:
            p.remove_from_stock(200)
            assert False, "Should raise stock error"
        except ValueError:
            assert True

def test_product_profit_calculation(app):
    """Testa cálculos de lucro do produto."""
    with app.app_context():
        p = Product(name='Profit Test', cost_price=10.0, sale_price=30.0, stock=10)
        assert p.profit == 20.0
        assert p.profit_margin == 200.0  # (20/10)*100

def test_sale_calculations(app):
    """Testa cálculos de totais da venda."""
    with app.app_context():
        # Setup
        category = Category.query.first()
        user = User.query.first()
        p1 = Product(name='P1', cost_price=10, sale_price=20, stock=10, category=category)
        p2 = Product(name='P2', cost_price=20, sale_price=50, stock=10, category=category)
        db.session.add_all([p1, p2])
        db.session.commit()

        # Create Sale
        sale = Sale(payment_method='money', subtotal=0, total_amount=0, user_id=user.id)
        
        # Add items
        item1 = SaleItem(product=p1, quantity=2, price=p1.sale_price) # 40
        item2 = SaleItem(product=p2, quantity=1, price=p2.sale_price) # 50
        
        sale.items.extend([item1, item2])
        
        # Calculate totals
        subtotal = sum(i.quantity * i.price for i in sale.items)
        sale.subtotal = subtotal
        sale.total_amount = subtotal # Assuming no interest for this test
        
        db.session.add(sale)
        db.session.commit()

        assert sale.subtotal == 90.0
        assert sale.total_amount == 90.0
        assert sale.profit == (90.0 - (2*10 + 1*20)) # 90 - 40 = 50
