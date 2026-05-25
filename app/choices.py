SEXE = [('M', 'Masculin'), ('F', 'Féminin')]

LIEN_CHEF_MENAGE = [
    ('CHEF', 'Chef de ménage'),
    ('CONJOINT', 'Conjoint(e)'),
    ('ENFANT', 'Enfant'),
    ('PERE_MERE', 'Père / Mère'),
    ('FRERE_SOEUR', 'Frère / Sœur'),
    ('AUTRE_PARENT', 'Autre parent'),
    ('SANS_LIEN', 'Sans lien de parenté'),
]

SITUATION_MATRIMONIALE = [
    ('CELIBATAIRE', 'Célibataire'),
    ('MARIE_MONO', 'Marié(e) monogame'),
    ('MARIE_POLY', 'Marié(e) polygame'),
    ('DIVORCE', 'Divorcé(e)'),
    ('VEUF', 'Veuf / Veuve'),
    ('UNION_LIBRE', 'Union libre'),
]

NIVEAU_INSTRUCTION = [
    ('AUCUN', 'Aucun'),
    ('PRIMAIRE', 'Primaire'),
    ('SECONDAIRE_1', 'Secondaire 1er cycle'),
    ('SECONDAIRE_2', 'Secondaire 2nd cycle'),
    ('SUPERIEUR', 'Supérieur'),
]

STATUT_SCOLARISATION = [
    ('SCOLARISE', 'Scolarisé(e)'),
    ('NON_SCOLARISE', 'Non scolarisé(e)'),
    ('JAMAIS_SCOLARISE', 'Jamais scolarisé(e)'),
    ('ABANDONNE', 'A abandonné'),
]

STATUT_ACTIVITE = [
    ('ACTIF_OCCUPE', 'Actif occupé'),
    ('CHOMEUR', 'Chômeur'),
    ('ELEVE_ETUDIANT', 'Élève / Étudiant'),
    ('RETRAITE', 'Retraité'),
    ('MENAGERE', 'Ménagère'),
    ('AUTRE_INACTIF', 'Autre inactif'),
]

ROLE = [
    ('ADMINISTRATEUR', 'Administrateur'),
    ('SUPERVISEUR', 'Superviseur'),
    ('ENQUETEUR', 'Enquêteur'),
]

TRANSITIONS = {
    'EN_COURS': ['SOUMIS'],
    'SOUMIS':   ['VALIDE', 'RENVOYE'],
    'RENVOYE':  ['SOUMIS'],
    'VALIDE':   [],
}
