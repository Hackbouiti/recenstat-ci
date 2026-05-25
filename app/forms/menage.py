from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField, DateField, TimeField, IntegerField
from wtforms.validators import DataRequired, Optional


class MenageForm(FlaskForm):
    id_zd            = SelectField('Zone de dénombrement', coerce=int, validators=[DataRequired()])
    id_ilot          = SelectField('Îlot', coerce=int, validators=[DataRequired()])
    id_type_logement = SelectField('Type de logement', coerce=int, validators=[DataRequired()])
    id_materiau_mur  = SelectField('Matériau des murs', coerce=int, validators=[DataRequired()])
    id_materiau_toit = SelectField('Matériau du toit', coerce=int, validators=[DataRequired()])
    id_source_eau    = SelectField("Source d'eau", coerce=int, validators=[DataRequired()])
    id_type_toilette = SelectField('Type de toilettes', coerce=int, validators=[DataRequired()])
    submit           = SubmitField('Créer le ménage')


class PassageForm(FlaskForm):
    id_statut_passage = SelectField('Statut du passage', coerce=int, validators=[DataRequired()])
    date_passage      = DateField('Date du passage', validators=[DataRequired()])
    heure_passage     = TimeField('Heure du passage', validators=[Optional()])
    observations      = TextAreaField('Observations', validators=[Optional()])
    submit            = SubmitField('Enregistrer le passage')


class AffectationForm(FlaskForm):
    id_utilisateur = SelectField('Enquêteur', coerce=int, validators=[DataRequired()])
    id_zd          = SelectField('Zone de dénombrement', coerce=int, validators=[DataRequired()])
    date_debut     = DateField('Date de début', validators=[DataRequired()])
    date_fin       = DateField('Date de fin', validators=[Optional()])
    submit         = SubmitField('Affecter')


class LocaliteForm(FlaskForm):
    nom_localite     = SelectField('Nom de la localité', validators=[DataRequired()])
    code_localite    = SelectField('Code', validators=[DataRequired()])
    id_type_localite = SelectField('Type', coerce=int, validators=[DataRequired()])
    id_parent        = SelectField('Localité parente', coerce=int, validators=[Optional()])
    submit           = SubmitField('Enregistrer')


class QuartierForm(FlaskForm):
    nom_quartier  = SelectField('Nom du quartier', validators=[DataRequired()])
    code_quartier = SelectField('Code', validators=[DataRequired()])
    id_localite   = SelectField('Commune / Localité', coerce=int, validators=[DataRequired()])
    observations  = TextAreaField('Observations', validators=[Optional()])
    submit        = SubmitField('Enregistrer')


class ZDForm(FlaskForm):
    code_zd     = SelectField('Code ZD', validators=[DataRequired()])
    id_localite = SelectField('Localité', coerce=int, validators=[DataRequired()])
    id_quartier = SelectField('Quartier', coerce=int, validators=[Optional()])
    submit      = SubmitField('Enregistrer')


class IlotForm(FlaskForm):
    numero_ilot = IntegerField('Numéro îlot', validators=[DataRequired()])
    code_ilot   = SelectField('Code îlot', validators=[DataRequired()])
    id_zd       = SelectField('Zone de dénombrement', coerce=int, validators=[DataRequired()])
    submit      = SubmitField('Enregistrer')
