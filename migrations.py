from app import create_app, db
from flask_migrate import upgrade

app = create_app()
app.app_context().push()

# Criar todas as tabelas
db.create_all()

print("Banco de dados inicializado com sucesso!")
