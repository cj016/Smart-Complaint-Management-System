import os
from datetime import timedelta


class BaseConfig:
    JWT_TOKEN_LOCATION = ["headers"]     # never cookies, so no ambient credential
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000").split(",")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    USE_TLS = os.getenv("USE_TLS", "false").lower() == "true"  # local HTTPS demo
    PII_ENCRYPTION_KEY = os.getenv("PII_ENCRYPTION_KEY")
    AUTO_VERIFY = os.getenv("AUTO_VERIFY", "false").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me-0123456789")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me-0123456789")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=3600)  # SAD 4.3: expiresIn 3600
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///scms_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    # Business rules from the SRS
    MAX_PHOTOS = 3                       # SCMS-F-013
    MAX_PHOTO_BYTES = 5 * 1024 * 1024    # SCMS-F-013
    MAX_FAILED_LOGINS = 5                # SCMS-F-004
    LOCKOUT_MINUTES = 15                 # SCMS-F-004
    # SCMS-F-034: hours a complaint may stay open before it is auto-escalated
    SLA_HOURS = {"Low": 120, "Medium": 72, "High": 48, "Critical": 24}


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
