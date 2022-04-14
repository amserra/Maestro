from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'default_unsecure_secret_key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

TEST = (os.getenv('TEST', 'False') == 'True')

if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
else:
    ALLOWED_HOSTS = ['maestro-web.inesc-id.pt']

ADMINS = [('Alexandre', os.getenv('ALEX_ADMIN_EMAIL'))]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
    'tailwind',
    'theme',
    'widget_tweaks',
    'imagekit',
    'taggit',
    'django_filters',
    'django_celery_results',
    'debug_toolbar',
    'common',
    'account',
    'organization',
    'context',
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
]

if not TEST and not DEBUG:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')



if not TEST and not DEBUG:
    # Compression and caching with whitenoise. In development will still use Django default static file handling
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'maestro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'maestro.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', ''),
        'USER': os.getenv('DATABASE_USER', ''),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', ''),
        'PORT': os.getenv('DATABASE_PORT', ''),
        'TEST': {
            'NAME': 'maestro_test_db',
            'TEMPLATE': os.getenv('DATABASE_NAME', '')
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'


MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TAILWIND_APP_NAME = 'theme'

INTERNAL_IPS = [
    "127.0.0.1",
]

# TODO: change when we have domain
ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'account.User'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' if DEBUG is False else 'django.core.mail.backends.console.EmailBackend'
# EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'email_logs')
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Allows to specify different default widgets
# https://timonweb.com/django/overriding-field-widgets-in-django-doesnt-work-template-not-found-the-solution/
# https://docs.djangoproject.com/en/4.0/ref/forms/renderers/#django.forms.renderers.TemplatesSetting
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

LOGGED_IN_HOME = '/'
LOGIN_URL = 'login'

if not DEBUG:
    NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'

# Celery configurations
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/London'
CELERY_RESULT_BACKEND = 'django-db'

# SerpAPI key
SERPAPI_KEY = os.getenv('SERPAPI_KEY', '')

# Bing API key
BING_SUBSCRIPTION_KEY = os.getenv('BING_SUBSCRIPTION_KEY', '')

# Twitter API key
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')

# Context's data directory
CONTEXTS_DATA_DIR = os.path.join(BASE_DIR, 'contexts_data')

LOGS_PATH = os.path.join(BASE_DIR, 'logs')

MAPBOX_KEY = os.getenv('MAPBOX_KEY', '')

ARCGIS_KEY = os.getenv('ARCGIS_KEY', '')
