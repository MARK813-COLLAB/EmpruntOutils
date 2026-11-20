import os
from .base import *

DEBUG = False

allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]

# Database can be configured via environment or default to PostgreSQL / SQLite
db_engine = os.environ.get("DB_ENGINE", "django.db.backends.sqlite3")
db_name = os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3"))
db_user = os.environ.get("DB_USER", "")
db_password = os.environ.get("DB_PASSWORD", "")
db_host = os.environ.get("DB_HOST", "")
db_port = os.environ.get("DB_PORT", "")

DATABASES = {
    "default": {
        "ENGINE": db_engine,
        "NAME": db_name,
        "USER": db_user,
        "PASSWORD": db_password,
        "HOST": db_host,
        "PORT": db_port,
    }
}

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ("true", "1")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@empruntoutils.fr")
