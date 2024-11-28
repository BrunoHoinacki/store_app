# Sistema de Gerenciamento de Loja

Este é um sistema completo de gerenciamento de loja desenvolvido com Flask, oferecendo funcionalidades para controle de vendas, estoque, clientes e finanças.

## 🚀 Funcionalidades

### Vendas
- Registro de vendas com múltiplos itens
- Diferentes formas de pagamento (Dinheiro, Cartão, PIX, etc.)
- Histórico detalhado de vendas
- Cancelamento de vendas
- Busca rápida de produtos

### Produtos
- Cadastro e gestão de produtos
- Controle de estoque
- Alertas de baixo estoque
- Categorização de produtos
- Preços de custo e venda

### Clientes
- Cadastro de clientes
- Histórico de compras por cliente
- Status ativo/inativo
- Busca rápida de clientes

### Financeiro
- Dashboard com indicadores financeiros
- Relatórios de vendas
- Análise de lucros
- Filtros por período
- Métricas de desempenho

### Dashboard Principal
- Visão geral do negócio
- Vendas do dia/semana
- Produtos mais vendidos
- Alertas importantes
- Indicadores em tempo real

## 💻 Tecnologias Utilizadas

- **Backend**: Python/Flask
- **Banco de Dados**: SQLite
- **Frontend**: Bootstrap 5
- **JavaScript**: jQuery, DataTables, Select2
- **Ícones**: Font Awesome, Bootstrap Icons

## 📦 Dependências

```txt
Flask==2.0.1
Flask-SQLAlchemy==2.5.1
Flask-Login==0.5.0
Flask-WTF==0.15.1
Werkzeug==2.0.1
SQLAlchemy==1.4.23
python-dotenv==0.19.0
```

## 🛠️ Instalação

1. Clone o repositório
```bash
git clone git@github.com:danielthejoker18/store_app.git
```

2. Crie um ambiente virtual
```bash
python -m venv venv
```

3. Ative o ambiente virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Instale as dependências
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

6. Rode as migrations
```bash
flask db migrate
```

7. Inicialize o banco de dados
```bash
flask db upgrade
```

8. Execute a aplicação
```bash
flask run
```

9. Crie um usuario
```bash
python create_user.py
```

## 🗄️ Estrutura do Projeto

```
store_app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes.py
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── products/
│       ├── sales/
│       ├── customers/
│       └── finance/
├── migrations/
├── instance/
├── venv/
├── config.py
├── requirements.txt
└── README.md
```

## 👥 Usuários e Autenticação

- Sistema de login seguro
- Proteção de rotas
- Gerenciamento de sessões

## 📊 Banco de Dados

### Tabelas Principais
- Users: Usuários do sistema
- Products: Cadastro de produtos
- Categories: Categorias de produtos
- Sales: Registro de vendas
- SaleItems: Itens de cada venda
- Customers: Cadastro de clientes

## 🔒 Segurança

- Senhas criptografadas
- Proteção contra CSRF
- Validação de formulários
- Sanitização de inputs
- Controle de acesso por rota

## 📱 Interface

- Design responsivo
- Tema moderno e clean
- Navegação intuitiva
- Feedback visual de ações
- Modais e formulários otimizados

## ⚙️ Configurações

As principais configurações podem ser ajustadas através do arquivo `.env`:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta
DATABASE_URL=sqlite:///store.db
```

## 🔄 Últimas Atualizações

### Correções e Melhorias (2024-01-09)
- Corrigido erro no processamento de vendas relacionado aos métodos de pagamento
- Melhorado o tratamento de erros na função de processamento de vendas
- Adicionado logging de erros para melhor diagnóstico de problemas
- Ajustado o layout do dashboard financeiro para melhor usabilidade
- Implementado tratamento mais preciso para cálculos monetários usando Decimal

### Métodos de Pagamento Suportados
- Dinheiro
- Cartão de Crédito (com suporte a parcelamento)
- Cartão de Débito
- PIX

### Próximas Atualizações Planejadas
- Implementação de relatórios exportáveis
- Melhorias na interface do usuário
- Integração com sistemas de pagamento
- Sistema de backup automático

## 🔄 Atualizações Futuras

- [ ] Relatórios em PDF
- [ ] Backup automático
- [ ] Integração com API de pagamentos
- [ ] App mobile
- [ ] Módulo de fornecedores

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuição

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Adicione as mudanças para staged (`git add .`)
3. Faça o Commit das suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Faça o Push da Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📧 Suporte

Para suporte e dúvidas, por favor abra uma issue no repositório ou entre em contato através do email danielmoreira18@hotmail.com.

## 🙏 Agradecimentos

- Bootstrap Team
- Flask Team
- Contribuidores
- Comunidade Open Source
