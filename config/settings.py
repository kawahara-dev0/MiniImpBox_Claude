"""
Django settings for Mini Improvement Box v1.

Basic design: docs/design/basic-design-v1.md (Approved 2026-05-11)
ADRs: ADR-001 through ADR-006 (All Accepted 2026-05-11)

BD-01 (Decided 2026-05-11): SESSION_COOKIE_SECURE = False is accepted for
the localhost-only Docker Compose trial. Change to True if any non-localhost
network access is required.

BD-02 (Pending): ip_address logging in AdminLoginLog — confirm before trial start.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core ---

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# --- Applications ---

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'proposals',
    'accounts',
]
# django.contrib.admin is intentionally omitted in v1 (basic design Section 2, ADR-002)

# --- Middleware ---

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # immediately after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- Database (ADR-003, ADR-004) ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ['POSTGRES_DB'],
        'USER':     os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST':     os.environ.get('POSTGRES_HOST', 'db'),
        'PORT':     os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# --- Authentication (ADR-001, ADR-002) ---

AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']

LOGIN_URL           = '/admin-portal/login/'
LOGIN_REDIRECT_URL  = '/admin-portal/'
LOGOUT_REDIRECT_URL = '/admin-portal/login/'

AUTH_PASSWORD_VALIDATORS = []  # Custom EmailBackend; Django built-in validators not used

# --- Session (ADR-001, BD-01) ---

SESSION_ENGINE               = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE           = 28800   # 8 hours absolute maximum
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # also expires when browser closes
SESSION_COOKIE_HTTPONLY      = True    # prevent JS access to session cookie
SESSION_COOKIE_SAMESITE      = 'Lax'  # CSRF mitigation for same-site requests
SESSION_COOKIE_SECURE        = False   # BD-01 decided: localhost-only trial; change to True if network access required
SESSION_COOKIE_NAME          = 'miniimpbox_sessionid'

# --- Static files (basic design Section 16, ADR-003) ---

STATIC_URL  = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Note: STATICFILES_STORAGE is deprecated in Django 4.2+ in favour of STORAGES.
# It remains functional in Django 5.2. No migration required for v1 trial scope.

# --- Localisation ---

LANGUAGE_CODE = 'ja'          # Japanese locale; change to 'en-us' before trial if preferred
TIME_ZONE     = 'Asia/Tokyo'
USE_I18N      = True
USE_TZ        = True

# --- Misc ---

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Logging ---
# Sensitive data (proposal body, submitter fields, passwords, session tokens)
# must NEVER be logged (ADR-005, HD-19).

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
