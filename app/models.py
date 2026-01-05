"""
Models do Sistema de Gerenciamento de Loja

Este módulo contém todos os modelos de dados utilizados no sistema, implementados
usando SQLAlchemy. Os modelos representam as principais entidades do negócio:
usuários, produtos, vendas, clientes e categorias.

Cada modelo inclui validações e métodos úteis para manipulação dos dados,
garantindo a integridade e facilitando operações comuns do negócio.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Numeric
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    """Carrega um usuário pelo ID para o Flask-Login."""
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """
    Modelo de Usuário do sistema.
    
    Attributes:
        id (int): Identificador único do usuário
        username (str): Nome de usuário, único no sistema
        password_hash (str): Hash da senha do usuário
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        """Define a senha do usuário, convertendo-a em hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    """
    Modelo de Categoria de produtos.
    
    Attributes:
        id (int): Identificador único da categoria
        name (str): Nome da categoria
        products (relationship): Relacionamento com produtos desta categoria
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    """
    Modelo de Produto.
    
    Attributes:
        id (int): Identificador único do produto
        name (str): Nome do produto
        description (str): Descrição detalhada do produto
        cost_price (float): Preço de custo
        sale_price (float): Preço de venda
        stock (int): Quantidade em estoque
        category_id (int): ID da categoria do produto
        created_at (datetime): Data de criação do registro
        
    Methods:
        profit(): Calcula o lucro por unidade
        profit_margin(): Calcula a margem de lucro em porcentagem
        adjust_stock(quantity_change): Ajusta o estoque de forma segura
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def profit(self):
        """Calcula o lucro por unidade"""
        return self.sale_price - self.cost_price

    @property
    def profit_margin(self):
        """Calcula a margem de lucro em porcentagem"""
        if self.cost_price > 0:
            return (self.profit / self.cost_price) * 100
        return 0

    def adjust_stock(self, quantity_change):
        """Ajusta o estoque de forma segura"""
        new_stock = self.stock + quantity_change
        if new_stock < 0:
            raise ValueError(f"Estoque insuficiente para o produto {self.name}")
        self.stock = new_stock
        return self.stock

    def remove_from_stock(self, quantity):
        """Remove quantidade do estoque"""
        return self.adjust_stock(-quantity)

    def add_to_stock(self, quantity):
        """Adiciona quantidade ao estoque"""
        return self.adjust_stock(quantity)

class Sale(db.Model):
    """
    Modelo de Venda.
    
    Attributes:
        id (int): Identificador único da venda
        date (datetime): Data e hora da venda
        customer_id (int): ID do cliente (opcional)
        user_id (int): ID do usuário que registrou a venda
        payment_method (str): Método de pagamento
        installments (int): Número de parcelas
        has_interest (bool): Indica se há juros
        interest_rate (float): Taxa de juros
        subtotal (float): Valor sem juros
        total_amount (float): Valor total com juros
        notes (str): Observações
        status (str): Status da venda (active/cancelled)
        cancelled_at (datetime): Data de cancelamento
        cancellation_reason (str): Motivo do cancelamento
        
    Methods:
        payment_method_display(): Retorna o método de pagamento formatado
        cancel(reason): Cancela a venda e retorna produtos ao estoque
        profit(): Calcula o lucro total da venda
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer = db.relationship('Customer', backref=db.backref('sales', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('sales', lazy=True))
    payment_method = db.Column(db.String(50), nullable=False)
    installments = db.Column(db.Integer, default=1)
    has_interest = db.Column(db.Boolean, default=False)
    interest_rate = db.Column(db.Numeric(5, 2), default=0)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text)
    items = db.relationship('SaleItem', backref='sale', lazy=True)

    @property
    def payment_method_display(self):
        """Retorna o método de pagamento formatado para exibição"""
        methods = {
            'credit_card': 'Cartão de Crédito',
            'debit_card': 'Cartão de Débito',
            'money': 'Dinheiro',
            'pix': 'PIX',
            'bank_transfer': 'Transferência Bancária'
        }
        return methods.get(self.payment_method, self.payment_method)

    @property
    def is_cancelled(self):
        return self.status == 'cancelled'

    def cancel(self, reason):
        """Cancela a venda e retorna os produtos ao estoque"""
        if not self.is_cancelled:
            print(f"Cancelando venda {self.id}")
            try:
                # Retorna os produtos ao estoque
                for item in self.items:
                    print(f"Produto {item.product.name}: estoque atual = {item.product.stock}")
                    print(f"Devolvendo {item.quantity} unidades")
                    item.product.add_to_stock(item.quantity)
                    print(f"Novo estoque = {item.product.stock}")
                
                self.status = 'cancelled'
                self.cancelled_at = datetime.now()
                self.cancellation_reason = reason
                print(f"Venda {self.id} cancelada com sucesso")
            except Exception as e:
                print(f"Erro ao cancelar venda: {str(e)}")
                raise

    @property
    def interest_amount(self):
        """Calcula o valor dos juros"""
        return self.total_amount - self.subtotal

    @property
    def profit(self):
        """Calcula o lucro total da venda"""
        cost = sum([item.quantity * item.product.cost_price for item in self.items])
        return self.total_amount - cost

class SaleItem(db.Model):
    """
    Modelo de Item de Venda.
    
    Attributes:
        id (int): Identificador único do item
        sale_id (int): ID da venda
        product_id (int): ID do produto
        quantity (int): Quantidade vendida
        price (float): Preço unitário no momento da venda
        
    Methods:
        subtotal(): Calcula o subtotal do item
    """
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    product = db.relationship('Product')

    @property
    def subtotal(self):
        """Calcula o subtotal do item"""
        return self.quantity * self.price

class TempSaleItem(db.Model):
    """
    Modelo de Item Temporário de Venda.
    
    Usado para armazenar itens durante o processo de venda,
    antes da finalização.
    
    Attributes:
        id (int): Identificador único do item temporário
        session_id (str): ID da sessão do usuário
        product_id (int): ID do produto
        quantity (int): Quantidade
        price (float): Preço unitário
        created_at (datetime): Data de criação do item temporário
    """
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')

    @property
    def subtotal(self):
        return self.quantity * self.price

class Customer(db.Model):
    """
    Modelo de Cliente.
    
    Attributes:
        id (int): Identificador único do cliente
        name (str): Nome do cliente
        email (str): Email do cliente (opcional)
        phone (str): Telefone do cliente (opcional)
        address (str): Endereço do cliente (opcional)
        notes (str): Observações sobre o cliente
        active (bool): Status do cliente
        inactivated_at (datetime): Data de inativação
        inactivation_reason (str): Motivo da inativação
        created_at (datetime): Data de criação do registro
        updated_at (datetime): Data da última atualização
        
    Methods:
        inactivate(reason): Inativa o cliente
        reactivate(): Reativa o cliente
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    inactivated_at = db.Column(db.DateTime, nullable=True)
    inactivation_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Customer {self.name}>'

    def inactivate(self, reason):
        """Inativa o cliente"""
        self.active = False
        self.inactivated_at = datetime.utcnow()
        self.inactivation_reason = reason

    def reactivate(self):
        """Reativa o cliente"""
        self.active = True
        self.inactivated_at = None
        self.inactivation_reason = None