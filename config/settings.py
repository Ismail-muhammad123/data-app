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

PRODUCTION = os.environ.get("PRODUCTION", "True").lower() == "true"

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
    # >custom template for admin
    'jazzmin',


    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # 3ed party apps
    'drf_spectacular',
    'corsheaders',
    

    # custom apps
    'users',
    'orders',
    'wallet',
    'payments',
    'summary',
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
    
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),  
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365), 
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

if PRODUCTION:
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
        'NAME': 'users.validators.DigitsOnlyValidator',
        'OPTIONS': {
            'min_length': 6,
        },
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


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")


MONNIFY_BASE_URL=os.getenv("MONNIFY_BASE_URL")
MONNIFY_API_KEY=os.getenv("MONNIFY_API_KEY")
MONNIFY_API_SECRET=os.getenv("MONNIFY_API_SECRET")
MONNIFY_CONTRACT_CODE=os.getenv("MONNIFY_CONTRACT_CODE")
MONNIFY_WEBHOOK_SECRET=os.getenv("MONNIFY_WEBHOOK_SECRET")



VTPASS_BASE_URL = ""
VTPASS_USERNAME = ""
VTPASS_PASSWORD = ""
VTPASS_BASE_URL = os.getenv("VTPASS_BASE_URL")
VTPASS_API_KEY = os.getenv("VTPASS_API_KEY") or ""
VTPASS_API_SECRET = os.getenv("VTPASS_API_SECRET") or ""
VTPASS_API_PUBLIC_KEY = os.getenv("VTPASS_API_PUBLIC_KEY") or ""


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SMS_NUMBER = os.getenv("TWILIO_SMS_NUMBER")         # e.g., +1234567890
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") # e.g., whatsapp:+1234567890
TWILIO_EMAIL = os.getenv("TWILIO_EMAIL")                   # Twilio SendGrid or Mail API



TERMII_API_KEY = os.getenv("TERMII_API_KEY")
TERMII_SENDER_ID = os.getenv("TERMII_SENDER_ID")
TERMII_EMAIL_CONFIG_ID = os.getenv("TERMII_EMAIL_CONFIG_ID")


# ----------------------------- ClubKonnect Configuration -----------------------------

CLUBKONNECT_BASE_URL = "https://www.nellobytesystems.com"

CLUBKONNECT_USER_ID = os.getenv("CLUBKONNECT_USER_ID", "")
CLUBKONNECT_API_KEY = os.getenv("CLUBKONNECT_API_KEY", "")

CLUBKONNECT_TIMEOUT = 30

# Endpoints
CLUBKONNECT_ENDPOINTS = {
    # wallet balance
    "balance": "/APIWalletBalanceV1.asp",

    # airtime
    "airtime_networks": "/APIAirtimeDiscountV2.asp",
    "buy_airtime": "/APIAirtimeV1.asp",
   
    # data
    "buy_data": "/APIDatabundleV1.asp",
    "data_plans": "/APIDatabundlePlansV2.asp",
    "query": "/APIQueryV1.asp",
    "cancel": "/APICancelV1.asp",

    # Smile
    "buy_smile": "/APISmileV1.asp",
    "smile_packages": "/APISmilePackagesV2.asp",

    # Cable
    "buy_cable": "/APICableTVV1.asp",
    "verify_cable": "/APIVerifyCableTVV1.0.asp",
    "cable_packages": "/APICableTVPackagesV2.asp",

    # Electricity
    "buy_electricity": "/APIElectricityV1.asp",
    "verify_electricity": "/APIVerifyElectricityV1.asp",
    "electricity_discos": "/APIElectricityDiscosV2.asp",
}

# ----------------------------- End ClubKonnect Configuration -----------------------------
# ----------------------------- Jazzmin Configuration -----------------------------

JAZZMIN_SETTINGS = {
    "site_title": "A-Star Data App",
    "site_header": "A-Star Data",
    "site_brand": "A-Star",
    "welcome_sign": "Welcome to A-Star Data App",
    "copyright": "A-Star Data App Ltd",
    "search_model": ["users.User"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "users.User"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": ["users.OTP", "authtoken.Token"],
    "order_with_respect_to": ["summary", "users", "orders", "wallet", "payments"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user-friends",
        "wallet.Wallet": "fas fa-wallet",
        "payments.Deposit": "fas fa-money-bill-wave",
        "payments.Withdrawal": "fas fa-hand-holding-usd",
        "orders.Purchase": "fas fa-shopping-cart",
        "summary.SummaryDashboard": "fas fa-chart-pie",
        "summary.SiteConfig": "fas fa-cogs",
        "summary.SystemTransaction": "fas fa-exchange-alt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_js": "js/jazzmin_fix.js",
    "custom_css": "css/admin_custom.css",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {},
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-indigo",
    "accent": "accent-indigo",
    "navbar": "navbar-indigo navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-indigo",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
