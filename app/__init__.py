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
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from . import models  # noqa: F401  (registers tables with SQLAlchemy)

    register_blueprints(app)
    from .citizen_actions import bp as citizen_actions_bp
    app.register_blueprint(citizen_actions_bp)
    register_error_handlers(app, jwt)

    @app.after_request
    def security_headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "frame-ancestors 'none'")
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        return resp

    if app.config.get("FORCE_HTTPS"):
        from flask_talisman import Talisman
        from werkzeug.middleware.proxy_fix import ProxyFix

        # trust the reverse proxy's X-Forwarded-Proto so Flask knows the request was HTTPS
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            strict_transport_security_include_subdomains=True,
            content_security_policy=None,  # CSP is already set in security_headers (SR003)
            frame_options=None,
            referrer_policy=None,
        )

    return app


def register_blueprints(app):
    from .audit.routes import bp as audit_bp
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
    app.register_blueprint(audit_bp, url_prefix="/api/v1/audit")
    app.register_blueprint(notifications_bp, url_prefix="/api/v1/notifications")
    app.register_blueprint(reporting_bp, url_prefix="/api/v1/reports")
