import click
from datetime import date
from flask.cli import with_appcontext
from app import db
from app.models.habitat import StatutMenage, TypeLogement, MateriauMur, MateriauToit, SourceEau, TypeToilette
from app.models.collecte import StatutPassage, Utilisateur, AffectationZD
from app.models.territoire import TypeLocalite, LocaliteAdministrative, Quartier, ZoneDenombrement, Ilot
from app.models.individu import Profession


def register_seed_command(app):
    @app.cli.command('seed')
    @with_appcontext
    def seed():
        """Peuple la base de données avec les données de référence et de test."""
        click.echo('Démarrage du seed...')

        # --- Statuts ménage ---
        statuts_menage = [
            ('EN_COURS', 'En cours de saisie'),
            ('SOUMIS', 'Soumis'),
            ('RENVOYE', 'Renvoyé en correction'),
            ('VALIDE', 'Validé'),
        ]
        for code, libelle in statuts_menage:
            if not StatutMenage.query.filter_by(code_statut=code).first():
                db.session.add(StatutMenage(code_statut=code, libelle_statut=libelle))

        # --- Statuts passage ---
        statuts_passage = [
            ('COMPLET',   'Questionnaire complet'),
            ('ABSENT',    'Ménage absent'),
            ('REFUS',     'Refus de répondre'),
            ('PARTIEL',   'Questionnaire partiel'),
            ('RDV_FIXE',  'Rendez-vous fixé'),
        ]
        for code, libelle in statuts_passage:
            if not StatutPassage.query.filter_by(code_statut=code).first():
                db.session.add(StatutPassage(code_statut=code, libelle_statut=libelle))

        # --- Types logement ---
        types_logement = [
            ('VILLA',   'Villa'),
            ('APPART',  'Appartement'),
            ('MAISON',  'Maison basse'),
            ('CHAMBRE', 'Chambre en location'),
            ('CASE',    'Case / Concession'),
        ]
        for code, libelle in types_logement:
            if not TypeLogement.query.filter_by(code_type=code).first():
                db.session.add(TypeLogement(code_type=code, libelle_type=libelle))

        # --- Matériaux mur ---
        mat_murs = [
            ('BETON',  'Béton / Parpaing'),
            ('BOIS',   'Bois'),
            ('BANCO',  'Banco / Terre'),
            ('TOLE',   'Tôle'),
            ('PAILLE', 'Paille / Tige'),
        ]
        for code, libelle in mat_murs:
            if not MateriauMur.query.filter_by(code_materiau=code).first():
                db.session.add(MateriauMur(code_materiau=code, libelle_materiau=libelle))

        # --- Matériaux toit ---
        mat_toits = [
            ('TOLE',   'Tôle'),
            ('TUILE',  'Tuile'),
            ('BETON',  'Béton'),
            ('PAILLE', 'Paille / Chaume'),
        ]
        for code, libelle in mat_toits:
            if not MateriauToit.query.filter_by(code_materiau=code).first():
                db.session.add(MateriauToit(code_materiau=code, libelle_materiau=libelle))

        # --- Sources eau ---
        sources_eau = [
            ('ROBINET_INT',    'Robinet intérieur'),
            ('BORNE_FONTAINE', 'Borne-fontaine'),
            ('PUITS',          'Puits'),
            ('COURS_EAU',      "Cours d'eau"),
            ('ACHETEE',        'Eau achetée'),
        ]
        for code, libelle in sources_eau:
            if not SourceEau.query.filter_by(code_source=code).first():
                db.session.add(SourceEau(code_source=code, libelle_source=libelle))

        # --- Types toilette ---
        types_toilette = [
            ('WC_INT',           'WC intérieur'),
            ('LATRINE_COUV',     'Latrine couverte'),
            ('LATRINE_NON_COUV', 'Latrine non couverte'),
            ('NATURE',           'Nature'),
        ]
        for code, libelle in types_toilette:
            if not TypeToilette.query.filter_by(code_type=code).first():
                db.session.add(TypeToilette(code_type=code, libelle_type=libelle))

        # --- Types localité ---
        types_localite = [
            ('DISTRICT',    'District'),
            ('REGION',      'Région'),
            ('DEPARTEMENT', 'Département'),
            ('COMMUNE',     'Commune'),
            ('SOUS_PREF',   'Sous-préfecture'),
        ]
        for code, libelle in types_localite:
            if not TypeLocalite.query.filter_by(code_type=code).first():
                db.session.add(TypeLocalite(code_type=code, libelle_type=libelle))

        # --- Professions ---
        professions = [
            ('AGRI',    'Agriculture / Élevage'),
            ('COMM',    'Commerce'),
            ('ENSEIGNANT', 'Enseignement'),
            ('SANTE',   'Santé / Médecine'),
            ('ARTISAN',  'Artisanat'),
            ('TRANSPORT','Transport'),
            ('ADMIN',   'Administration publique'),
            ('BTP',     'Bâtiment / Travaux publics'),
            ('INFORM',  'Informatique / Télécommunications'),
            ('AUTRE',   'Autre profession'),
        ]
        for code, libelle in professions:
            if not Profession.query.filter_by(code_profession=code).first():
                db.session.add(Profession(code_profession=code, libelle_profession=libelle))

        db.session.commit()
        click.echo('Tables de référence peuplées.')

        # --- Structure territoriale de test ---
        type_commune = TypeLocalite.query.filter_by(code_type='COMMUNE').first()

        localite = LocaliteAdministrative.query.filter_by(code_localite='ABJ-ABO').first()
        if not localite:
            localite = LocaliteAdministrative(
                nom_localite="Commune d'Abobo",
                code_localite='ABJ-ABO',
                id_type_localite=type_commune.id_type_localite,
            )
            db.session.add(localite)
            db.session.flush()

        quartier = Quartier.query.filter_by(code_quartier='ABO-BAO').first()
        if not quartier:
            quartier = Quartier(
                nom_quartier='Abobo-Baoulé',
                code_quartier='ABO-BAO',
                id_localite=localite.id_localite,
            )
            db.session.add(quartier)
            db.session.flush()

        zd = ZoneDenombrement.query.filter_by(code_zd='ZD-138').first()
        if not zd:
            zd = ZoneDenombrement(
                code_zd='ZD-138',
                id_localite=localite.id_localite,
                id_quartier=quartier.id_quartier,
            )
            db.session.add(zd)
            db.session.flush()

        ilot = Ilot.query.filter_by(code_ilot='ZD138-IL01').first()
        if not ilot:
            ilot = Ilot(
                numero_ilot=1,
                code_ilot='ZD138-IL01',
                id_zd=zd.id_zd,
            )
            db.session.add(ilot)
            db.session.flush()

        db.session.commit()
        click.echo('Structure territoriale créée.')

        # --- Comptes utilisateurs ---
        users_data = [
            ('Admin', 'Système', 'admin@recenstat.ci', 'admin1234', 'ADMINISTRATEUR'),
            ('Superviseur', 'Test', 'superviseur@recenstat.ci', 'superviseur1234', 'SUPERVISEUR'),
            ('Enquêteur', 'Test', 'enqueteur@recenstat.ci', 'enqueteur1234', 'ENQUETEUR'),
        ]
        for nom, prenom, email, pwd, role in users_data:
            if not Utilisateur.query.filter_by(email=email).first():
                u = Utilisateur(nom=nom, prenom=prenom, email=email, role=role, actif=True)
                u.set_password(pwd)
                db.session.add(u)

        db.session.commit()
        click.echo('Comptes utilisateurs créés.')

        # --- Affectation enquêteur → ZD-138 ---
        enqueteur = Utilisateur.query.filter_by(email='enqueteur@recenstat.ci').first()
        if enqueteur and not AffectationZD.query.filter_by(
            id_utilisateur=enqueteur.id_utilisateur,
            id_zd=zd.id_zd
        ).first():
            aff = AffectationZD(
                id_utilisateur=enqueteur.id_utilisateur,
                id_zd=zd.id_zd,
                date_debut=date.today(),
                actif=True,
            )
            db.session.add(aff)
            db.session.commit()
            click.echo('Affectation enquêteur créée.')

        click.echo('Seed terminé avec succès !')
        click.echo('\nComptes disponibles :')
        click.echo('  admin@recenstat.ci / admin1234')
        click.echo('  superviseur@recenstat.ci / superviseur1234')
        click.echo('  enqueteur@recenstat.ci / enqueteur1234')
