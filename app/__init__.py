from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import territoire, habitat, individu, collecte  # noqa

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.enqueteur import enqueteur_bp
    from app.routes.stats import stats_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(enqueteur_bp, url_prefix='/enqueteur')
    app.register_blueprint(stats_bp, url_prefix='/stats')

    from seeds.seed import register_seed_command
    register_seed_command(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.collecte import Utilisateur
        return Utilisateur.query.get(int(user_id))

    return app
