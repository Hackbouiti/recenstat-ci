from datetime import date, datetime, date as dt_date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.collecte import AffectationZD, PassageCollecte
from app.models.habitat import Menage, StatutMenage, Logement, TypeLogement, MateriauMur, MateriauToit, SourceEau, TypeToilette
from app.models.territoire import ZoneDenombrement, Ilot
from app.models.individu import Individu, Profession
from app.forms.menage import MenageForm, PassageForm
from app.forms.individu import IndividuForm
from app.choices import TRANSITIONS

enqueteur_bp = Blueprint('enqueteur', __name__)


def enqueteur_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('ENQUETEUR', 'ADMINISTRATEUR', 'SUPERVISEUR'):
            flash('Accès non autorisé.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def zd_autorisees(id_utilisateur):
    return [a.id_zd for a in AffectationZD.query.filter_by(
        id_utilisateur=id_utilisateur, actif=True).all()]


def generer_code_menage(id_ilot):
    ilot = Ilot.query.get(id_ilot)
    zd   = ZoneDenombrement.query.get(ilot.id_zd)
    n    = Menage.query.join(Logement).filter(Logement.id_ilot == id_ilot).count()
    return f"{zd.code_zd}-{ilot.code_ilot}-MEN{n + 1:03d}"


def generer_code_logement(id_ilot):
    ilot = Ilot.query.get(id_ilot)
    n    = Logement.query.filter_by(id_ilot=id_ilot).count()
    return f"{ilot.code_ilot}-LOG{n + 1:03d}"


@enqueteur_bp.route('/dashboard')
@login_required
@enqueteur_required
def dashboard():
    zd_ids = zd_autorisees(current_user.id_utilisateur)
    zones  = ZoneDenombrement.query.filter(ZoneDenombrement.id_zd.in_(zd_ids)).all()

    progression = []
    for zd in zones:
        ilot_ids = [i.id_ilot for i in zd.ilots]
        log_ids  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()] if ilot_ids else []
        total    = Menage.query.filter(Menage.id_logement.in_(log_ids)).count() if log_ids else 0
        st_val   = StatutMenage.query.filter_by(code_statut='VALIDE').first()
        valides  = Menage.query.filter(
            Menage.id_logement.in_(log_ids),
            Menage.id_statut_menage == st_val.id_statut_menage
        ).count() if (log_ids and st_val) else 0
        pct = round(valides / total * 100) if total > 0 else 0
        progression.append({'zd': zd, 'total': total, 'valides': valides, 'pct': pct})

    passages_jour = PassageCollecte.query.filter_by(
        id_utilisateur=current_user.id_utilisateur,
        date_passage=date.today()
    ).count()

    return render_template('enqueteur/dashboard.html',
        progression=progression,
        passages_jour=passages_jour,
        now=datetime.now(),
    )


@enqueteur_bp.route('/zd/<int:id_zd>/menages')
@login_required
@enqueteur_required
def menages_zd(id_zd):
    if current_user.role == 'ENQUETEUR' and id_zd not in zd_autorisees(current_user.id_utilisateur):
        flash('Vous n\'êtes pas autorisé à accéder à cette zone.', 'danger')
        return redirect(url_for('enqueteur.dashboard'))

    zd      = ZoneDenombrement.query.get_or_404(id_zd)
    query   = request.args.get('q', '').strip()
    ilot_ids = [i.id_ilot for i in zd.ilots]
    log_ids  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()] if ilot_ids else []

    menages_q = Menage.query.filter(Menage.id_logement.in_(log_ids))
    if query:
        menages_q = menages_q.filter(Menage.code_menage.ilike(f'%{query}%'))

    menages = menages_q.order_by(Menage.code_menage).all()
    return render_template('enqueteur/menages.html', zd=zd, menages=menages, query=query)


@enqueteur_bp.route('/menage/nouveau', methods=['GET', 'POST'])
@login_required
@enqueteur_required
def nouveau_menage():
    zd_ids = zd_autorisees(current_user.id_utilisateur)
    zones  = ZoneDenombrement.query.filter(ZoneDenombrement.id_zd.in_(zd_ids)).all()

    form = MenageForm()
    form.id_zd.choices   = [(z.id_zd, z.code_zd) for z in zones]
    form.id_ilot.choices = [(0, '--- Sélectionner une ZD d\'abord ---')]

    form.id_type_logement.choices = [(t.id_type_logement, t.libelle_type) for t in TypeLogement.query.all()]
    form.id_materiau_mur.choices  = [(m.id_materiau_mur, m.libelle_materiau) for m in MateriauMur.query.all()]
    form.id_materiau_toit.choices = [(m.id_materiau_toit, m.libelle_materiau) for m in MateriauToit.query.all()]
    form.id_source_eau.choices    = [(s.id_source_eau, s.libelle_source) for s in SourceEau.query.all()]
    form.id_type_toilette.choices = [(t.id_type_toilette, t.libelle_type) for t in TypeToilette.query.all()]

    if request.method == 'POST':
        id_zd   = request.form.get('id_zd', type=int)
        id_ilot = request.form.get('id_ilot', type=int)
        ilots   = Ilot.query.filter_by(id_zd=id_zd).all() if id_zd else []
        form.id_ilot.choices = [(i.id_ilot, i.code_ilot) for i in ilots]

    if form.validate_on_submit():
        id_ilot = form.id_ilot.data
        ilot    = Ilot.query.get(id_ilot)

        if current_user.role == 'ENQUETEUR' and ilot.id_zd not in zd_ids:
            flash('Vous n\'êtes pas autorisé pour cet îlot.', 'danger')
            return redirect(url_for('enqueteur.nouveau_menage'))

        code_log     = generer_code_logement(id_ilot)
        n_log        = Logement.query.filter_by(id_ilot=id_ilot).count()
        logement     = Logement(
            numero_logement  = n_log + 1,
            code_logement    = code_log,
            id_ilot          = id_ilot,
            id_type_logement = form.id_type_logement.data,
            id_materiau_mur  = form.id_materiau_mur.data,
            id_materiau_toit = form.id_materiau_toit.data,
            id_source_eau    = form.id_source_eau.data,
            id_type_toilette = form.id_type_toilette.data,
        )
        db.session.add(logement)
        db.session.flush()

        statut_en_cours = StatutMenage.query.filter_by(code_statut='EN_COURS').first()
        code_menage     = generer_code_menage(id_ilot)
        n_men           = Menage.query.join(Logement).filter(Logement.id_ilot == id_ilot).count()
        menage          = Menage(
            numero_menage    = n_men + 1,
            code_menage      = code_menage,
            id_logement      = logement.id_logement,
            id_statut_menage = statut_en_cours.id_statut_menage,
        )
        db.session.add(menage)
        db.session.commit()
        flash(f'Ménage {code_menage} créé avec succès.', 'success')
        return redirect(url_for('enqueteur.fiche_menage', id_menage=menage.id_menage))

    return render_template('enqueteur/nouveau_menage.html', form=form, zones=zones)


@enqueteur_bp.route('/api/ilots/<int:id_zd>')
@login_required
def api_ilots(id_zd):
    ilots = Ilot.query.filter_by(id_zd=id_zd).all()
    return {'ilots': [{'id': i.id_ilot, 'code': i.code_ilot} for i in ilots]}


@enqueteur_bp.route('/menage/<int:id_menage>')
@login_required
@enqueteur_required
def fiche_menage(id_menage):
    menage = Menage.query.get_or_404(id_menage)
    ilot   = menage.logement.ilot
    zd     = ilot.zone_denombrement

    if current_user.role == 'ENQUETEUR' and zd.id_zd not in zd_autorisees(current_user.id_utilisateur):
        flash('Accès non autorisé à ce ménage.', 'danger')
        return redirect(url_for('enqueteur.dashboard'))

    passages = sorted(menage.passages, key=lambda p: p.date_passage, reverse=True)
    peut_soumettre = (
        len(menage.individus) > 0
        and menage.statut_menage.code_statut in TRANSITIONS
        and 'SOUMIS' in TRANSITIONS[menage.statut_menage.code_statut]
    )

    return render_template('enqueteur/fiche_menage.html',
        menage=menage, ilot=ilot, zd=zd,
        passages=passages, peut_soumettre=peut_soumettre,
    )


@enqueteur_bp.route('/menage/<int:id_menage>/soumettre', methods=['POST'])
@login_required
@enqueteur_required
def soumettre_menage(id_menage):
    menage = Menage.query.get_or_404(id_menage)
    zd     = menage.logement.ilot.zone_denombrement

    if current_user.role == 'ENQUETEUR' and zd.id_zd not in zd_autorisees(current_user.id_utilisateur):
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('enqueteur.dashboard'))

    if len(menage.individus) == 0:
        flash('Impossible de soumettre un ménage sans membres.', 'danger')
        return redirect(url_for('enqueteur.fiche_menage', id_menage=id_menage))

    code_actuel = menage.statut_menage.code_statut
    if 'SOUMIS' not in TRANSITIONS.get(code_actuel, []):
        flash('Ce ménage ne peut pas être soumis dans son état actuel.', 'danger')
        return redirect(url_for('enqueteur.fiche_menage', id_menage=id_menage))

    statut_soumis = StatutMenage.query.filter_by(code_statut='SOUMIS').first()
    menage.id_statut_menage = statut_soumis.id_statut_menage
    db.session.commit()
    flash(f'Ménage {menage.code_menage} soumis pour validation.', 'success')
    return redirect(url_for('enqueteur.fiche_menage', id_menage=id_menage))


@enqueteur_bp.route('/menage/<int:id_menage>/individu/nouveau', methods=['GET', 'POST'])
@login_required
@enqueteur_required
def nouveau_individu(id_menage):
    menage = Menage.query.get_or_404(id_menage)
    zd     = menage.logement.ilot.zone_denombrement

    if current_user.role == 'ENQUETEUR' and zd.id_zd not in zd_autorisees(current_user.id_utilisateur):
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('enqueteur.dashboard'))

    form = IndividuForm()
    professions = Profession.query.order_by(Profession.libelle_profession).all()
    form.id_profession.choices = [(0, '--- Sélectionner ---')] + [
        (p.id_profession, p.libelle_profession) for p in professions
    ]

    if form.validate_on_submit():
        statut_activite = form.statut_activite.data
        id_profession   = form.id_profession.data if form.id_profession.data != 0 else None

        if statut_activite == 'ACTIF_OCCUPE' and not id_profession:
            flash('La profession est obligatoire pour un actif occupé.', 'danger')
            return render_template('enqueteur/nouveau_individu.html', form=form, menage=menage)

        lien = form.lien_chef_menage.data
        est_chef = False
        if lien == 'CHEF':
            chef_existant = Individu.query.filter_by(id_menage=id_menage, est_chef_menage=True).first()
            if not chef_existant:
                est_chef = True

        statut_scol = form.statut_scolarisation.data or None

        individu = Individu(
            id_menage              = id_menage,
            nom                    = form.nom.data,
            prenom                 = form.prenom.data,
            date_naissance         = form.date_naissance.data,
            sexe                   = form.sexe.data,
            lien_chef_menage       = lien,
            est_chef_menage        = est_chef,
            situation_matrimoniale = form.situation_matrimoniale.data,
            niveau_instruction     = form.niveau_instruction.data,
            statut_scolarisation   = statut_scol,
            statut_activite        = statut_activite,
            sait_lire_ecrire       = form.sait_lire_ecrire.data,
            id_profession          = id_profession,
        )
        db.session.add(individu)
        db.session.commit()
        flash(f'{individu.prenom} {individu.nom} ajouté au ménage.', 'success')
        return redirect(url_for('enqueteur.fiche_menage', id_menage=id_menage))

    return render_template('enqueteur/nouveau_individu.html', form=form, menage=menage)


@enqueteur_bp.route('/menage/<int:id_menage>/passage/nouveau', methods=['GET', 'POST'])
@login_required
@enqueteur_required
def nouveau_passage(id_menage):
    menage = Menage.query.get_or_404(id_menage)
    zd     = menage.logement.ilot.zone_denombrement

    if current_user.role == 'ENQUETEUR' and zd.id_zd not in zd_autorisees(current_user.id_utilisateur):
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('enqueteur.dashboard'))

    form = PassageForm()
    from app.models.collecte import StatutPassage
    form.id_statut_passage.choices = [
        (s.id_statut_passage, s.libelle_statut)
        for s in StatutPassage.query.all()
    ]
    form.date_passage.data = form.date_passage.data or date.today()

    if form.validate_on_submit():
        n_passage = PassageCollecte.query.filter_by(id_menage=id_menage).count() + 1
        passage   = PassageCollecte(
            id_menage         = id_menage,
            id_utilisateur    = current_user.id_utilisateur,
            numero_passage    = n_passage,
            date_passage      = form.date_passage.data,
            heure_passage     = form.heure_passage.data,
            id_statut_passage = form.id_statut_passage.data,
            observations      = form.observations.data,
        )
        db.session.add(passage)
        db.session.commit()
        flash('Passage enregistré.', 'success')
        return redirect(url_for('enqueteur.fiche_menage', id_menage=id_menage))

    return render_template('enqueteur/nouveau_passage.html', form=form, menage=menage)
