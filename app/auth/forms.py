from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField 
from wtforms.validators import DataRequired, Length, Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User
from flask import flash
import re,os

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    email=StringField("Email",validators=[
        DataRequired(),
        Length(1,64),
        Email()
    ])
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            flash("Email already in use.")
            raise ValidationError()
        if not re.match(r"^.*@{}$".format(os.getenv("DOMAIN")),field.data):
            flash("Not Valid Email Address")
            raise ValidationError()

    username=StringField("Username",validators=[
        DataRequired(),
        Length(1,64)
    ])
    def validate_username(self,field):
        if not re.match('^[a-zA-Z][A-Za-z0-9_.]*$',field.data):
            flash("Username must have only letters, numbers dots or underscore")
            raise ValidationError()


    password=PasswordField("Password",validators=[
        DataRequired(),
        EqualTo("password2",
                message="Password not match!")
    ])
    password2=PasswordField("Confirm password", validators=[DataRequired()])
    submit=SubmitField("Register")

