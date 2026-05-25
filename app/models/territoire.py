from app import db


class TypeLocalite(db.Model):
    __tablename__ = 'type_localite'

    id_type_localite = db.Column(db.Integer, primary_key=True)
    code_type        = db.Column(db.String(20), nullable=False, unique=True)
    libelle_type     = db.Column(db.String(100), nullable=False)

    localites = db.relationship('LocaliteAdministrative', back_populates='type_localite')


class LocaliteAdministrative(db.Model):
    __tablename__ = 'localite_administrative'

    id_localite      = db.Column(db.Integer, primary_key=True)
    nom_localite     = db.Column(db.String(150), nullable=False)
    code_localite    = db.Column(db.String(30), nullable=False, unique=True)
    id_type_localite = db.Column(db.Integer, db.ForeignKey('type_localite.id_type_localite'), nullable=False)
    id_parent        = db.Column(db.Integer, db.ForeignKey('localite_administrative.id_localite'))

    type_localite = db.relationship('TypeLocalite', back_populates='localites')
    parent        = db.relationship('LocaliteAdministrative', remote_side=[id_localite], back_populates='enfants')
    enfants       = db.relationship('LocaliteAdministrative', back_populates='parent')
    quartiers     = db.relationship('Quartier', back_populates='localite')
    zones         = db.relationship('ZoneDenombrement', back_populates='localite')


class Quartier(db.Model):
    __tablename__ = 'quartier'

    id_quartier   = db.Column(db.Integer, primary_key=True)
    nom_quartier  = db.Column(db.String(150), nullable=False)
    code_quartier = db.Column(db.String(30), nullable=False, unique=True)
    id_localite   = db.Column(db.Integer, db.ForeignKey('localite_administrative.id_localite'), nullable=False)
    observations  = db.Column(db.Text)

    localite = db.relationship('LocaliteAdministrative', back_populates='quartiers')
    zones    = db.relationship('ZoneDenombrement', back_populates='quartier')


class ZoneDenombrement(db.Model):
    __tablename__ = 'zone_denombrement'

    __table_args__ = (
        db.Index('idx_zd_localite', 'id_localite'),
        db.Index('idx_zd_quartier', 'id_quartier'),
    )

    id_zd       = db.Column(db.Integer, primary_key=True)
    code_zd     = db.Column(db.String(30), nullable=False, unique=True)
    id_localite = db.Column(db.Integer, db.ForeignKey('localite_administrative.id_localite'), nullable=False)
    id_quartier = db.Column(db.Integer, db.ForeignKey('quartier.id_quartier'))

    localite      = db.relationship('LocaliteAdministrative', back_populates='zones')
    quartier      = db.relationship('Quartier', back_populates='zones')
    ilots         = db.relationship('Ilot', back_populates='zone_denombrement')
    affectations  = db.relationship('AffectationZD', back_populates='zone_denombrement')


class Ilot(db.Model):
    __tablename__ = 'ilot'

    __table_args__ = (
        db.Index('idx_ilot_zd', 'id_zd'),
    )

    id_ilot      = db.Column(db.Integer, primary_key=True)
    numero_ilot  = db.Column(db.Integer, nullable=False)
    code_ilot    = db.Column(db.String(30), nullable=False, unique=True)
    id_zd        = db.Column(db.Integer, db.ForeignKey('zone_denombrement.id_zd'), nullable=False)

    zone_denombrement = db.relationship('ZoneDenombrement', back_populates='ilots')
    logements         = db.relationship('Logement', back_populates='ilot')
