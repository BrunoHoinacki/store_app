import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    # Diretório base do projeto
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Configurações do Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Configurações do Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'store.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de Paginação
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '10'))
    
    # Configurações do Sistema
    LOW_STOCK_THRESHOLD = int(os.getenv('LOW_STOCK_THRESHOLD', '10'))
    APP_NAME = os.getenv('APP_NAME', 'Store App')
    
    # Configurações de Email (opcional)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')