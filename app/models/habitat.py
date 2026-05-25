from datetime import datetime
from app import db


class TypeLogement(db.Model):
    __tablename__ = 'type_logement'

    id_type_logement = db.Column(db.Integer, primary_key=True)
    code_type        = db.Column(db.String(20), nullable=False, unique=True)
    libelle_type     = db.Column(db.String(100), nullable=False)

    logements = db.relationship('Logement', back_populates='type_logement')


class MateriauMur(db.Model):
    __tablename__ = 'materiau_mur'

    id_materiau_mur  = db.Column(db.Integer, primary_key=True)
    code_materiau    = db.Column(db.String(20), nullable=False, unique=True)
    libelle_materiau = db.Column(db.String(100), nullable=False)

    logements = db.relationship('Logement', back_populates='materiau_mur')


class MateriauToit(db.Model):
    __tablename__ = 'materiau_toit'

    id_materiau_toit = db.Column(db.Integer, primary_key=True)
    code_materiau    = db.Column(db.String(20), nullable=False, unique=True)
    libelle_materiau = db.Column(db.String(100), nullable=False)

    logements = db.relationship('Logement', back_populates='materiau_toit')


class SourceEau(db.Model):
    __tablename__ = 'source_eau'

    id_source_eau  = db.Column(db.Integer, primary_key=True)
    code_source    = db.Column(db.String(20), nullable=False, unique=True)
    libelle_source = db.Column(db.String(100), nullable=False)

    logements = db.relationship('Logement', back_populates='source_eau')


class TypeToilette(db.Model):
    __tablename__ = 'type_toilette'

    id_type_toilette = db.Column(db.Integer, primary_key=True)
    code_type        = db.Column(db.String(20), nullable=False, unique=True)
    libelle_type     = db.Column(db.String(100), nullable=False)

    logements = db.relationship('Logement', back_populates='type_toilette')


class StatutMenage(db.Model):
    __tablename__ = 'statut_menage'

    id_statut_menage = db.Column(db.Integer, primary_key=True)
    code_statut      = db.Column(db.String(30), nullable=False, unique=True)
    libelle_statut   = db.Column(db.String(100), nullable=False)

    menages = db.relationship('Menage', back_populates='statut_menage')


class Logement(db.Model):
    __tablename__ = 'logement'

    __table_args__ = (
        db.Index('idx_logement_ilot', 'id_ilot'),
    )

    id_logement      = db.Column(db.Integer, primary_key=True)
    numero_logement  = db.Column(db.Integer, nullable=False)
    code_logement    = db.Column(db.String(50), nullable=False, unique=True)
    id_ilot          = db.Column(db.Integer, db.ForeignKey('ilot.id_ilot'), nullable=False)
    id_type_logement = db.Column(db.Integer, db.ForeignKey('type_logement.id_type_logement'), nullable=False)
    id_materiau_mur  = db.Column(db.Integer, db.ForeignKey('materiau_mur.id_materiau_mur'), nullable=False)
    id_materiau_toit = db.Column(db.Integer, db.ForeignKey('materiau_toit.id_materiau_toit'), nullable=False)
    id_source_eau    = db.Column(db.Integer, db.ForeignKey('source_eau.id_source_eau'), nullable=False)
    id_type_toilette = db.Column(db.Integer, db.ForeignKey('type_toilette.id_type_toilette'), nullable=False)

    ilot          = db.relationship('Ilot', back_populates='logements')
    type_logement = db.relationship('TypeLogement', back_populates='logements')
    materiau_mur  = db.relationship('MateriauMur', back_populates='logements')
    materiau_toit = db.relationship('MateriauToit', back_populates='logements')
    source_eau    = db.relationship('SourceEau', back_populates='logements')
    type_toilette = db.relationship('TypeToilette', back_populates='logements')
    menages       = db.relationship('Menage', back_populates='logement')


class Menage(db.Model):
    __tablename__ = 'menage'

    __table_args__ = (
        db.Index('idx_menage_logement', 'id_logement'),
        db.Index('idx_menage_statut', 'id_statut_menage'),
    )

    id_menage        = db.Column(db.Integer, primary_key=True)
    numero_menage    = db.Column(db.Integer, nullable=False)
    code_menage      = db.Column(db.String(60), nullable=False, unique=True)
    id_logement      = db.Column(db.Integer, db.ForeignKey('logement.id_logement'), nullable=False)
    id_statut_menage = db.Column(db.Integer, db.ForeignKey('statut_menage.id_statut_menage'), nullable=False)
    date_creation    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    logement      = db.relationship('Logement', back_populates='menages')
    statut_menage = db.relationship('StatutMenage', back_populates='menages')
    individus     = db.relationship('Individu', back_populates='menage', cascade='all, delete-orphan')
    passages      = db.relationship('PassageCollecte', back_populates='menage')
