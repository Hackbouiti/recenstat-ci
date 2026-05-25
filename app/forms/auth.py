from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, TelField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.choices import ROLE


class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit   = SubmitField('Se connecter')


class UserForm(FlaskForm):
    nom       = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom    = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    email     = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    telephone = TelField('Téléphone', validators=[Optional(), Length(max=20)])
    role      = SelectField('Rôle', choices=ROLE, validators=[DataRequired()])
    password  = PasswordField('Mot de passe', validators=[Optional(), Length(min=6)])
    actif     = BooleanField('Compte actif', default=True)
    submit    = SubmitField('Enregistrer')
