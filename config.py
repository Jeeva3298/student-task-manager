import os

from dotenv import load_dotenv

load_dotenv()

_TRUE = ("1", "true", "yes")
_DEFAULT_SECRET = "dev-secret-change-in-production"


def _bool_env(name, default="false"):
    return os.getenv(name, default).lower() in _TRUE


class Config:
    DEBUG = _bool_env("FLASK_DEBUG", "false")
    SECRET_KEY = os.getenv("SECRET_KEY") or (_DEFAULT_SECRET if DEBUG else None)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "student_task_manager")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_SSL = _bool_env("DB_SSL", "false")
    DB_SSL_CA = os.getenv("DB_SSL_CA") or None
    INIT_CREATE_DATABASE = _bool_env("INIT_CREATE_DATABASE", "false")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("PORT", os.getenv("APP_PORT", "5000")))
    TRUST_PROXY = _bool_env("TRUST_PROXY", "false")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", "false")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https" if SESSION_COOKIE_SECURE else "http")


def validate_runtime_config():
    if not Config.SECRET_KEY or (
        Config.SECRET_KEY == _DEFAULT_SECRET and not Config.DEBUG
    ):
        raise SystemExit(
            "SECRET_KEY must be set to a strong unique value. "
            "Use the same value on every EC2 instance."
        )
    if not Config.DEBUG and Config.DB_HOST in ("localhost", "127.0.0.1"):
        raise SystemExit(
            "DB_HOST is localhost. Set DB_HOST to your RDS endpoint before deploying."
        )
