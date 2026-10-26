import os

from flask import Flask

from .config import config_by_name
from .errors import register_error_handlers
from .extensions import cors, db, jwt, migrate


def create_app(config_name=None):
    config_name = config_name or os.getenv("APP_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    from . import models  # noqa: F401  (registers tables with SQLAlchemy)

    register_blueprints(app)
    register_error_handlers(app, jwt)
    return app


def register_blueprints(app):
    from .admin.routes import bp as admin_bp
    from .auth.routes import bp as auth_bp
    from .complaints.routes import bp as complaints_bp
    from .health import bp as health_bp
    from .notifications.routes import bp as notifications_bp
    from .reporting.routes import bp as reporting_bp
    from .tracking.routes import bp as tracking_bp
    from .web.routes import bp as web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(complaints_bp, url_prefix="/api/v1/complaints")
    app.register_blueprint(tracking_bp, url_prefix="/api/v1/tracking")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(notifications_bp, url_prefix="/api/v1/notifications")
    app.register_blueprint(reporting_bp, url_prefix="/api/v1/reports")
