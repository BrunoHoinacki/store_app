# Imports da biblioteca padrão
import os
from datetime import datetime

# Imports da aplicação
from app import create_app, db
from app.models import User, Category, Product, Customer, Sale, SaleItem

print("Iniciando script...")
print(f"Diretório atual: {os.getcwd()}")

app = create_app()

def init_db():
    """Inicializa o banco de dados com dados de teste"""
    print("Iniciando inicialização do banco...")
    with app.app_context():
        # Recria todas as tabelas
        print("Removendo tabelas existentes...")
        db.drop_all()
        print("Criando novas tabelas...")
        db.create_all()
        
        print("Criando usuário de teste...")
        # Cria usuário admin
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        
        print("Criando categorias...")
        # Cria categorias
        categories = [
            Category(name='Smartphones'),
            Category(name='Notebooks'),
            Category(name='Tablets'),
            Category(name='Acessórios'),
            Category(name='Smart TVs')
        ]
        
        for category in categories:
            db.session.add(category)
        db.session.commit()

        print("Criando produtos de exemplo...")
        # Cria alguns produtos de exemplo
        products = [
            # Smartphones
            Product(
                name='iPhone 14 Pro',
                description='Apple iPhone 14 Pro 256GB',
                category=categories[0],
                cost_price=6500.00,
                sale_price=8999.00,
                stock=10
            ),
            Product(
                name='Samsung Galaxy S23',
                description='Samsung Galaxy S23 Ultra 512GB',
                category=categories[0],
                cost_price=5800.00,
                sale_price=7999.00,
                stock=8
            ),
            # Notebooks
            Product(
                name='MacBook Pro M2',
                description='Apple MacBook Pro M2 14" 512GB',
                category=categories[1],
                cost_price=12000.00,
                sale_price=14999.00,
                stock=5
            ),
            Product(
                name='Dell XPS 13',
                description='Dell XPS 13 Plus i7 16GB 512GB',
                category=categories[1],
                cost_price=8500.00,
                sale_price=10999.00,
                stock=7
            ),
            # Tablets
            Product(
                name='iPad Pro M2',
                description='Apple iPad Pro M2 11" 256GB',
                category=categories[2],
                cost_price=6000.00,
                sale_price=7499.00,
                stock=12
            ),
            # Acessórios
            Product(
                name='AirPods Pro 2',
                description='Apple AirPods Pro 2ª Geração',
                category=categories[3],
                cost_price=1800.00,
                sale_price=2499.00,
                stock=20
            ),
            # Smart TVs
            Product(
                name='Samsung Neo QLED',
                description='Samsung Smart TV 65" Neo QLED 4K',
                category=categories[4],
                cost_price=7000.00,
                sale_price=9499.00,
                stock=3
            )
        ]
        
        for product in products:
            db.session.add(product)
        db.session.commit()

        print("Criando clientes de exemplo...")
        # Cria alguns clientes de exemplo
        customers = [
            Customer(
                name='João Silva',
                email='joao.silva@email.com',
                phone='(11) 98765-4321',
                address='Rua das Flores, 123 - São Paulo/SP',
                notes='Cliente VIP'
            ),
            Customer(
                name='Maria Santos',
                email='maria.santos@email.com',
                phone='(11) 91234-5678',
                address='Av. Paulista, 1000 - São Paulo/SP',
                notes='Prefere contato por WhatsApp'
            ),
            Customer(
                name='Pedro Oliveira',
                email='pedro.oliveira@email.com',
                phone='(11) 97777-8888',
                address='Rua Augusta, 500 - São Paulo/SP',
                notes='Cliente corporativo'
            ),
            Customer(
                name='Ana Costa',
                email='ana.costa@email.com',
                phone='(11) 96666-7777',
                address='Rua Oscar Freire, 200 - São Paulo/SP',
                notes='Cliente desde 2022'
            ),
            Customer(
                name='Carlos Ferreira',
                email='carlos.ferreira@email.com',
                phone='(11) 95555-6666',
                address='Alameda Santos, 800 - São Paulo/SP',
                notes='Sempre compra à vista'
            )
        ]
        
        for customer in customers:
            db.session.add(customer)
        db.session.commit()

        print("Criando vendas de exemplo...")
        # Cria algumas vendas de exemplo
        sales = [
            # Venda 1 - iPhone para João
            Sale(
                customer=customers[0],
                payment_method='credit_card',
                installments=12,
                has_interest=True,
                interest_rate=1.99,
                subtotal=8999.00,
                total_amount=9500.00,
                notes='Parcelado em 12x',
                date=datetime(2024, 1, 15, 14, 30),
                user_id=admin.id
            ),
            # Venda 2 - MacBook para Maria
            Sale(
                customer=customers[1],
                payment_method='debit_card',
                installments=1,
                subtotal=14999.00,
                total_amount=14999.00,
                notes='Pagamento à vista no débito',
                date=datetime(2024, 1, 16, 10, 45),
                user_id=admin.id
            ),
            # Venda 3 - AirPods para Pedro
            Sale(
                customer=customers[2],
                payment_method='pix',
                installments=1,
                subtotal=2499.00,
                total_amount=2499.00,
                notes='Pagamento via PIX',
                date=datetime(2024, 1, 17, 16, 20),
                user_id=admin.id
            ),
            # Venda 4 - TV para Ana
            Sale(
                customer=customers[3],
                payment_method='credit_card',
                installments=6,
                has_interest=True,
                interest_rate=1.99,
                subtotal=9499.00,
                total_amount=9800.00,
                notes='Parcelado em 6x',
                date=datetime(2024, 1, 18, 11, 15),
                user_id=admin.id
            ),
            # Venda 5 - iPad para Carlos
            Sale(
                customer=customers[4],
                payment_method='money',
                installments=1,
                subtotal=7499.00,
                total_amount=7499.00,
                notes='Pagamento em dinheiro',
                date=datetime(2024, 1, 19, 15, 30),
                user_id=admin.id
            )
        ]

        # Adiciona as vendas e seus itens
        for i, sale in enumerate(sales):
            db.session.add(sale)
            db.session.commit()  # Commit para gerar o ID da venda

            # Cria os itens para cada venda
            if i == 0:  # Venda do iPhone
                sale_item = SaleItem(
                    sale=sale,
                    product=products[0],  # iPhone 14 Pro
                    quantity=1,
                    price=8999.00
                )
                products[0].remove_from_stock(1)
            elif i == 1:  # Venda do MacBook
                sale_item = SaleItem(
                    sale=sale,
                    product=products[2],  # MacBook Pro M2
                    quantity=1,
                    price=14999.00
                )
                products[2].remove_from_stock(1)
            elif i == 2:  # Venda do AirPods
                sale_item = SaleItem(
                    sale=sale,
                    product=products[4],  # AirPods Pro 2
                    quantity=1,
                    price=2499.00
                )
                products[4].remove_from_stock(1)
            elif i == 3:  # Venda da TV
                sale_item = SaleItem(
                    sale=sale,
                    product=products[6],  # Samsung Neo QLED
                    quantity=1,
                    price=9499.00
                )
                products[6].remove_from_stock(1)
            else:  # Venda do iPad
                sale_item = SaleItem(
                    sale=sale,
                    product=products[3],  # iPad Pro M2
                    quantity=1,
                    price=7499.00
                )
                products[3].remove_from_stock(1)

            db.session.add(sale_item)

        db.session.commit()
        print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    print("Iniciando programa principal...")
    resposta = input("Isso irá apagar todos os dados existentes. Deseja continuar? (s/N): ")
    if resposta.lower() == 's':
        init_db()
        app.run(debug=True)
    else:
        print("Operação cancelada pelo usuário.")