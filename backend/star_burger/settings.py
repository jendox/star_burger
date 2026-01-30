import os

import dj_database_url
from environs import Env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Env()
env_path_candidates = [
    os.path.join(BASE_DIR, ".env"),
    os.path.join(os.path.dirname(BASE_DIR), ".env"),
]
for env_path in env_path_candidates:
    if os.path.exists(env_path):
        env.read_env(env_path)
        break
else:
    env.read_env()

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', '0.0.0.0'], delimiter=',')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[], delimiter=',')

# Proxy/HTTPS (nginx)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

INSTALLED_APPS = [
    'foodcartapp.apps.FoodcartappConfig',
    'restaurateur.apps.RestaurateurConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'phonenumber_field',
    'rest_framework',
    'geocache.apps.GeocacheConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
]

ROOT_URLCONF = 'star_burger.urls'

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates"),
        ],
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

WSGI_APPLICATION = 'star_burger.wsgi.application'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

DATABASES = {
    'default': dj_database_url.config(
        default=env.str('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    ),
}

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

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

INTERNAL_IPS = [
    '127.0.0.1'
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "assets"),
    os.path.join(BASE_DIR, "bundles"),
]

# Yandex
YANDEX_GEOCODER_API_KEY = env.str('YANDEX_GEOCODER_API_KEY')

# Rollbar
ROLLBAR = {
    'access_token': env.str('ROLLBAR_ACCESS_TOKEN', ''),
    'environment': env.str('ROLLBAR_ENV', 'development'),
    'code_version': '1.0',
    'root': BASE_DIR,
}
