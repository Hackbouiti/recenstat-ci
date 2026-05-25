from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from app.choices import (
    SEXE, LIEN_CHEF_MENAGE, SITUATION_MATRIMONIALE,
    NIVEAU_INSTRUCTION, STATUT_SCOLARISATION, STATUT_ACTIVITE
)


class IndividuForm(FlaskForm):
    nom                    = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom                 = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    date_naissance         = DateField('Date de naissance', validators=[DataRequired()])
    sexe                   = SelectField('Sexe', choices=SEXE, validators=[DataRequired()])
    lien_chef_menage       = SelectField('Lien avec le chef de ménage', choices=LIEN_CHEF_MENAGE, validators=[DataRequired()])
    situation_matrimoniale = SelectField('Situation matrimoniale', choices=SITUATION_MATRIMONIALE, validators=[DataRequired()])
    niveau_instruction     = SelectField('Niveau d\'instruction', choices=NIVEAU_INSTRUCTION, validators=[DataRequired()])
    statut_scolarisation   = SelectField('Statut de scolarisation', choices=[('', '--- Sélectionner ---')] + STATUT_SCOLARISATION, validators=[Optional()])
    statut_activite        = SelectField('Statut d\'activité', choices=STATUT_ACTIVITE, validators=[DataRequired()])
    sait_lire_ecrire       = BooleanField('Sait lire et écrire', validators=[Optional()])
    id_profession          = SelectField('Profession', coerce=int, validators=[Optional()])
    submit                 = SubmitField('Enregistrer')
