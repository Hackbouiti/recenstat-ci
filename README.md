# RecenStat-CI

Système d'information statistique de collecte et de gestion de données de recensement des ménages,
inspiré des pratiques du RGPH de l'Anstat en Côte d'Ivoire.

---

## Prérequis

- Python 3.10 ou supérieur
- PostgreSQL 14 ou supérieur installé et en cours d'exécution

---

## Installation

### 1. Cloner le projet

```bash
git clone <url-du-dépôt>
cd recenstat-ci
```

### 2. Créer l'environnement virtuel et installer les dépendances

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Créer la base de données PostgreSQL

```sql
CREATE DATABASE recenstat_ci;
```

Ou via la ligne de commande :

```bash
psql -U postgres -c "CREATE DATABASE recenstat_ci;"
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditer `.env` et renseigner vos valeurs :

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=une_cle_secrete_longue_et_aleatoire
DATABASE_URL=postgresql://postgres:votre_motdepasse@localhost:5432/recenstat_ci
```

### 5. Lancer les migrations

```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

### 6. Peupler la base de données (seed)

```bash
flask seed
```

Cette commande crée les tables de référence, la structure territoriale de test et les comptes utilisateurs.

### 7. Démarrer le serveur

```bash
flask run --host=0.0.0.0
```

Ou directement :

```bash
python run.py
```

---

## Accès à l'application

### Depuis la machine hôte

```
http://localhost:5000
```

### Depuis un autre appareil sur le même réseau Wi-Fi

1. Récupérer l'adresse IP locale de votre machine :
   - Windows : `ipconfig` → chercher "Adresse IPv4"
   - Linux/macOS : `ip addr` ou `ifconfig`
2. Accéder via : `http://<adresse_IP_de_votre_machine>:5000`

---

## Comptes de test

Disponibles après l'exécution du seed :

| Rôle           | Email                        | Mot de passe      |
|----------------|------------------------------|-------------------|
| Administrateur | admin@recenstat.ci           | admin1234         |
| Superviseur    | superviseur@recenstat.ci     | superviseur1234   |
| Enquêteur      | enqueteur@recenstat.ci       | enqueteur1234     |

---

## Structure du projet

```
recenstat-ci/
├── app/
│   ├── __init__.py          # Factory Flask, extensions
│   ├── config.py            # Configuration (SECRET_KEY, DATABASE_URL)
│   ├── choices.py           # Listes déroulantes (SEXE, ROLE, etc.)
│   ├── models/              # Modèles SQLAlchemy (19 tables)
│   ├── routes/              # Blueprints (auth, admin, enqueteur, stats)
│   ├── forms/               # Formulaires WTForms
│   ├── static/css/          # Charte graphique CSS
│   └── templates/           # Templates Jinja2
├── seeds/seed.py            # Données de référence + comptes de test
├── migrations/              # Fichiers Alembic
├── run.py                   # Point d'entrée
├── requirements.txt
└── .env.example
```

---

## Règles métier clés

- L'**âge** n'est jamais stocké — il est calculé dynamiquement depuis `date_naissance`.
- Le **code ménage** est généré automatiquement (`ZD-138-ZD138-IL01-MEN001`), jamais saisi manuellement.
- Un ménage ne peut être **soumis** que s'il contient au moins un membre.
- La **profession** est obligatoire si `statut_activite = ACTIF_OCCUPE`.
- Les **statistiques** ne portent que sur les ménages au statut `VALIDE`.
- Transitions de statut autorisées : `EN_COURS → SOUMIS → VALIDE` ou `SOUMIS → RENVOYE → SOUMIS`.
