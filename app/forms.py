from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField, TextAreaField, BooleanField, FieldList, FormField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Optional, Email
from app.models import Product, Customer

class ProductQuantityForm(FlaskForm):
    product_id = SelectField('Produto', coerce=int, choices=[], validate_choice=False)
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class ProductForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)], render_kw={'placeholder': 'Exemplo: Cadeira de escritório'})
    description = TextAreaField('Descrição', render_kw={'placeholder': 'Exemplo: Cadeira ergonômica, ajuste de altura e apoio para os braços.'})
    cost_price = DecimalField('Preço de Custo', validators=[DataRequired(), NumberRange(min=0)], render_kw={'placeholder': 'Exemplo: 150.00'})
    sale_price = DecimalField('Preço de Venda', validators=[DataRequired(), NumberRange(min=0)], render_kw={'placeholder': 'Exemplo: 250.00'})
    stock = IntegerField('Estoque', validators=[DataRequired(), NumberRange(min=0)], render_kw={'placeholder': 'Exemplo: 50'})
    category_id = SelectField('Categoria', coerce=int, validators=[DataRequired()], render_kw={'placeholder': 'Selecione uma categoria'})
    submit = SubmitField('Salvar')

class CustomerForm(FlaskForm):
    id = StringField('ID', validators=[Optional()])
    name = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Telefone', validators=[Optional()])
    address = StringField('Endereço', validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])

    def validate_email(self, field):
        if field.data:
            customer = Customer.query.filter_by(email=field.data).first()
            if customer and (not self.id.data or str(customer.id) != self.id.data):
                raise ValidationError('Este email já está cadastrado.')

class SaleForm(FlaskForm):
    customer_id = SelectField('Cliente', coerce=int, validators=[Optional()])
    payment_method = SelectField('Forma de Pagamento', 
        choices=[('money', 'Dinheiro'), ('credit_card', 'Cartão de Crédito'), ('debit_card', 'Cartão de Débito'), ('pix', 'PIX')],
        validators=[DataRequired()]
    )
    installments = IntegerField('Parcelas', validators=[Optional()], default=1)
    has_interest = BooleanField('Aplicar Juros')
    interest_rate = DecimalField('Taxa de Juros (%)', validators=[Optional()], default=0)
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Finalizar Venda')

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.customer_id.choices = [(0, 'Selecione um cliente (opcional)')] + [
            (c.id, c.name) for c in Customer.query.order_by(Customer.name).all()
        ]

    def validate_installments(self, field):
        if self.payment_method.data != 'credit_card' and field.data > 1:
            raise ValidationError('Apenas vendas no cartão de crédito podem ser parceladas')

    def validate_interest_rate(self, field):
        if self.has_interest.data and field.data <= 0:
            raise ValidationError('A taxa de juros deve ser maior que zero quando juros estão habilitados')

class CategoryForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Salvar') 