from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.collecte import Utilisateur, AffectationZD, PassageCollecte, StatutPassage
from app.models.habitat import Menage, StatutMenage, Logement, TypeLogement, MateriauMur, MateriauToit, SourceEau, TypeToilette
from app.models.territoire import ZoneDenombrement, Ilot, Quartier, LocaliteAdministrative, TypeLocalite
from app.models.individu import Individu, Profession
from app.forms.auth import UserForm
from app.forms.menage import AffectationForm
from app.choices import TRANSITIONS

admin_bp = Blueprint('admin', __name__)


def admin_or_superviseur_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('ADMINISTRATEUR', 'SUPERVISEUR'):
            flash('Accès réservé aux administrateurs et superviseurs.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ADMINISTRATEUR':
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_or_superviseur_required
def dashboard():
    statut_en_cours = StatutMenage.query.filter_by(code_statut='EN_COURS').first()
    statut_soumis   = StatutMenage.query.filter_by(code_statut='SOUMIS').first()
    statut_valide   = StatutMenage.query.filter_by(code_statut='VALIDE').first()

    total_menages   = Menage.query.count()
    fiches_validees = Menage.query.filter_by(id_statut_menage=statut_valide.id_statut_menage).count() if statut_valide else 0
    en_attente      = Menage.query.filter_by(id_statut_menage=statut_soumis.id_statut_menage).count() if statut_soumis else 0
    enqueteurs_actifs = Utilisateur.query.filter_by(role='ENQUETEUR', actif=True).count()

    zds = ZoneDenombrement.query.all()
    zd_labels = []
    zd_data   = []
    for zd in zds:
        ilot_ids = [i.id_ilot for i in zd.ilots]
        if not ilot_ids:
            continue
        from app.models.habitat import Logement
        log_ids = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()]
        total   = Menage.query.filter(Menage.id_logement.in_(log_ids)).count()
        valides = Menage.query.filter(
            Menage.id_logement.in_(log_ids),
            Menage.id_statut_menage == (statut_valide.id_statut_menage if statut_valide else -1)
        ).count()
        if total > 0:
            zd_labels.append(zd.code_zd)
            zd_data.append(round(valides / total * 100, 1))

    activite_recente = db.session.query(Utilisateur, Menage)\
        .join(AffectationZD, AffectationZD.id_utilisateur == Utilisateur.id_utilisateur)\
        .join(ZoneDenombrement, ZoneDenombrement.id_zd == AffectationZD.id_zd)\
        .filter(Utilisateur.role == 'ENQUETEUR')\
        .limit(10).all()

    return render_template('admin/dashboard.html',
        total_menages=total_menages,
        fiches_validees=fiches_validees,
        en_attente=en_attente,
        enqueteurs_actifs=enqueteurs_actifs,
        zd_labels=zd_labels,
        zd_data=zd_data,
        activite_recente=activite_recente,
    )


@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    form = UserForm()
    if form.validate_on_submit():
        if Utilisateur.query.filter_by(email=form.email.data.lower()).first():
            flash('Cet email est déjà utilisé.', 'danger')
        else:
            u = Utilisateur(
                nom=form.nom.data,
                prenom=form.prenom.data,
                email=form.email.data.lower(),
                telephone=form.telephone.data,
                role=form.role.data,
                actif=form.actif.data,
            )
            u.set_password(form.password.data)
            db.session.add(u)
            db.session.commit()
            flash('Utilisateur créé avec succès.', 'success')
            return redirect(url_for('admin.users'))

    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom).all()
    return render_template('admin/users.html', form=form, utilisateurs=utilisateurs)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    u = Utilisateur.query.get_or_404(user_id)
    u.actif = not u.actif
    db.session.commit()
    return jsonify({'actif': u.actif})


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    u = Utilisateur.query.get_or_404(user_id)
    nom       = request.form.get('nom', '').strip()
    prenom    = request.form.get('prenom', '').strip()
    email     = request.form.get('email', '').strip().lower()
    telephone = request.form.get('telephone', '').strip()
    role      = request.form.get('role', '').strip()
    password  = request.form.get('password', '').strip()

    if not nom or not prenom or not email or not role:
        flash('Tous les champs obligatoires doivent être remplis.', 'danger')
        return redirect(url_for('admin.users'))

    # Vérifier unicité email (sauf si c'est le même utilisateur)
    existing = Utilisateur.query.filter_by(email=email).first()
    if existing and existing.id_utilisateur != user_id:
        flash('Cet email est déjà utilisé par un autre compte.', 'danger')
        return redirect(url_for('admin.users'))

    # Empêcher un admin de se rétrograder lui-même
    if u.id_utilisateur == current_user.id_utilisateur and role != 'ADMINISTRATEUR':
        flash('Vous ne pouvez pas changer votre propre rôle.', 'danger')
        return redirect(url_for('admin.users'))

    u.nom       = nom
    u.prenom    = prenom
    u.email     = email
    u.telephone = telephone or None
    u.role      = role
    if password:
        u.set_password(password)

    db.session.commit()
    flash(f'Utilisateur {u.prenom} {u.nom} modifié avec succès.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    u = Utilisateur.query.get_or_404(user_id)

    # Empêcher l'auto-suppression
    if u.id_utilisateur == current_user.id_utilisateur:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.users'))

    # Vérifier si l'utilisateur a des passages enregistrés
    if u.passages:
        flash(
            f'{u.prenom} {u.nom} a {len(u.passages)} passage(s) enregistré(s). '
            'Désactivez le compte plutôt que de le supprimer.',
            'warning'
        )
        return redirect(url_for('admin.users'))

    # Supprimer les affectations puis l'utilisateur
    AffectationZD.query.filter_by(id_utilisateur=user_id).delete()
    db.session.delete(u)
    db.session.commit()
    flash(f'Utilisateur {u.prenom} {u.nom} supprimé.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/affectations', methods=['GET', 'POST'])
@login_required
@admin_required
def affectations():
    form = AffectationForm()
    form.id_utilisateur.choices = [
        (u.id_utilisateur, f'{u.nom} {u.prenom}')
        for u in Utilisateur.query.filter_by(role='ENQUETEUR', actif=True).order_by(Utilisateur.nom).all()
    ]
    form.id_zd.choices = [
        (z.id_zd, z.code_zd)
        for z in ZoneDenombrement.query.order_by(ZoneDenombrement.code_zd).all()
    ]

    if form.validate_on_submit():
        aff = AffectationZD(
            id_utilisateur=form.id_utilisateur.data,
            id_zd=form.id_zd.data,
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            actif=True,
        )
        db.session.add(aff)
        db.session.commit()
        flash('Affectation enregistrée.', 'success')
        return redirect(url_for('admin.affectations'))

    enqueteurs = Utilisateur.query.filter_by(role='ENQUETEUR').order_by(Utilisateur.nom).all()
    result = []
    for enq in enqueteurs:
        affs = AffectationZD.query.filter_by(id_utilisateur=enq.id_utilisateur, actif=True).all()
        for a in affs:
            ilot_ids = [i.id_ilot for i in a.zone_denombrement.ilots]
            log_ids  = [l.id_logement for l in Logement.query.filter(Logement.id_ilot.in_(ilot_ids)).all()] if ilot_ids else []
            total    = Menage.query.filter(Menage.id_logement.in_(log_ids)).count() if log_ids else 0
            st_val   = StatutMenage.query.filter_by(code_statut='VALIDE').first()
            valides  = Menage.query.filter(
                Menage.id_logement.in_(log_ids),
                Menage.id_statut_menage == st_val.id_statut_menage
            ).count() if (log_ids and st_val) else 0
            result.append({'enqueteur': enq, 'affectation': a, 'total': total, 'valides': valides})

    return render_template('admin/affectations.html', form=form, result=result)


@admin_bp.route('/supervision')
@login_required
@admin_or_superviseur_required
def supervision():
    statut_soumis = StatutMenage.query.filter_by(code_statut='SOUMIS').first()
    fiches = []
    if statut_soumis:
        menages_soumis = Menage.query.filter_by(id_statut_menage=statut_soumis.id_statut_menage).all()
        for m in menages_soumis:
            ilot = m.logement.ilot
            zd   = ilot.zone_denombrement
            dernier_passage = None
            if m.passages:
                dernier_passage = sorted(m.passages, key=lambda p: p.date_passage, reverse=True)[0]
            fiches.append({
                'menage': m,
                'ilot': ilot,
                'zd': zd,
                'nb_membres': len(m.individus),
                'passage': dernier_passage,
            })
    return render_template('admin/supervision.html', fiches=fiches)


@admin_bp.route('/supervision/<int:menage_id>/valider', methods=['POST'])
@login_required
@admin_or_superviseur_required
def valider_menage(menage_id):
    menage = Menage.query.get_or_404(menage_id)
    statut_soumis = StatutMenage.query.filter_by(code_statut='SOUMIS').first()
    statut_valide = StatutMenage.query.filter_by(code_statut='VALIDE').first()

    if not statut_soumis or menage.id_statut_menage != statut_soumis.id_statut_menage:
        flash('Ce ménage ne peut pas être validé dans son état actuel.', 'danger')
        return redirect(url_for('admin.supervision'))

    if 'VALIDE' not in TRANSITIONS.get('SOUMIS', []):
        flash('Transition non autorisée.', 'danger')
        return redirect(url_for('admin.supervision'))

    menage.id_statut_menage = statut_valide.id_statut_menage
    db.session.commit()
    flash(f'Ménage {menage.code_menage} validé.', 'success')
    return redirect(url_for('admin.supervision'))


@admin_bp.route('/supervision/<int:menage_id>/renvoyer', methods=['POST'])
@login_required
@admin_or_superviseur_required
def renvoyer_menage(menage_id):
    menage = Menage.query.get_or_404(menage_id)
    statut_soumis  = StatutMenage.query.filter_by(code_statut='SOUMIS').first()
    statut_renvoye = StatutMenage.query.filter_by(code_statut='RENVOYE').first()

    if not statut_soumis or menage.id_statut_menage != statut_soumis.id_statut_menage:
        flash('Ce ménage ne peut pas être renvoyé dans son état actuel.', 'danger')
        return redirect(url_for('admin.supervision'))

    menage.id_statut_menage = statut_renvoye.id_statut_menage
    db.session.commit()
    flash(f'Ménage {menage.code_menage} renvoyé en correction.', 'warning')
    return redirect(url_for('admin.supervision'))


@admin_bp.route('/territoire')
@login_required
@admin_required
def territoire():
    localites = LocaliteAdministrative.query.order_by(LocaliteAdministrative.nom_localite).all()
    quartiers = Quartier.query.order_by(Quartier.nom_quartier).all()
    zones     = ZoneDenombrement.query.order_by(ZoneDenombrement.code_zd).all()
    ilots     = Ilot.query.order_by(Ilot.code_ilot).all()
    types     = TypeLocalite.query.all()
    return render_template('admin/territoire.html',
        localites=localites, quartiers=quartiers,
        zones=zones, ilots=ilots, types=types
    )


@admin_bp.route('/territoire/localite/add', methods=['POST'])
@login_required
@admin_required
def add_localite():
    nom   = request.form.get('nom_localite', '').strip()
    code  = request.form.get('code_localite', '').strip()
    tid   = request.form.get('id_type_localite', type=int)
    pid   = request.form.get('id_parent', type=int) or None

    if not nom or not code or not tid:
        flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        return redirect(url_for('admin.territoire'))

    if LocaliteAdministrative.query.filter_by(code_localite=code).first():
        flash('Ce code localité est déjà utilisé.', 'danger')
        return redirect(url_for('admin.territoire'))

    loc = LocaliteAdministrative(nom_localite=nom, code_localite=code,
                                  id_type_localite=tid, id_parent=pid)
    db.session.add(loc)
    db.session.commit()
    flash('Localité ajoutée.', 'success')
    return redirect(url_for('admin.territoire'))


@admin_bp.route('/territoire/quartier/add', methods=['POST'])
@login_required
@admin_required
def add_quartier():
    nom  = request.form.get('nom_quartier', '').strip()
    code = request.form.get('code_quartier', '').strip()
    lid  = request.form.get('id_localite', type=int)
    obs  = request.form.get('observations', '').strip() or None

    if not nom or not code or not lid:
        flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        return redirect(url_for('admin.territoire'))

    if Quartier.query.filter_by(code_quartier=code).first():
        flash('Ce code quartier est déjà utilisé.', 'danger')
        return redirect(url_for('admin.territoire'))

    q = Quartier(nom_quartier=nom, code_quartier=code, id_localite=lid, observations=obs)
    db.session.add(q)
    db.session.commit()
    flash('Quartier ajouté.', 'success')
    return redirect(url_for('admin.territoire'))


@admin_bp.route('/territoire/zd/add', methods=['POST'])
@login_required
@admin_required
def add_zd():
    code = request.form.get('code_zd', '').strip()
    lid  = request.form.get('id_localite', type=int)
    qid  = request.form.get('id_quartier', type=int) or None

    if not code or not lid:
        flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        return redirect(url_for('admin.territoire'))

    if ZoneDenombrement.query.filter_by(code_zd=code).first():
        flash('Ce code ZD est déjà utilisé.', 'danger')
        return redirect(url_for('admin.territoire'))

    zd = ZoneDenombrement(code_zd=code, id_localite=lid, id_quartier=qid)
    db.session.add(zd)
    db.session.commit()
    flash('Zone de dénombrement ajoutée.', 'success')
    return redirect(url_for('admin.territoire'))


@admin_bp.route('/territoire/ilot/add', methods=['POST'])
@login_required
@admin_required
def add_ilot():
    numero = request.form.get('numero_ilot', type=int)
    code   = request.form.get('code_ilot', '').strip()
    zd_id  = request.form.get('id_zd', type=int)

    if not numero or not code or not zd_id:
        flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        return redirect(url_for('admin.territoire'))

    if Ilot.query.filter_by(code_ilot=code).first():
        flash('Ce code îlot est déjà utilisé.', 'danger')
        return redirect(url_for('admin.territoire'))

    ilot = Ilot(numero_ilot=numero, code_ilot=code, id_zd=zd_id)
    db.session.add(ilot)
    db.session.commit()
    flash('Îlot ajouté.', 'success')
    return redirect(url_for('admin.territoire'))


# ─── VUE DES TABLES DE DONNÉES ────────────────────────────────────────────────

@admin_bp.route('/donnees')
@login_required
@admin_or_superviseur_required
def donnees():
    table  = request.args.get('table', 'menages')
    q      = request.args.get('q', '').strip()
    page   = request.args.get('page', 1, type=int)
    statut = request.args.get('statut', '')
    zd_id  = request.args.get('zd_id', '', type=str)
    per_page = 20

    data = {}

    if table == 'menages':
        query = Menage.query
        if q:
            query = query.filter(Menage.code_menage.ilike(f'%{q}%'))
        if statut:
            st = StatutMenage.query.filter_by(code_statut=statut).first()
            if st:
                query = query.filter_by(id_statut_menage=st.id_statut_menage)
        data['pagination'] = query.order_by(Menage.date_creation.desc()).paginate(page=page, per_page=per_page, error_out=False)
        data['statuts'] = StatutMenage.query.all()

    elif table == 'individus':
        query = Individu.query
        if q:
            query = query.filter(
                db.or_(
                    Individu.nom.ilike(f'%{q}%'),
                    Individu.prenom.ilike(f'%{q}%')
                )
            )
        if statut:  # statut = statut_activite ici
            query = query.filter_by(statut_activite=statut)
        data['pagination'] = query.order_by(Individu.id_individu.desc()).paginate(page=page, per_page=per_page, error_out=False)

    elif table == 'logements':
        query = Logement.query
        if q:
            query = query.filter(Logement.code_logement.ilike(f'%{q}%'))
        data['pagination'] = query.order_by(Logement.id_logement.desc()).paginate(page=page, per_page=per_page, error_out=False)

    elif table == 'passages':
        query = PassageCollecte.query
        if q:
            query = query.join(Menage).filter(Menage.code_menage.ilike(f'%{q}%'))
        if statut:
            sp = StatutPassage.query.filter_by(code_statut=statut).first()
            if sp:
                query = query.filter_by(id_statut_passage=sp.id_statut_passage)
        data['pagination'] = query.order_by(PassageCollecte.date_passage.desc()).paginate(page=page, per_page=per_page, error_out=False)
        data['statuts_passage'] = StatutPassage.query.all()

    elif table == 'zones':
        query = ZoneDenombrement.query
        if q:
            query = query.filter(ZoneDenombrement.code_zd.ilike(f'%{q}%'))
        data['pagination'] = query.order_by(ZoneDenombrement.code_zd).paginate(page=page, per_page=per_page, error_out=False)

    elif table == 'utilisateurs':
        query = Utilisateur.query
        if q:
            query = query.filter(
                db.or_(
                    Utilisateur.nom.ilike(f'%{q}%'),
                    Utilisateur.email.ilike(f'%{q}%')
                )
            )
        if statut:
            query = query.filter_by(role=statut)
        data['pagination'] = query.order_by(Utilisateur.nom).paginate(page=page, per_page=per_page, error_out=False)

    # Compteurs pour les onglets
    data['counts'] = {
        'menages':      Menage.query.count(),
        'individus':    Individu.query.count(),
        'logements':    Logement.query.count(),
        'passages':     PassageCollecte.query.count(),
        'zones':        ZoneDenombrement.query.count(),
        'utilisateurs': Utilisateur.query.count(),
    }

    return render_template('admin/donnees.html',
        table=table, q=q, statut=statut, zd_id=zd_id,
        **data
    )
