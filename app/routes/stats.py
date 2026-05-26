import csv
import io
from datetime import date
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from app import db
from app.models.habitat import Menage, StatutMenage, Logement, SourceEau
from app.models.individu import Individu
from app.models.territoire import ZoneDenombrement, Ilot, Quartier, LocaliteAdministrative

stats_bp = Blueprint('stats', __name__)


def get_menages_valides(zd_id=None, quartier_id=None, commune_id=None):
    statut_valide = StatutMenage.query.filter_by(code_statut='VALIDE').first()
    if not statut_valide:
        return []

    q = Menage.query.filter_by(id_statut_menage=statut_valide.id_statut_menage)

    if zd_id:
        ilot_ids = [i.id_ilot for i in Ilot.query.filter_by(id_zd=zd_id).all()]
        log_ids  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()]
        q = q.filter(Menage.id_logement.in_(log_ids))
    elif quartier_id:
        zd_ids   = [z.id_zd for z in ZoneDenombrement.query.filter_by(id_quartier=quartier_id).all()]
        ilot_ids = [i.id_ilot for i in Ilot.query.filter(Ilot.id_zd.in_(zd_ids)).all()]
        log_ids  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()]
        q = q.filter(Menage.id_logement.in_(log_ids))
    elif commune_id:
        zd_ids   = [z.id_zd for z in ZoneDenombrement.query.filter_by(id_localite=commune_id).all()]
        ilot_ids = [i.id_ilot for i in Ilot.query.filter(Ilot.id_zd.in_(zd_ids)).all()]
        log_ids  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()]
        q = q.filter(Menage.id_logement.in_(log_ids))

    return q.all()


@stats_bp.route('/tableau_bord')
@login_required
def tableau_bord():
    communes   = LocaliteAdministrative.query.order_by(LocaliteAdministrative.nom_localite).all()
    quartiers  = Quartier.query.order_by(Quartier.nom_quartier).all()
    zones      = ZoneDenombrement.query.order_by(ZoneDenombrement.code_zd).all()

    commune_id  = request.args.get('commune_id', type=int)
    quartier_id = request.args.get('quartier_id', type=int)
    zd_id       = request.args.get('zd_id', type=int)

    menages = get_menages_valides(zd_id, quartier_id, commune_id)
    menage_ids = [m.id_menage for m in menages]

    individus = Individu.query.filter(Individu.id_menage.in_(menage_ids)).all() if menage_ids else []

    nb_menages  = len(menages)
    nb_individus = len(individus)
    taille_moy  = round(nb_individus / nb_menages, 2) if nb_menages > 0 else 0

    scolarises = [i for i in individus if i.statut_scolarisation == 'SCOLARISE']
    age_scol   = [i for i in individus if 6 <= i.age <= 24]
    taux_scol  = round(len(scolarises) / len(age_scol) * 100, 1) if age_scol else 0

    actifs_occupes = [i for i in individus if i.statut_activite == 'ACTIF_OCCUPE']
    age_actif = [i for i in individus if 15 <= i.age <= 64]
    taux_activite = round(len(actifs_occupes) / len(age_actif) * 100, 1) if age_actif else 0

    eau_potable_codes = {'ROBINET_INT', 'BORNE_FONTAINE', 'ACHETEE'}
    menages_eau = 0
    for m in menages:
        log = m.logement
        if log.source_eau and log.source_eau.code_source in eau_potable_codes:
            menages_eau += 1
    taux_eau = round(menages_eau / nb_menages * 100, 1) if nb_menages > 0 else 0

    # Pyramide des âges — tranches quinquennales
    # Ordre inversé : 80+ en haut, 0-4 en bas (sens naturel d'une pyramide)
    tranches = ['80+','75-79','70-74','65-69','60-64','55-59','50-54','45-49',
                '40-44','35-39','30-34','25-29','20-24','15-19','10-14','5-9','0-4']
    pyramide_h = []
    pyramide_f = []
    for label in tranches:
        if label == '80+':
            low, high = 80, 999
        else:
            low, high = map(int, label.split('-'))
        h = len([i for i in individus if i.sexe == 'M' and low <= i.age <= high])
        f = len([i for i in individus if i.sexe == 'F' and low <= i.age <= high])
        pyramide_h.append(-h)
        pyramide_f.append(f)

    # Répartition activités
    activite_labels = ['Actif occupé','Chômeur','Élève/Étudiant','Retraité','Ménagère','Autre inactif']
    activite_codes  = ['ACTIF_OCCUPE','CHOMEUR','ELEVE_ETUDIANT','RETRAITE','MENAGERE','AUTRE_INACTIF']
    activite_data   = [len([i for i in individus if i.statut_activite == c]) for c in activite_codes]

    # Taux scolarisation par ZD
    zd_scol_labels = []
    zd_scol_data   = []
    for zd in zones[:10]:
        ilot_ids_zd = [i.id_ilot for i in zd.ilots]
        log_ids_zd  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids_zd)).all()]
        men_ids_zd  = [m.id_menage for m in Menage.query.filter(
            Menage.id_logement.in_(log_ids_zd),
            Menage.id_statut_menage == (StatutMenage.query.filter_by(code_statut='VALIDE').first().id_statut_menage if StatutMenage.query.filter_by(code_statut='VALIDE').first() else -1)
        ).all()]
        ind_zd = Individu.query.filter(Individu.id_menage.in_(men_ids_zd)).all()
        age_s  = [i for i in ind_zd if 6 <= i.age <= 24]
        scol_s = [i for i in age_s if i.statut_scolarisation == 'SCOLARISE']
        taux   = round(len(scol_s) / len(age_s) * 100, 1) if age_s else 0
        zd_scol_labels.append(zd.code_zd)
        zd_scol_data.append(taux)

    # JSON pour les filtres cascadants côté JS
    all_quartiers_json = [
        {'id': q.id_quartier, 'nom': q.nom_quartier, 'id_localite': q.id_localite}
        for q in quartiers
    ]
    all_zones_json = [
        {
            'id': z.id_zd,
            'code': z.code_zd,
            'id_quartier': z.id_quartier,
            'id_localite': z.id_localite,
        }
        for z in zones
    ]

    return render_template('stats/tableau_bord.html',
        communes=communes, quartiers=quartiers, zones=zones,
        commune_id=commune_id, quartier_id=quartier_id, zd_id=zd_id,
        all_quartiers_json=all_quartiers_json, all_zones_json=all_zones_json,
        nb_menages=nb_menages, nb_individus=nb_individus, taille_moy=taille_moy,
        taux_scol=taux_scol, taux_activite=taux_activite, taux_eau=taux_eau,
        tranches=tranches, pyramide_h=pyramide_h, pyramide_f=pyramide_f,
        activite_labels=activite_labels, activite_data=activite_data,
        zd_scol_labels=zd_scol_labels, zd_scol_data=zd_scol_data,
    )


@stats_bp.route('/export_csv')
@login_required
def export_csv():
    commune_id  = request.args.get('commune_id', type=int)
    quartier_id = request.args.get('quartier_id', type=int)
    zd_id       = request.args.get('zd_id', type=int)

    menages    = get_menages_valides(zd_id, quartier_id, commune_id)
    menage_ids = [m.id_menage for m in menages]
    individus  = Individu.query.filter(Individu.id_menage.in_(menage_ids)).all() if menage_ids else []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'id_individu','id_menage','code_menage','nom','prenom',
        'date_naissance','age','sexe','lien_chef_menage','est_chef_menage',
        'situation_matrimoniale','niveau_instruction','statut_scolarisation',
        'statut_activite','sait_lire_ecrire','profession'
    ])
    for ind in individus:
        writer.writerow([
            ind.id_individu,
            ind.id_menage,
            ind.menage.code_menage,
            ind.nom,
            ind.prenom,
            ind.date_naissance.isoformat(),
            ind.age,
            ind.sexe,
            ind.lien_chef_menage,
            ind.est_chef_menage,
            ind.situation_matrimoniale,
            ind.niveau_instruction,
            ind.statut_scolarisation or '',
            ind.statut_activite,
            ind.sait_lire_ecrire,
            ind.profession.libelle_profession if ind.profession else '',
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=recenstat_export.csv'}
    )
