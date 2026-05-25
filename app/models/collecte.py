import bcrypt
from flask_login import UserMixin
from app import db


class StatutPassage(db.Model):
    __tablename__ = 'statut_passage'

    id_statut_passage = db.Column(db.Integer, primary_key=True)
    code_statut       = db.Column(db.String(30), nullable=False, unique=True)
    libelle_statut    = db.Column(db.String(100), nullable=False)

    passages = db.relationship('PassageCollecte', back_populates='statut_passage')


class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateur'

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('ADMINISTRATEUR','SUPERVISEUR','ENQUETEUR')",
            name='ck_utilisateur_role'
        ),
    )

    id_utilisateur    = db.Column(db.Integer, primary_key=True)
    nom               = db.Column(db.String(100), nullable=False)
    prenom            = db.Column(db.String(100), nullable=False)
    email             = db.Column(db.String(150), nullable=False, unique=True)
    telephone         = db.Column(db.String(20))
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    actif             = db.Column(db.Boolean, nullable=False, default=True)
    role              = db.Column(db.String(20), nullable=False)

    affectations = db.relationship('AffectationZD', back_populates='utilisateur')
    passages     = db.relationship('PassageCollecte', back_populates='utilisateur')

    def get_id(self):
        return str(self.id_utilisateur)

    def set_password(self, password):
        self.mot_de_passe_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.mot_de_passe_hash.encode('utf-8')
        )

    @property
    def is_active(self):
        return self.actif


class AffectationZD(db.Model):
    __tablename__ = 'affectation_zd'

    __table_args__ = (
        db.Index('idx_affectation_zd', 'id_zd'),
        db.Index('idx_affectation_user', 'id_utilisateur'),
    )

    id_affectation = db.Column(db.Integer, primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur'), nullable=False)
    id_zd          = db.Column(db.Integer, db.ForeignKey('zone_denombrement.id_zd'), nullable=False)
    date_debut     = db.Column(db.Date, nullable=False)
    date_fin       = db.Column(db.Date)
    actif          = db.Column(db.Boolean, nullable=False, default=True)

    utilisateur       = db.relationship('Utilisateur', back_populates='affectations')
    zone_denombrement = db.relationship('ZoneDenombrement', back_populates='affectations')


class PassageCollecte(db.Model):
    __tablename__ = 'passage_collecte'

    __table_args__ = (
        db.Index('idx_passage_menage', 'id_menage'),
    )

    id_passage        = db.Column(db.Integer, primary_key=True)
    id_menage         = db.Column(db.Integer, db.ForeignKey('menage.id_menage'), nullable=False)
    id_utilisateur    = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur'), nullable=False)
    numero_passage    = db.Column(db.Integer, nullable=False, default=1)
    date_passage      = db.Column(db.Date, nullable=False)
    heure_passage     = db.Column(db.Time)
    id_statut_passage = db.Column(db.Integer, db.ForeignKey('statut_passage.id_statut_passage'), nullable=False)
    observations      = db.Column(db.Text)

    menage         = db.relationship('Menage', back_populates='passages')
    utilisateur    = db.relationship('Utilisateur', back_populates='passages')
    statut_passage = db.relationship('StatutPassage', back_populates='passages')
