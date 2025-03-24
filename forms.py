
from flask_wtf import FlaskForm
from wtforms import SubmitField,StringField,IntegerField,PasswordField,FloatField,FileField,SelectField,HiddenField
from wtforms.validators import DataRequired,Email



class Login_form(FlaskForm):
    email = StringField("Email",validators=[DataRequired(),Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("submit")


class Signup_form(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    address = StringField("Adress", validators=[DataRequired()])
    number = IntegerField("Phone Number",validators=[DataRequired()])
    email = StringField("Email",  validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("submit")

class Edit_profile_form(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    address = StringField("Adress", validators=[DataRequired()])
    number = IntegerField("Phone Number",validators=[DataRequired()])
    email = StringField("Email",  validators=[DataRequired(), Email()])
    submit = SubmitField("submit")


class Config_product(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    category = StringField("Category",validators=[DataRequired()])
    decription = StringField("Description",validators=[DataRequired()])
    price = FloatField("Price",validators=[DataRequired()])
    image_url = StringField("Image URl")
    upload = FileField("Or Upload Img")
    quantity = IntegerField("Quantity",validators=[DataRequired()])
    submit = SubmitField("Submit")


class Select_status(FlaskForm):
    select = SelectField(choices=["Pending","paid","delivered","canceled"],validators=[DataRequired()])
    submit = SubmitField("Submit")
