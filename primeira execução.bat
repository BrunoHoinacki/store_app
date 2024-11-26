@echo off
echo Instalando dependências do requirements.txt...
pip install -r requirements.txt

python create_user.py

python run.py

echo Concluído.
exit