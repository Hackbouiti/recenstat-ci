# Models package — import all models to register them with SQLAlchemy
from app.models.territoire import TypeLocalite, LocaliteAdministrative, Quartier, ZoneDenombrement, Ilot
from app.models.habitat import TypeLogement, MateriauMur, MateriauToit, SourceEau, TypeToilette, StatutMenage, Logement, Menage
from app.models.individu import Profession, Individu
from app.models.collecte import StatutPassage, Utilisateur, AffectationZD, PassageCollecte
