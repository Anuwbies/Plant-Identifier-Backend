from pathlib import Path
import os
from dotenv import load_dotenv

# --- Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Load environment from .env at project root (next to manage.py)
load_dotenv(BASE_DIR / ".env")

# --- Core
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-qcow&9(oxjjf#hj47%fo9gb%+ch-v!!@o%(#wp*yb=q4pomupz')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes')

_default_hosts = [
    'localhost', '127.0.0.1',
    '10.0.2.2',          # Android emulator -> host loopback
    '192.168.100.4',
    '192.168.100.12',
    '172.20.10.2',
]
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', ','.join(_default_hosts)).split(',') if h.strip()]

# --- Apps
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'plant_identifier',
    'rest_framework',
]

# --- Middleware (CORS must be near the top, before CommonMiddleware)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',  # keep
    'django.middleware.csrf.CsrfViewMiddleware',  # keep CSRF enabled
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'plant.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'plant.wsgi.application'

# --- Database (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- I18N / TZ
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static / Media
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================
# CORS / CSRF for frontend
# =========================

# Your Vite origins (adjust/add as needed)
_env_cors = os.getenv('CORS_ORIGINS')
if _env_cors:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _env_cors.split(',') if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://10.0.2.2:5173',
        'http://192.168.100.4:5173',
        'http://192.168.100.12:5173',
        'http://172.20.10.2:5173',
    ]

# ✅ Credentials mode requires this to be True
CORS_ALLOW_CREDENTIALS = True

# Mirror CSRF trusted origins to the same list (dev convenience)
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS[:]

# Headers your frontend will send
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Methods
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']

# Cookies flags for dev
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# --- DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}
