import os
from datetime import timedelta


class BaseConfig:
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
