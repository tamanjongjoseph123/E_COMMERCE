"""
Django settings for e_commerce project (Production-ready with VPS storage).

DEBUG can be toggled here.
Media and static files are stored locally on the VPS.
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ------------------------
# Paths
# ------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "staticfiles"
MEDIA_DIR = BASE_DIR / "media"

# ------------------------
# Security
# ------------------------
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-production-secret-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "firstchoiceserver.faithhubs.org", "infinitemarket.cloud", "www.infinitemarket.cloud", "infinitymarket01.com"]

# ------------------------
# CSRF Settings
# ------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://infinitemarket.cloud",
    "https://www.infinitemarket.cloud",
    "https://infinitymarket01.com",
    "https://www.infinitymarket01.com",
]

# ------------------------
# Installed apps
# ------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "api",
]

# ------------------------
# Middleware
# ------------------------
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

ROOT_URLCONF = "e_commerce.urls"

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

WSGI_APPLICATION = "e_commerce.wsgi.application"

# ------------------------
# Database (environment variables)
# ------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('DB_NAME', 'infinitemarket_db'),
        "USER": os.getenv('DB_USER', 'infinitemarket_user'),
        "PASSWORD": os.getenv('DB_PASSWORD', 'infinitemarket_password'),
        "HOST": os.getenv('DB_HOST', 'localhost'),
        "PORT": os.getenv('DB_PORT', '5432'),
    }
}

# Fapshi API Credentials
FAPSHI_PAYMENT_API_KEY = os.getenv('FAPSHI_PAYMENT_API_KEY')
FAPSHI_PAYMENT_API_USER = os.getenv('FAPSHI_PAYMENT_API_USER')
FAPSHI_PAYOUT_API_KEY = os.getenv('FAPSHI_PAYOUT_API_KEY')
FAPSHI_PAYOUT_API_USER = os.getenv('FAPSHI_PAYOUT_API_USER')

# ------------------------
# Password validation
# ------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------
# Internationalization
# ------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------
# Static and media files
# ------------------------
STATIC_URL = "/static/"
STATIC_ROOT = STATIC_DIR

MEDIA_URL = "/media/"
MEDIA_ROOT = MEDIA_DIR

# ------------------------
# Custom User Model
# ------------------------
AUTH_USER_MODEL = "api.User"

# ------------------------
# REST Framework
# ------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ------------------------
# JWT Settings
# ------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ------------------------
# CORS Settings
# ------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://infinitemarket.cloud",
    "https://infinitemarket.cloud",
    "http://www.infinitemarket.cloud",
    "https://www.infinitemarket.cloud",
    "http://infinitymarket01.com",
    "https://infinitymarket01.com",
    "http://www.infinitymarket01.com",
    "https://www.infinitymarket01.com",
]

# Always allow localhost origins for development
if DEBUG:
    CORS_ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ])

# Allow all origins if DEBUG is True
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# ------------------------
# Logging
# ------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "debug.log"),
            "formatter": "verbose",
        },
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
    "loggers": {
        "api": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
        "api.payment_service": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
}

# ------------------------
# File Upload Settings
# ------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB in bytes
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB in bytes

# ------------------------
# Default primary key field type
# ------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
