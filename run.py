"""
Arquivo principal para execução do Store App.
Este módulo configura e inicia a aplicação Flask com todas as configurações necessárias.
"""

import os
from app import create_app
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Cria a aplicação usando as configurações do ambiente
app = create_app()

if __name__ == '__main__':
    # Configurações do servidor de desenvolvimento
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    # Inicia o servidor
    app.run(host=host, port=port, debug=debug)