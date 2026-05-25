import click
from datetime import date, time
from flask.cli import with_appcontext
from app import db
from app.models.habitat import (StatutMenage, TypeLogement, MateriauMur, MateriauToit,
                                  SourceEau, TypeToilette, Logement, Menage)
from app.models.collecte import StatutPassage, Utilisateur, AffectationZD, PassageCollecte
from app.models.territoire import TypeLocalite, LocaliteAdministrative, Quartier, ZoneDenombrement, Ilot
from app.models.individu import Profession, Individu


# ─── helpers ────────────────────────────────────────────────────────────────

def get_or_create(model, filter_kwargs, **create_kwargs):
    obj = model.query.filter_by(**filter_kwargs).first()
    if not obj:
        obj = model(**filter_kwargs, **create_kwargs)
        db.session.add(obj)
        db.session.flush()
    return obj


def make_code_logement(code_ilot, n):
    return f"{code_ilot}-LOG{n:03d}"


def make_code_menage(code_zd, code_ilot, n):
    return f"{code_zd}-{code_ilot}-MEN{n:03d}"


# ─── seed command ────────────────────────────────────────────────────────────

def register_seed_command(app):
    @app.cli.command('seed')
    @with_appcontext
    def seed():
        """Peuple la base de données avec les données de référence et de test."""
        click.echo('Démarrage du seed...')

        # ══════════════════════════════════════════════════════════════════
        # 1. TABLES DE RÉFÉRENCE
        # ══════════════════════════════════════════════════════════════════

        for code, lib in [('EN_COURS', 'En cours de saisie'), ('SOUMIS', 'Soumis'),
                           ('RENVOYE', 'Renvoyé en correction'), ('VALIDE', 'Validé')]:
            get_or_create(StatutMenage, {'code_statut': code}, libelle_statut=lib)

        for code, lib in [('COMPLET', 'Questionnaire complet'), ('ABSENT', 'Ménage absent'),
                           ('REFUS', 'Refus de répondre'), ('PARTIEL', 'Questionnaire partiel'),
                           ('RDV_FIXE', 'Rendez-vous fixé')]:
            get_or_create(StatutPassage, {'code_statut': code}, libelle_statut=lib)

        for code, lib in [('VILLA', 'Villa'), ('APPART', 'Appartement'),
                           ('MAISON', 'Maison basse'), ('CHAMBRE', 'Chambre en location'),
                           ('CASE', 'Case / Concession')]:
            get_or_create(TypeLogement, {'code_type': code}, libelle_type=lib)

        for code, lib in [('BETON', 'Béton / Parpaing'), ('BOIS', 'Bois'),
                           ('BANCO', 'Banco / Terre'), ('TOLE', 'Tôle'), ('PAILLE', 'Paille / Tige')]:
            get_or_create(MateriauMur, {'code_materiau': code}, libelle_materiau=lib)

        for code, lib in [('TOLE', 'Tôle'), ('TUILE', 'Tuile'),
                           ('BETON', 'Béton'), ('PAILLE', 'Paille / Chaume')]:
            get_or_create(MateriauToit, {'code_materiau': code}, libelle_materiau=lib)

        for code, lib in [('ROBINET_INT', 'Robinet intérieur'), ('BORNE_FONTAINE', 'Borne-fontaine'),
                           ('PUITS', 'Puits'), ('COURS_EAU', "Cours d'eau"), ('ACHETEE', 'Eau achetée')]:
            get_or_create(SourceEau, {'code_source': code}, libelle_source=lib)

        for code, lib in [('WC_INT', 'WC intérieur'), ('LATRINE_COUV', 'Latrine couverte'),
                           ('LATRINE_NON_COUV', 'Latrine non couverte'), ('NATURE', 'Nature')]:
            get_or_create(TypeToilette, {'code_type': code}, libelle_type=lib)

        for code, lib in [('DISTRICT', 'District'), ('REGION', 'Région'),
                           ('DEPARTEMENT', 'Département'), ('COMMUNE', 'Commune'),
                           ('SOUS_PREF', 'Sous-préfecture')]:
            get_or_create(TypeLocalite, {'code_type': code}, libelle_type=lib)

        for code, lib in [
            ('AGRI', 'Agriculture / Élevage'), ('COMM', 'Commerce'),
            ('ENSEIGNANT', 'Enseignement'), ('SANTE', 'Santé / Médecine'),
            ('ARTISAN', 'Artisanat'), ('TRANSPORT', 'Transport'),
            ('ADMIN', 'Administration publique'), ('BTP', 'Bâtiment / Travaux publics'),
            ('INFORM', 'Informatique / Télécommunications'), ('AUTRE', 'Autre profession'),
        ]:
            get_or_create(Profession, {'code_profession': code}, libelle_profession=lib)

        db.session.commit()
        click.echo('✓ Tables de référence peuplées.')

        # ══════════════════════════════════════════════════════════════════
        # 2. STRUCTURE TERRITORIALE — Commune d'Abobo
        # ══════════════════════════════════════════════════════════════════

        t_commune = TypeLocalite.query.filter_by(code_type='COMMUNE').first()

        localite = get_or_create(
            LocaliteAdministrative,
            {'code_localite': 'ABJ-ABO'},
            nom_localite="Commune d'Abobo",
            id_type_localite=t_commune.id_type_localite,
        )

        # Quartiers
        q_bao = get_or_create(Quartier, {'code_quartier': 'ABO-BAO'},
                               nom_quartier='Abobo-Baoulé', id_localite=localite.id_localite)
        q_dr  = get_or_create(Quartier, {'code_quartier': 'ABO-DR'},
                               nom_quartier='Abobo-Derrière Rails', id_localite=localite.id_localite)
        q_sam = get_or_create(Quartier, {'code_quartier': 'ABO-SAM'},
                               nom_quartier='Samaké', id_localite=localite.id_localite)
        q_clo = get_or_create(Quartier, {'code_quartier': 'ABO-CLO'},
                               nom_quartier='Clouétcha', id_localite=localite.id_localite)

        # Zones de dénombrement
        zd138 = get_or_create(ZoneDenombrement, {'code_zd': 'ZD-138'},
                               id_localite=localite.id_localite, id_quartier=q_bao.id_quartier)
        zd201 = get_or_create(ZoneDenombrement, {'code_zd': 'ZD-201'},
                               id_localite=localite.id_localite, id_quartier=q_dr.id_quartier)
        zd202 = get_or_create(ZoneDenombrement, {'code_zd': 'ZD-202'},
                               id_localite=localite.id_localite, id_quartier=q_sam.id_quartier)
        zd203 = get_or_create(ZoneDenombrement, {'code_zd': 'ZD-203'},
                               id_localite=localite.id_localite, id_quartier=q_clo.id_quartier)

        # Îlots ZD-138
        il138_1 = get_or_create(Ilot, {'code_ilot': 'ZD138-IL01'}, numero_ilot=1, id_zd=zd138.id_zd)
        il138_2 = get_or_create(Ilot, {'code_ilot': 'ZD138-IL02'}, numero_ilot=2, id_zd=zd138.id_zd)
        il138_3 = get_or_create(Ilot, {'code_ilot': 'ZD138-IL03'}, numero_ilot=3, id_zd=zd138.id_zd)
        il138_4 = get_or_create(Ilot, {'code_ilot': 'ZD138-IL04'}, numero_ilot=4, id_zd=zd138.id_zd)

        # Îlots ZD-201
        il201_1 = get_or_create(Ilot, {'code_ilot': 'ZD201-IL01'}, numero_ilot=1, id_zd=zd201.id_zd)
        il201_2 = get_or_create(Ilot, {'code_ilot': 'ZD201-IL02'}, numero_ilot=2, id_zd=zd201.id_zd)
        il201_3 = get_or_create(Ilot, {'code_ilot': 'ZD201-IL03'}, numero_ilot=3, id_zd=zd201.id_zd)

        # Îlots ZD-202
        il202_1 = get_or_create(Ilot, {'code_ilot': 'ZD202-IL01'}, numero_ilot=1, id_zd=zd202.id_zd)
        il202_2 = get_or_create(Ilot, {'code_ilot': 'ZD202-IL02'}, numero_ilot=2, id_zd=zd202.id_zd)

        # Îlots ZD-203
        il203_1 = get_or_create(Ilot, {'code_ilot': 'ZD203-IL01'}, numero_ilot=1, id_zd=zd203.id_zd)
        il203_2 = get_or_create(Ilot, {'code_ilot': 'ZD203-IL02'}, numero_ilot=2, id_zd=zd203.id_zd)

        db.session.commit()
        click.echo('✓ Structure territoriale créée.')

        # ══════════════════════════════════════════════════════════════════
        # 3. UTILISATEURS
        # ══════════════════════════════════════════════════════════════════

        users_data = [
            # (nom, prenom, email, pwd, role, tel)
            ('Système',  'Admin',       'admin@recenstat.ci',        'admin1234',        'ADMINISTRATEUR', None),
            ('Test',     'Superviseur', 'superviseur@recenstat.ci',  'superviseur1234',  'SUPERVISEUR',    None),
            ('Test',     'Enquêteur',   'enqueteur@recenstat.ci',    'enqueteur1234',    'ENQUETEUR',      None),
            ('BIYEN',    'Abdoul',      'biyen@recenstat.ci',        'biyen1234',        'ENQUETEUR',      '0701234567'),
            ('ZOH',      'Arthur',      'zoh@recenstat.ci',          'zoh1234',          'ENQUETEUR',      '0709876543'),
            ('BOUITI',   'Marc',        'bouiti@recenstat.ci',       'bouiti1234',       'ADMINISTRATEUR', '0777001122'),
        ]

        for nom, prenom, email, pwd, role, tel in users_data:
            if not Utilisateur.query.filter_by(email=email).first():
                u = Utilisateur(nom=nom, prenom=prenom, email=email, role=role,
                                actif=True, telephone=tel)
                u.set_password(pwd)
                db.session.add(u)

        db.session.commit()
        click.echo('✓ Comptes utilisateurs créés.')

        # ══════════════════════════════════════════════════════════════════
        # 4. AFFECTATIONS
        # ══════════════════════════════════════════════════════════════════

        biyen  = Utilisateur.query.filter_by(email='biyen@recenstat.ci').first()
        zoh    = Utilisateur.query.filter_by(email='zoh@recenstat.ci').first()
        enq_test = Utilisateur.query.filter_by(email='enqueteur@recenstat.ci').first()

        def affecter(utilisateur, zd):
            if utilisateur and not AffectationZD.query.filter_by(
                    id_utilisateur=utilisateur.id_utilisateur, id_zd=zd.id_zd).first():
                db.session.add(AffectationZD(
                    id_utilisateur=utilisateur.id_utilisateur,
                    id_zd=zd.id_zd,
                    date_debut=date(2026, 3, 1),
                    actif=True,
                ))

        affecter(biyen,    zd138)
        affecter(zoh,      zd201)
        affecter(enq_test, zd138)

        db.session.commit()
        click.echo('✓ Affectations créées.')

        # ══════════════════════════════════════════════════════════════════
        # 5. MÉNAGES, LOGEMENTS, INDIVIDUS, PASSAGES
        # ══════════════════════════════════════════════════════════════════

        # Références FK (lues une fois)
        ref = {
            'tlog': {r.code_type: r.id_type_logement  for r in TypeLogement.query.all()},
            'mur':  {r.code_materiau: r.id_materiau_mur  for r in MateriauMur.query.all()},
            'toit': {r.code_materiau: r.id_materiau_toit for r in MateriauToit.query.all()},
            'eau':  {r.code_source: r.id_source_eau      for r in SourceEau.query.all()},
            'wc':   {r.code_type: r.id_type_toilette     for r in TypeToilette.query.all()},
            'stm':  {r.code_statut: r.id_statut_menage   for r in StatutMenage.query.all()},
            'stp':  {r.code_statut: r.id_statut_passage  for r in StatutPassage.query.all()},
            'prof': {r.code_profession: r.id_profession  for r in Profession.query.all()},
        }

        ilots_map = {
            'ZD138-IL01': il138_1, 'ZD138-IL02': il138_2,
            'ZD138-IL03': il138_3, 'ZD138-IL04': il138_4,
            'ZD201-IL01': il201_1, 'ZD201-IL02': il201_2,
            'ZD201-IL03': il201_3,
        }
        zd_map = {
            'ZD138-IL01': zd138, 'ZD138-IL02': zd138,
            'ZD138-IL03': zd138, 'ZD138-IL04': zd138,
            'ZD201-IL01': zd201, 'ZD201-IL02': zd201,
            'ZD201-IL03': zd201,
        }
        enq_map = {
            'ZD138-IL01': biyen, 'ZD138-IL02': biyen,
            'ZD138-IL03': biyen, 'ZD138-IL04': biyen,
            'ZD201-IL01': zoh,   'ZD201-IL02': zoh,
            'ZD201-IL03': zoh,
        }

        # ──────────────────────────────────────────────────────────────────
        # Données brutes des ménages
        # Format individu : (nom, prenom, date_naissance, sexe, lien, est_chef,
        #                    sit_mat, niv_instr, stat_scol, stat_act, sait_lire, prof_code)
        # Format passage  : (numero, date_passage, heure, stat_passage, observation)
        # ──────────────────────────────────────────────────────────────────

        MENAGES = [

            # ══ ZD-138 — Îlot 1 ══════════════════════════════════════════

            {
                'ilot': 'ZD138-IL01', 'statut': 'VALIDE',
                'log': ('MAISON', 'BETON', 'TOLE',  'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('KONAN',   'Kouamé',     date(1981, 3, 15), 'M', 'CHEF',        True,  'MARIE_MONO',  'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'ENSEIGNANT'),
                    ('KONAN',   'Aminata',    date(1988, 7, 22), 'F', 'CONJOINT',    False, 'MARIE_MONO',  'SECONDAIRE_2', 'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('KONAN',   'Stéphane',   date(2006, 2, 10), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('KONAN',   'Mariame',    date(2011, 5, 18), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('KONAN',   'Théodore',   date(2016, 9, 4),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 10), time(9, 30), 'COMPLET', 'Ménage coopératif, données complètes.'),
                ],
            },

            {
                'ilot': 'ZD138-IL01', 'statut': 'VALIDE',
                'log': ('MAISON', 'BANCO', 'TOLE',  'BORNE_FONTAINE',  'LATRINE_COUV'),
                'individus': [
                    ('DIALLO',  'Mamadou',    date(1974, 1, 5),  'M', 'CHEF',        True,  'MARIE_POLY',  'PRIMAIRE',     'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('DIALLO',  'Fatoumata',  date(1982, 6, 14), 'F', 'CONJOINT',    False, 'MARIE_POLY',  'AUCUN',        'JAMAIS_SCOLARISE',   'MENAGERE',        False, None),
                    ('DIALLO',  'Mariam',     date(1994, 11, 3), 'F', 'CONJOINT',    False, 'MARIE_POLY',  'PRIMAIRE',     'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('DIALLO',  'Ibrahim',    date(2008, 4, 20), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('DIALLO',  'Aminata',    date(2014, 2, 28), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('DIALLO',  'Moussa',     date(2019, 8, 12), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('DIALLO',  'Kadiatou',   date(2024, 1, 17), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 11), time(10, 0), 'COMPLET', 'Chef de ménage très accueillant.'),
                ],
            },

            {
                'ilot': 'ZD138-IL01', 'statut': 'EN_COURS',
                'log': ('CHAMBRE', 'TOLE', 'TOLE',  'ACHETEE',         'LATRINE_NON_COUV'),
                'individus': [
                    ('SYLLA',   'Oumar',      date(1997, 12, 8), 'M', 'CHEF',        True,  'CELIBATAIRE', 'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('SYLLA',   'Ibrahima',   date(2002, 4, 15), 'M', 'FRERE_SOEUR', False, 'CELIBATAIRE', 'SECONDAIRE_2', 'ABANDONNE',          'CHOMEUR',         True,  None),
                    ('SYLLA',   'Fatoumata',  date(2005, 9, 22), 'F', 'FRERE_SOEUR', False, 'CELIBATAIRE', 'SECONDAIRE_2', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                ],
                'passages': [],
            },

            # ══ ZD-138 — Îlot 2 ══════════════════════════════════════════

            {
                'ilot': 'ZD138-IL02', 'statut': 'VALIDE',
                'log': ('VILLA', 'BETON', 'BETON', 'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('N\'GUESSAN', 'Koffi',   date(1991, 5, 12), 'M', 'CHEF',        True,  'MARIE_MONO',  'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'BTP'),
                    ('N\'GUESSAN', 'Awa',     date(1997, 3, 25), 'F', 'CONJOINT',    False, 'MARIE_MONO',  'SECONDAIRE_1', 'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('N\'GUESSAN', 'Jean',    date(2018, 5, 22), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('N\'GUESSAN', 'Christelle', date(2021, 2, 3), 'F', 'ENFANT',   False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                    ('YAO',     'Koukougnon', date(1958, 7, 16), 'M', 'PERE_MERE',  False, 'VEUF',        'AUCUN',        'JAMAIS_SCOLARISE',   'RETRAITE',        False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 12), time(8, 45), 'COMPLET', 'Famille étendue, grand-père présent.'),
                ],
            },

            {
                'ilot': 'ZD138-IL02', 'statut': 'SOUMIS',
                'log': ('MAISON', 'BETON', 'TOLE',  'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('TRAORÉ',  'Bakary',     date(1984, 9, 28), 'M', 'CHEF',        True,  'MARIE_MONO',  'SECONDAIRE_1', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'TRANSPORT'),
                    ('TRAORÉ',  'Salimata',   date(1990, 4, 7),  'F', 'CONJOINT',    False, 'MARIE_MONO',  'PRIMAIRE',     'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('TRAORÉ',  'Seydou',     date(2010, 6, 24), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('TRAORÉ',  'Aïssatou',   date(2012, 11, 3), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('TRAORÉ',  'Kalil',      date(2022, 3, 19), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 14), time(11, 0), 'COMPLET', 'Les deux époux actifs, deux enfants scolarisés.'),
                ],
            },

            {
                'ilot': 'ZD138-IL02', 'statut': 'VALIDE',
                'log': ('MAISON', 'BETON', 'TOLE',  'ROBINET_INT',    'LATRINE_COUV'),
                'individus': [
                    ('OUATTARA', 'Mariam',    date(1968, 4, 7),  'F', 'CHEF',        True,  'VEUF',        'PRIMAIRE',     'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('OUATTARA', 'Adama',     date(1998, 6, 17), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'INFORM'),
                    ('OUATTARA', 'Nadia',     date(2002, 12, 1), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SUPERIEUR',    'NON_SCOLARISE',      'CHOMEUR',         True,  None),
                    ('OUATTARA', 'Fatima',    date(2023, 5, 14), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 15), time(9, 15), 'COMPLET', 'Femme chef de ménage, veuve. Bon accueil.'),
                ],
            },

            {
                'ilot': 'ZD138-IL02', 'statut': 'RENVOYE',
                'log': ('CASE', 'BANCO', 'PAILLE', 'PUITS',           'NATURE'),
                'individus': [
                    ('KONE',    'Arouna',     date(1982, 8, 17), 'M', 'CHEF',        True,  'MARIE_MONO',  'AUCUN',        'JAMAIS_SCOLARISE',   'ACTIF_OCCUPE',    False, 'AGRI'),
                    ('KONE',    'Hawa',       date(1988, 2, 11), 'F', 'CONJOINT',    False, 'MARIE_MONO',  'AUCUN',        'JAMAIS_SCOLARISE',   'MENAGERE',        False, None),
                    ('KONE',    'Drissa',     date(2009, 4, 30), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('KONE',    'Mariam',     date(2014, 7, 19), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('KONE',    'Aly',        date(2019, 3, 15), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('KONE',    'Seydou',     date(2023, 1, 25), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 16), time(8, 0), 'PARTIEL', 'Données incomplètes : date naissance chef manquante. À corriger.'),
                ],
            },

            # ══ ZD-138 — Îlot 3 ══════════════════════════════════════════

            {
                'ilot': 'ZD138-IL03', 'statut': 'VALIDE',
                'log': ('MAISON', 'BETON', 'TOLE',  'BORNE_FONTAINE',  'LATRINE_COUV'),
                'individus': [
                    ('CISSÉ',   'Modibo',     date(1995, 10, 19), 'M', 'CHEF',       True,  'UNION_LIBRE', 'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'ARTISAN'),
                    ('CISSÉ',   'Bintou',     date(2000, 3, 8),   'F', 'CONJOINT',   False, 'UNION_LIBRE', 'SECONDAIRE_1', 'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('CISSÉ',   'Ibrahima',   date(2022, 4, 20),  'M', 'ENFANT',     False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                    ('CISSÉ',   'Hawa',       date(2025, 1, 10),  'F', 'ENFANT',     False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 17), time(14, 0), 'COMPLET', 'Jeune couple, artisan du quartier.'),
                ],
            },

            {
                'ilot': 'ZD138-IL03', 'statut': 'RENVOYE',
                'log': ('MAISON', 'BANCO', 'TOLE',  'BORNE_FONTAINE',  'LATRINE_NON_COUV'),
                'individus': [
                    ('BAMBA',   'Koné',       date(1978, 9, 15), 'M', 'CHEF',        True,  'DIVORCE',     'AUCUN',        'JAMAIS_SCOLARISE',   'ACTIF_OCCUPE',    False, 'AGRI'),
                    ('BAMBA',   'Soumaïla',   date(2004, 7, 16), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'ABANDONNE',          'CHOMEUR',         True,  None),
                    ('BAMBA',   'Rokia',      date(2007, 8, 5),  'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('BAMBA',   'Issa',       date(2015, 7, 19), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 18), time(15, 30), 'PARTIEL', "Lien chef de ménage non renseigné pour l'enfant Issa. À corriger."),
                ],
            },

            {
                'ilot': 'ZD138-IL03', 'statut': 'SOUMIS',
                'log': ('APPART', 'BETON', 'BETON', 'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('YEBOUÉ',  'Franck',     date(1988, 3, 25), 'M', 'CHEF',        True,  'MARIE_MONO',  'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'ADMIN'),
                    ('YEBOUÉ',  'Marie',      date(1994, 7, 4),  'F', 'CONJOINT',    False, 'MARIE_MONO',  'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'SANTE'),
                    ('YEBOUÉ',  'Arthur',     date(2020, 6, 5),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('YEBOUÉ',  'Carole',     date(2022, 11, 12),'F', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 19), time(18, 0), 'COMPLET', 'Couple de cadres, deux enfants en bas âge.'),
                ],
            },

            # ══ ZD-138 — Îlot 4 ══════════════════════════════════════════

            {
                'ilot': 'ZD138-IL04', 'statut': 'EN_COURS',
                'log': ('MAISON', 'BANCO', 'TOLE',  'BORNE_FONTAINE',  'LATRINE_COUV'),
                'individus': [
                    ('DOUMBIA', 'Sekou',      date(1971, 7, 22), 'M', 'CHEF',        True,  'MARIE_POLY',  'PRIMAIRE',     'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('DOUMBIA', 'Djénéba',    date(1979, 6, 28), 'F', 'CONJOINT',    False, 'MARIE_POLY',  'AUCUN',        'JAMAIS_SCOLARISE',   'MENAGERE',        False, None),
                    ('DOUMBIA', 'Lamine',     date(2001, 9, 14), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'ABANDONNE',          'CHOMEUR',         True,  None),
                    ('DOUMBIA', 'Kadiatou',   date(2005, 10, 10),'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('DOUMBIA', 'Boubacar',   date(2012, 11, 3), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('DOUMBIA', 'Mariame',    date(2017, 8, 5),  'F', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('DOUMBIA', 'Salif',      date(2021, 3, 17), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 20), time(9, 0), 'ABSENT', 'Premier passage : ménage absent. RDV fixé.'),
                ],
            },

            {
                'ilot': 'ZD138-IL04', 'statut': 'VALIDE',
                'log': ('VILLA', 'BETON', 'BETON', 'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('KOUAKOU', 'Yao',        date(1964, 2, 19), 'M', 'CHEF',        True,  'VEUF',        'SECONDAIRE_2', 'NON_SCOLARISE',      'RETRAITE',        True,  None),
                    ('KOUAKOU', 'Serge',      date(1992, 9, 28), 'M', 'ENFANT',      False, 'MARIE_MONO',  'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'INFORM'),
                    ('KOUAKOU', 'Ange',       date(1996, 3, 8),  'F', 'SANS_LIEN',   False, 'MARIE_MONO',  'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'ENSEIGNANT'),
                    ('KOUAKOU', 'Emile',      date(2021, 2, 3),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                    ('KOUAKOU', 'Chloé',      date(2023, 6, 11), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 21), time(10, 30), 'COMPLET', 'Famille multi-générationnelle. Grand-père retraité.'),
                ],
            },

            # ══ ZD-201 — Îlot 1 ══════════════════════════════════════════

            {
                'ilot': 'ZD201-IL01', 'statut': 'VALIDE',
                'log': ('MAISON', 'BETON', 'TOLE',  'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('ASSI',    'Kofi',       date(1986, 7, 14), 'M', 'CHEF',        True,  'MARIE_MONO',  'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'BTP'),
                    ('ASSI',    'Edwige',     date(1991, 5, 12), 'F', 'CONJOINT',    False, 'MARIE_MONO',  'SECONDAIRE_1', 'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('ASSI',    'Jean-Philippe', date(2013, 9, 11),'M','ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('ASSI',    'Ama',        date(2016, 4, 3),  'F', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('ASSI',    'Kévin',      date(2019, 3, 15), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 22), time(9, 0), 'COMPLET', 'Chef travailleur du BTP, famille bien établie.'),
                ],
            },

            {
                'ilot': 'ZD201-IL01', 'statut': 'VALIDE',
                'log': ('MAISON', 'BANCO', 'TOLE',  'BORNE_FONTAINE',  'LATRINE_COUV'),
                'individus': [
                    ('TOURÉ',   'Abdoulaye',  date(1976, 3, 11), 'M', 'CHEF',        True,  'MARIE_POLY',  'SECONDAIRE_1', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'TRANSPORT'),
                    ('TOURÉ',   'Kadidja',    date(1984, 4, 9),  'F', 'CONJOINT',    False, 'MARIE_POLY',  'PRIMAIRE',     'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('TOURÉ',   'Mamadou',    date(2003, 5, 8),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'ABANDONNE',          'CHOMEUR',         True,  None),
                    ('TOURÉ',   'Bintou',     date(2006, 3, 22), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('TOURÉ',   'Ramata',     date(1996, 4, 22), 'F', 'CONJOINT',    False, 'MARIE_POLY',  'PRIMAIRE',     'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('TOURÉ',   'Cheick',     date(2025, 3, 1),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 23), time(10, 0), 'COMPLET', 'Ménage polygame avec trois conjointes et enfants variés.'),
                ],
            },

            {
                'ilot': 'ZD201-IL01', 'statut': 'SOUMIS',
                'log': ('CHAMBRE', 'BETON', 'TOLE', 'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('LOBA',    'Clément',    date(1999, 1, 30), 'M', 'CHEF',        True,  'CELIBATAIRE', 'SUPERIEUR',    'NON_SCOLARISE',      'CHOMEUR',         True,  None),
                    ('DJEDJE',  'Arnaud',     date(2001, 4, 15), 'M', 'SANS_LIEN',   False, 'CELIBATAIRE', 'SUPERIEUR',    'NON_SCOLARISE',      'CHOMEUR',         True,  None),
                    ('KOUAMÉ',  'Eric',       date(2000, 7, 16), 'M', 'SANS_LIEN',   False, 'CELIBATAIRE', 'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'INFORM'),
                ],
                'passages': [
                    (1, date(2026, 4, 24), time(19, 0), 'COMPLET', 'Colocataires diplômés. Deux au chômage.'),
                ],
            },

            # ══ ZD-201 — Îlot 2 ══════════════════════════════════════════

            {
                'ilot': 'ZD201-IL02', 'statut': 'VALIDE',
                'log': ('VILLA', 'BETON', 'BETON', 'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('GNAGNE',  'Paul',       date(1980, 10, 3), 'M', 'CHEF',        True,  'MARIE_MONO',  'SUPERIEUR',    'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'ADMIN'),
                    ('GNAGNE',  'Florence',   date(1986, 1, 31), 'F', 'CONJOINT',    False, 'MARIE_MONO',  'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'SANTE'),
                    ('GNAGNE',  'Thierry',    date(2007, 8, 5),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('GNAGNE',  'Sandra',     date(2010, 11, 3), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('GNAGNE',  'Laure',      date(2015, 7, 19), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('GNAGNE',  'Kevin',      date(2020, 6, 5),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 25), time(17, 30), 'COMPLET', 'Famille aisée, tous les enfants scolarisés.'),
                ],
            },

            {
                'ilot': 'ZD201-IL02', 'statut': 'SOUMIS',
                'log': ('MAISON', 'BETON', 'TOLE',  'ROBINET_INT',    'LATRINE_COUV'),
                'individus': [
                    ('DIOUF',   'Amadou',     date(1990, 1, 31), 'M', 'CHEF',        True,  'UNION_LIBRE', 'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('DIOUF',   'Aïssatou',   date(1998, 6, 17), 'F', 'CONJOINT',    False, 'UNION_LIBRE', 'SECONDAIRE_1', 'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('DIOUF',   'Ibrahima',   date(2021, 3, 17), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                    ('DIOUF',   'Aminata',    date(2023, 5, 14), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 26), time(11, 15), 'COMPLET', 'Union libre, deux jeunes enfants.'),
                ],
            },

            {
                'ilot': 'ZD201-IL02', 'statut': 'EN_COURS',
                'log': ('MAISON', 'BANCO', 'TOLE',  'ACHETEE',         'LATRINE_NON_COUV'),
                'individus': [
                    ('FOFANA',  'Issouf',     date(1983, 12, 1), 'M', 'CHEF',        True,  'MARIE_POLY',  'PRIMAIRE',     'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'AGRI'),
                    ('FOFANA',  'Binta',      date(1991, 5, 12), 'F', 'CONJOINT',    False, 'MARIE_POLY',  'AUCUN',        'JAMAIS_SCOLARISE',   'MENAGERE',        False, None),
                    ('FOFANA',  'Moussa',     date(2008, 2, 14), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('FOFANA',  'Kadiatou',   date(2011, 1, 17), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('FOFANA',  'Seydou',     date(2016, 9, 4),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('FOFANA',  'Ibrahim',    date(2022, 4, 20), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 4, 27), time(8, 30), 'RDV_FIXE', 'Famille nombreuse. RDV pour samedi matin.'),
                ],
            },

            # ══ ZD-201 — Îlot 3 ══════════════════════════════════════════

            {
                'ilot': 'ZD201-IL03', 'statut': 'SOUMIS',
                'log': ('MAISON', 'BETON', 'TOLE',  'BORNE_FONTAINE',  'LATRINE_COUV'),
                'individus': [
                    ('AHOUA',   'Mathias',    date(1993, 2, 14), 'M', 'CHEF',        True,  'MARIE_MONO',  'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'ARTISAN'),
                    ('AHOUA',   'Brigitte',   date(1999, 11, 25),'F', 'CONJOINT',    False, 'MARIE_MONO',  'SECONDAIRE_1', 'NON_SCOLARISE',      'MENAGERE',        True,  None),
                    ('AHOUA',   'Christian',  date(2020, 6, 5),  'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('AHOUA',   'Vanessa',    date(2024, 2, 18), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'AUCUN',        'JAMAIS_SCOLARISE',   'AUTRE_INACTIF',   False, None),
                ],
                'passages': [
                    (1, date(2026, 5, 2), time(10, 0), 'COMPLET', 'Jeune artisan, bon accueil.'),
                ],
            },

            {
                'ilot': 'ZD201-IL03', 'statut': 'EN_COURS',
                'log': ('MAISON', 'BANCO', 'TOLE',  'PUITS',           'LATRINE_NON_COUV'),
                'individus': [
                    ('COULIBALY','Ladji',     date(1961, 8, 30), 'M', 'CHEF',        True,  'MARIE_POLY',  'AUCUN',        'JAMAIS_SCOLARISE',   'RETRAITE',        False, None),
                    ('COULIBALY','Tenin',     date(1970, 11, 14),'F', 'CONJOINT',    False, 'MARIE_POLY',  'AUCUN',        'JAMAIS_SCOLARISE',   'MENAGERE',        False, None),
                    ('COULIBALY','Mariam',    date(1996, 3, 8),  'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('COULIBALY','Moussa',    date(2018, 5, 22), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                ],
                'passages': [
                    (1, date(2026, 5, 3), time(14, 30), 'ABSENT', 'Chef absent, épouse présente mais réticente.'),
                ],
            },

            {
                'ilot': 'ZD201-IL03', 'statut': 'EN_COURS',
                'log': ('MAISON', 'BETON', 'TOLE',  'ROBINET_INT',    'WC_INT'),
                'individus': [
                    ('ZANZAN',  'Rose',       date(1988, 3, 25), 'F', 'CHEF',        True,  'DIVORCE',     'SECONDAIRE_2', 'NON_SCOLARISE',      'ACTIF_OCCUPE',    True,  'COMM'),
                    ('ZANZAN',  'Carine',     date(2009, 4, 30), 'F', 'ENFANT',      False, 'CELIBATAIRE', 'SECONDAIRE_1', 'SCOLARISE',          'ELEVE_ETUDIANT',  True,  None),
                    ('ZANZAN',  'Didier',     date(2014, 2, 28), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                    ('ZANZAN',  'Franck',     date(2019, 8, 12), 'M', 'ENFANT',      False, 'CELIBATAIRE', 'PRIMAIRE',     'SCOLARISE',          'ELEVE_ETUDIANT',  False, None),
                ],
                'passages': [
                    (1, date(2026, 5, 4), time(16, 0), 'PARTIEL', 'Femme chef de ménage, divorcée. Données partielles, à compléter.'),
                ],
            },
        ]

        # ──────────────────────────────────────────────────────────────────
        # Insertion des ménages
        # ──────────────────────────────────────────────────────────────────
        log_counters = {}   # code_ilot -> count de logements créés
        men_counters = {}   # code_ilot -> count de ménages créés

        inserted_men = 0
        inserted_ind = 0
        inserted_pas = 0

        for spec in MENAGES:
            code_ilot = spec['ilot']
            ilot_obj  = ilots_map[code_ilot]
            zd_obj    = zd_map[code_ilot]
            enqueteur = enq_map[code_ilot]

            # compteurs par îlot
            log_counters.setdefault(code_ilot, 0)
            men_counters.setdefault(code_ilot, 0)

            # ── Logement ──────────────────────────────────────────────────
            log_counters[code_ilot] += 1
            code_log = make_code_logement(code_ilot, log_counters[code_ilot])

            if not Logement.query.filter_by(code_logement=code_log).first():
                tl, mm, mt, se, tt = spec['log']
                logement = Logement(
                    numero_logement  = log_counters[code_ilot],
                    code_logement    = code_log,
                    id_ilot          = ilot_obj.id_ilot,
                    id_type_logement = ref['tlog'][tl],
                    id_materiau_mur  = ref['mur'][mm],
                    id_materiau_toit = ref['toit'][mt],
                    id_source_eau    = ref['eau'][se],
                    id_type_toilette = ref['wc'][tt],
                )
                db.session.add(logement)
                db.session.flush()
            else:
                logement = Logement.query.filter_by(code_logement=code_log).first()

            # ── Ménage ────────────────────────────────────────────────────
            men_counters[code_ilot] += 1
            code_men = make_code_menage(zd_obj.code_zd, code_ilot, men_counters[code_ilot])

            if not Menage.query.filter_by(code_menage=code_men).first():
                menage = Menage(
                    numero_menage    = men_counters[code_ilot],
                    code_menage      = code_men,
                    id_logement      = logement.id_logement,
                    id_statut_menage = ref['stm'][spec['statut']],
                )
                db.session.add(menage)
                db.session.flush()
                inserted_men += 1

                # ── Individus ─────────────────────────────────────────────
                for ind in spec['individus']:
                    nom, prenom, dn, sexe, lien, est_chef, mat, instr, scol, act, lire, prof_code = ind
                    individu = Individu(
                        id_menage              = menage.id_menage,
                        nom                    = nom,
                        prenom                 = prenom,
                        date_naissance         = dn,
                        sexe                   = sexe,
                        lien_chef_menage       = lien,
                        est_chef_menage        = est_chef,
                        situation_matrimoniale = mat,
                        niveau_instruction     = instr,
                        statut_scolarisation   = scol,
                        statut_activite        = act,
                        sait_lire_ecrire       = lire,
                        id_profession          = ref['prof'].get(prof_code) if prof_code else None,
                    )
                    db.session.add(individu)
                    inserted_ind += 1

                # ── Passages ──────────────────────────────────────────────
                for pas in spec['passages']:
                    num, d_pas, h_pas, stat_pas, obs = pas
                    if enqueteur:
                        passage = PassageCollecte(
                            id_menage         = menage.id_menage,
                            id_utilisateur    = enqueteur.id_utilisateur,
                            numero_passage    = num,
                            date_passage      = d_pas,
                            heure_passage     = h_pas,
                            id_statut_passage = ref['stp'][stat_pas],
                            observations      = obs,
                        )
                        db.session.add(passage)
                        inserted_pas += 1

        db.session.commit()
        click.echo(f'✓ {inserted_men} ménages créés, {inserted_ind} individus, {inserted_pas} passages.')

        # ══════════════════════════════════════════════════════════════════
        # Récapitulatif
        # ══════════════════════════════════════════════════════════════════
        click.echo('\n══════════════════════════════════')
        click.echo('  Seed terminé avec succès !')
        click.echo('══════════════════════════════════')
        click.echo('\nComptes disponibles :')
        click.echo('  admin@recenstat.ci        / admin1234')
        click.echo('  superviseur@recenstat.ci  / superviseur1234')
        click.echo('  enqueteur@recenstat.ci    / enqueteur1234')
        click.echo('  biyen@recenstat.ci        / biyen1234   (enquêteur ZD-138)')
        click.echo('  zoh@recenstat.ci          / zoh1234     (enquêteur ZD-201)')
        click.echo('  bouiti@recenstat.ci       / bouiti1234  (administrateur)')
