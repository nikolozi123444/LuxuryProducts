from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo
from models import Category
from wtforms import SubmitField

class MessageForm(FlaskForm):
    message = TextAreaField('შეტყობინება', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('გაგზავნა')


class LoginForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('პაროლი', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('მომხმარებლის სახელი', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('გაიმეორეთ პაროლი',
                                     validators=[DataRequired(), EqualTo('password', message='პაროლები არ ემთხვევა')])


class ProductForm(FlaskForm):
    name = StringField('პროდუქტის სახელი', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('აღწერა')
    price = FloatField('ფასი', validators=[DataRequired(), NumberRange(min=0.01)])
    image_url = StringField('სურათის URL')
    category_id = SelectField('კატეგორია', coerce=int, validators=[DataRequired()])
    in_stock = BooleanField('მარაგშია')
    featured = BooleanField('რჩეული პროდუქტი')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]


class ContactForm(FlaskForm):
    name = StringField('სახელი', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    message = TextAreaField('შეტყობინება', validators=[DataRequired(), Length(min=10, max=1000)])


class CategoryForm(FlaskForm):
    name = StringField('კატეგორიის სახელი', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('აღწერა')

class ResetPasswordForm(FlaskForm):
    email = StringField('ელფოსტა', validators=[DataRequired(), Email()])
    new_password = PasswordField('ახალი პაროლი', validators=[DataRequired(), Length(min=5)])
    confirm_password = PasswordField('გაიმეორე პაროლი', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('პაროლის შეცვლა')


class AddToCartForm(FlaskForm):
    submit = SubmitField('კალათაში დამატება')

class WishlistForm(FlaskForm):
    submit = SubmitField("სურვილების სიაში დამატება")

class CheckoutForm(FlaskForm):
    full_name = StringField("სრული სახელი", validators=[DataRequired(), Length(max=120)])
    address = StringField("მისამართი", validators=[DataRequired(), Length(max=200)])
    phone = StringField("ტელეფონი", validators=[DataRequired(), Length(max=50)])
    submit = SubmitField("შეკვეთის დადასტურება")