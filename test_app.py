from app import create_app, db

print("Teste de inicialização")
app = create_app()

with app.app_context():
    print("Testando conexão com banco de dados...")
    try:
        db.create_all()
        print("Banco de dados criado com sucesso!")
    except Exception as e:
        print(f"Erro ao criar banco de dados: {e}")

"""
Testes automatizados para o Store App.
Este módulo contém testes unitários e de integração para as principais funcionalidades do sistema.
"""

import os
import tempfile
import pytest
from app import create_app, db
from app.models import User, Product, Category, Customer

@pytest.fixture
def app():
    """Cria uma instância do app para testes."""
    # Cria um arquivo temporário para o banco de dados
    db_fd, db_path = tempfile.mkstemp()
    
    # Configurações de teste
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False
    })
    
    # Cria as tabelas do banco de dados
    with app.app_context():
        db.create_all()
        
        # Cria um usuário de teste
        user = User(username='test_user')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    yield app
    
    # Limpeza após os testes
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

def test_login_page(client):
    """Testa se a página de login está acessível."""
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Login' in rv.data

def test_login(client):
    """Testa o processo de login."""
    rv = client.post('/login', data={
        'username': 'test_user',
        'password': 'password123'
    }, follow_redirects=True)
    assert b'Dashboard' in rv.data

def test_invalid_login(client):
    """Testa tentativa de login inválido."""
    rv = client.post('/login', data={
        'username': 'invalid_user',
        'password': 'wrong_password'
    }, follow_redirects=True)
    assert b'Invalid username or password' in rv.data

def test_protected_routes(client):
    """Testa se rotas protegidas redirecionam para login."""
    routes = ['/', '/products', '/sales', '/customers']
    for route in routes:
        rv = client.get(route)
        assert rv.status_code == 302  # Redirecionamento
        assert b'login' in rv.data.lower()