"""
Django settings for agentic_django project.
"""

import os
import yaml
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load configuration from YAML file
config_path = BASE_DIR / 'config.yaml'
with open(config_path, 'r') as file:
    config_data = yaml.safe_load(file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config_data['app']['secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config_data['app']['debug']

ALLOWED_HOSTS = ['*'] if config_data['server']['allowed_hosts'] == '*' else config_data['server']['allowed_hosts'].split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_extensions',  # For HTTPS development server
    'authentication',
    'chat',
    'core',
    'mcpserver',  # Model Context Protocol integration
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add django-cors-headers middleware first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Commented out for API
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'authentication.middleware.MaintenanceModeMiddleware',
    'authentication.middleware.APIUsageStatsMiddleware',
    'authentication.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'agentic_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'agentic_django.wsgi.application'

# Database
if os.environ.get("IS_TESTING") == "1":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    class DisableMigrations:
        def __contains__(self, item):
            return True
        def __getitem__(self, item):
            return None
    MIGRATION_MODULES = DisableMigrations()
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config_data['database']['url'].split('/')[-1],
            'USER': config_data['database']['url'].split('//')[1].split(':')[0],
            'PASSWORD': config_data['database']['url'].split('//')[1].split(':')[1].split('@')[0],
            'HOST': config_data['database']['url'].split('@')[1].split(':')[0],
            'PORT': config_data['database']['url'].split('@')[1].split(':')[1].split('/')[0],
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password Hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS Configuration for production
SECURE_SSL_REDIRECT = not DEBUG  # Only redirect to HTTPS in production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Session and CSRF security for HTTPS
SESSION_COOKIE_SECURE = not DEBUG  # Only send session cookies over HTTPS in production
CSRF_COOKIE_SECURE = not DEBUG  # Only send CSRF cookies over HTTPS in production
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# Additional security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS Settings - Consolidated configuration
CORS_ALLOW_ALL_ORIGINS = True  # For development only
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "http://localhost:5173",
    "https://localhost:5173",
    "http://127.0.0.1:5173",
    "https://127.0.0.1:5173",
    "https://192.168.0.90:3000",  # Network address from terminal
    "http://192.168.0.90:3000",
]

# Additional CORS headers for proper API communication
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

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_CREDENTIALS = True

# Maintenance Mode
MAINTENANCE_MODE = False

# API Usage Stats
TRACK_API_USAGE = True

# Audit Logging
ENABLE_AUDIT_LOGGING = True

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CSRF settings for API
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "http://localhost:5173",
    "https://localhost:5173",
    "http://127.0.0.1:5173",
    "https://127.0.0.1:5173",
    "http://localhost:8000",
    "https://localhost:8000",
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000",
    "https://192.168.0.90:3000",  # Network address from terminal
    "http://192.168.0.90:3000",
    "https://192.168.0.90:8000",
    "http://192.168.0.90:8000",
]

# Disable CSRF for API endpoints - Updated for HTTPS support
# Note: These are set conditionally based on DEBUG mode above

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config_data['jwt']['token_expiry_minutes']),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': config_data['jwt']['algorithm'],
    'SIGNING_KEY': config_data['jwt']['secret_key'],
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS settings
# Remove duplicate CORS configuration - already defined above
# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
#     "https://localhost:3000",
#     "https://127.0.0.1:3000",
#     "https://localhost:5173",
#     "https://127.0.0.1:5173",
# ]

# CORS_ALLOW_HEADERS = [
#     'accept',
#     'accept-encoding',
#     'authorization',
#     'content-type',
#     'dnt',
#     'origin',
#     'user-agent',
#     'x-csrftoken',
#     'x-requested-with',
# ]

# Custom settings from config
COGNIVOX_CONFIG = config_data

# MongoDB settings (for external services)
MONGODB_URL = config_data['mongodb']['url']
MONGODB_DB_NAME = config_data['mongodb']['db_name']

# Ollama settings
OLLAMA_URL = config_data['additional']['ollama_url']

# Memory service settings
MEMORY_SERVICE_URL = os.getenv('MEMORY_SERVICE_URL', 'http://localhost:8002')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config_data['email']['host']
EMAIL_PORT = config_data['email']['port']
EMAIL_USE_TLS = config_data['email']['use_tls']
EMAIL_HOST_USER = config_data['email']['user']
EMAIL_HOST_PASSWORD = config_data['email']['password']

# Custom user model
AUTH_USER_MODEL = 'authentication.User'
