from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
import os
from app.models.collecte import Utilisateur
from app.forms.auth import LoginForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/sw.js')
def service_worker():
    """Sert le service worker depuis la racine (requis par les PWA)."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    response = send_from_directory(static_dir, 'sw.js')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Content-Type'] = 'application/javascript'
    return response


@auth_bp.route('/manifest.json')
def manifest():
    """Sert le manifest depuis la racine."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_dir, 'manifest.json')


@auth_bp.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    form = LoginForm()
    if form.validate_on_submit():
        user = Utilisateur.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            if not user.actif:
                flash('Votre compte est désactivé. Contactez l\'administrateur.', 'danger')
                return render_template('auth/login.html', form=form)
            login_user(user)
            return _redirect_by_role(user.role)
        flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role(role):
    if role == 'ADMINISTRATEUR':
        return redirect(url_for('admin.dashboard'))
    elif role == 'SUPERVISEUR':
        return redirect(url_for('admin.supervision'))
    else:
        return redirect(url_for('enqueteur.dashboard'))
