from pathlib import Path
import os
from datetime import timedelta
import os
from dotenv import load_dotenv
import dj_database_url 

load_dotenv() # This loads the variables from .env



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^pu^2d0rud-1_y+_bab)mm+d!nw$u9)k0z1w!!ml(s18$pd#(8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = []

allowed_host_addresses = os.environ.get("DJANGO_ALLOWED_HOSTS",None)

if allowed_host_addresses is not None:
    ALLOWED_HOSTS += [i for i in allowed_host_addresses.split(",")]

if DEBUG:
    ALLOWED_HOSTS+=['*']

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    'https://*',
    'http://*',
    'https://z9trades-backend-production.up.railway.app'
]

csrf_origins_env = os.environ.get("CSRF_TRUSTED_ORIGINS", None)
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS += [origin.strip() for origin in csrf_origins_env.split(",") if origin.strip()]






# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3ed party apps
    'drf_spectacular',
    'corsheaders',


    # custom apps
    'users',
    'orders',
    'wallet',
    'payments',
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Data App Api DOcs',
    'DESCRIPTION': 'A full API Documentation of the Data App',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False, # Set to True if you want to serve the schema at /schema/
    # ... other Spectacular settings
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTH_USER_MODEL = "users.User"

CORS_ALLOW_ALL_ORIGINS = True



MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
     'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if not DEBUG:
    DATABASES = {
     'default':  dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
        )
    }
        


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



STATIC_URL = 'static/'

# This production code might break development mode, so we check whether we're in DEBUG mode
if not DEBUG:
    # Tell Django to copy static assets into a path called `staticfiles` (this is specific to Render)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    # Enable the WhiteNoise storage backend, which compresses static files to reduce disk use
    # and renames the files with unique names for each version to support long-term caching
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STATIC_ROOT= os.path.join(BASE_DIR,'staticfiles/')
if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]



EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"


# for production
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = "your_email@gmail.com"
# EMAIL_HOST_PASSWORD = "your_app_password"



MONNIFY_BASE_URL=os.getenv("MONNIFY_BASE_URL")
MONNIFY_API_KEY=os.getenv("MONNIFY_API_KEY")
MONNIFY_API_SECRET=os.getenv("MONNIFY_API_SECRET")
MONNIFY_CONTRACT_CODE=os.getenv("MONNIFY_CONTRACT_CODE")
MONNIFY_WEBHOOK_SECRET=os.getenv("MONNIFY_WEBHOOK_SECRET")


VTPASS_BASE_URL = ""
VTPASS_USERNAME = ""
VTPASS_PASSWORD = ""
VTPASS_API_KEY = os.getenv("VTPASS_API_KEY") or ""
VTPASS_API_SECRET = os.getenv("VTPASS_API_SECRET") or ""
VTPASS_API_PUBLIC_KEY = os.getenv("VTPASS_API_PUBLIC_KEY") or ""


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SMS_NUMBER = os.getenv("TWILIO_SMS_NUMBER")         # e.g., +1234567890
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") # e.g., whatsapp:+1234567890
TWILIO_EMAIL = os.getenv("TWILIO_EMAIL")                   # Twilio SendGrid or Mail API
