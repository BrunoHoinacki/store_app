import pytest
import os
import tempfile
from app import create_app, db
from app.models import User, Product, Category, Customer

@pytest.fixture
def app():
    """Cria uma instância do app para testes."""
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False  # Disable CSRF for testing
    })
    
    with app.app_context():
        db.create_all()
        # Create default user
        user = User(username='test_user')
        user.set_password('password123')
        db.session.add(user)
        
        # Create default category
        category = Category(name='Test Category')
        db.session.add(category)
        
        db.session.commit()
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Cria um cliente de teste."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Cria um runner para testar comandos CLI."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """Retorna um cliente autenticado."""
    client.post('/login', data={
        'username': 'test_user',
        'password': 'password123'
    }, follow_redirects=True)
    return client
