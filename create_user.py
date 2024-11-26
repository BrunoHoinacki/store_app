from app import create_app, db
from app.models import User, Category
import webbrowser

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()
    
    # Create test user
    user = User(username='admin')
    user.set_password('admin')
    db.session.add(user)
    
    # Create some default categories
    categories = [
        'Eletrônicos',
        'Alimentos',
        'Bebidas',
        'Roupas',
        'Calçados',
        'Acessórios',
        'Livros',
        'Papelaria',
        'Higiene',
        'Limpeza'
    ]
    
    for cat_name in categories:
        category = Category(name=cat_name)
        db.session.add(category)
    
    db.session.commit()
    
    print("Usuário de teste criado:")
    print("Usuário: admin")
    print("Senha: admin")