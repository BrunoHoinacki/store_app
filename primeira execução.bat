@echo off
echo Instalando depend�ncias do requirements.txt...
pip install -r requirements.txt

python create_user.py

python run.py

echo Conclu�do.
exit