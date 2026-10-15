"""
Django settings for the EcoVision backend.

All environment-specific values are read from backend/.env (see .env.example).
"""

import os
from pathlib import Path

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_str(name, default=""):
    return os.getenv(name, default).strip()


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def env_int(name, default):
    value = os.getenv(name, "").strip()
    return int(value) if value else default


def env_float(name, default):
    value = os.getenv(name, "").strip()
    return float(value) if value else default


# --- Core -------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off.")
    SECRET_KEY = "django-insecure-local-development-only"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "accounts",
    "catalog",
    "recognition",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Localization -----------------------------------------------------------

LANGUAGE_CODE = "ru"
TIME_ZONE = env_str("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# --- Static and media files -------------------------------------------------

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

MAX_UPLOAD_MB = env_int("MAX_UPLOAD_MB", 10)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# --- CORS -------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOW_HEADERS = (*default_headers, "x-client-id")

# --- Django REST Framework --------------------------------------------------

REST_FRAMEWORK = {
    # Accounts are optional: requests carry "Authorization: Token <key>" when the
    # user is logged in; anonymous devices are identified by the X-Client-Id header.
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "recognize": env_str("RECOGNIZE_RATE", "30/min"),
        "auth": env_str("AUTH_RATE", "10/min"),
    },
}

# --- Roboflow ---------------------------------------------------------------

ROBOFLOW_API_KEY = env_str("ROBOFLOW_API_KEY")
ROBOFLOW_API_URL = env_str("ROBOFLOW_API_URL", "https://detect.roboflow.com").rstrip("/")
ROBOFLOW_MODEL_ID = env_str("ROBOFLOW_MODEL_ID")
ROBOFLOW_MODEL_VERSION = env_str("ROBOFLOW_MODEL_VERSION")
# Roboflow shows model IDs as "project/version"; accept that form too.
if "/" in ROBOFLOW_MODEL_ID and not ROBOFLOW_MODEL_VERSION:
    ROBOFLOW_MODEL_ID, ROBOFLOW_MODEL_VERSION = (
        part.strip() for part in ROBOFLOW_MODEL_ID.rsplit("/", 1)
    )
ROBOFLOW_MODEL_TYPE = env_str("ROBOFLOW_MODEL_TYPE", "object-detection")
ROBOFLOW_TIMEOUT_SECONDS = env_float("ROBOFLOW_TIMEOUT_SECONDS", 15.0)
ROBOFLOW_MIN_CONFIDENCE = env_float("ROBOFLOW_MIN_CONFIDENCE", 0.40)
LOW_CONFIDENCE_THRESHOLD = env_float("LOW_CONFIDENCE_THRESHOLD", 0.60)

if ROBOFLOW_MODEL_TYPE not in ("object-detection", "classification"):
    raise ImproperlyConfigured(
        "ROBOFLOW_MODEL_TYPE must be 'object-detection' or 'classification'."
    )

# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        # Replaces Django's default handlers, which would print every line twice.
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "catalog": {"level": "INFO"},
        "recognition": {"level": "INFO"},
        # urllib3 logs full request URLs (including the Roboflow api_key query
        # parameter) at DEBUG level, so keep it quiet.
        "urllib3": {"level": "WARNING"},
    },
}
