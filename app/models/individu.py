from datetime import date
from app import db


class Profession(db.Model):
    __tablename__ = 'profession'

    id_profession      = db.Column(db.Integer, primary_key=True)
    code_profession    = db.Column(db.String(30), nullable=False, unique=True)
    libelle_profession = db.Column(db.String(150), nullable=False)

    individus = db.relationship('Individu', back_populates='profession')


class Individu(db.Model):
    __tablename__ = 'individu'

    __table_args__ = (
        db.Index('idx_individu_menage', 'id_menage'),
        db.Index('idx_individu_activite', 'statut_activite'),
        db.CheckConstraint("sexe IN ('M','F')", name='ck_individu_sexe'),
        db.CheckConstraint(
            "lien_chef_menage IN ('CHEF','CONJOINT','ENFANT','PERE_MERE','FRERE_SOEUR','AUTRE_PARENT','SANS_LIEN')",
            name='ck_individu_lien'
        ),
        db.CheckConstraint(
            "situation_matrimoniale IN ('CELIBATAIRE','MARIE_MONO','MARIE_POLY','DIVORCE','VEUF','UNION_LIBRE')",
            name='ck_individu_matrimoniale'
        ),
        db.CheckConstraint(
            "niveau_instruction IN ('AUCUN','PRIMAIRE','SECONDAIRE_1','SECONDAIRE_2','SUPERIEUR')",
            name='ck_individu_instruction'
        ),
        db.CheckConstraint(
            "statut_scolarisation IN ('SCOLARISE','NON_SCOLARISE','JAMAIS_SCOLARISE','ABANDONNE')",
            name='ck_individu_scolarisation'
        ),
        db.CheckConstraint(
            "statut_activite IN ('ACTIF_OCCUPE','CHOMEUR','ELEVE_ETUDIANT','RETRAITE','MENAGERE','AUTRE_INACTIF')",
            name='ck_individu_activite'
        ),
    )

    id_individu            = db.Column(db.Integer, primary_key=True)
    id_menage              = db.Column(db.Integer, db.ForeignKey('menage.id_menage'), nullable=False)
    nom                    = db.Column(db.String(100), nullable=False)
    prenom                 = db.Column(db.String(100), nullable=False)
    date_naissance         = db.Column(db.Date, nullable=False)
    sexe                   = db.Column(db.String(1), nullable=False)
    lien_chef_menage       = db.Column(db.String(20), nullable=False)
    est_chef_menage        = db.Column(db.Boolean, nullable=False, default=False)
    situation_matrimoniale = db.Column(db.String(20), nullable=False)
    niveau_instruction     = db.Column(db.String(20), nullable=False)
    statut_scolarisation   = db.Column(db.String(20))
    statut_activite        = db.Column(db.String(20), nullable=False)
    sait_lire_ecrire       = db.Column(db.Boolean)
    id_profession          = db.Column(db.Integer, db.ForeignKey('profession.id_profession'))

    menage    = db.relationship('Menage', back_populates='individus')
    profession = db.relationship('Profession', back_populates='individus')

    @property
    def age(self):
        today = date.today()
        age = today.year - self.date_naissance.year
        if (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day):
            age -= 1
        return age
