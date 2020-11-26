import logging
import os

import environ
from google.auth import default as default_creds

log = logging.getLogger(__name__)
# necessary as we can't ask for a list of all secrets.
settings_from_secrets = [
    "DATABASE_URL",
    "SECRET_KEY",
]

# we can set secrets via docker-compose if we like for local dev.
if not all(k in os.environ.keys() for k in settings_from_secrets):
    from utils import secrets_helper

    secrets = secrets_helper.access_secrets(settings_from_secrets)
    os.environ.update({key: value for key, value in secrets.items() if key not in os.environ})

env = environ.Env(DEBUG=(bool, False))

root = environ.Path(__file__) - 3
SITE_ROOT = root()

DEBUG = env("DEBUG", default=False)
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = env("SECRET_KEY", default=None)
ENVIRONMENT_NAME = env("ENVIRONMENT_NAME", default="uat")
if SECRET_KEY is None:
    log.warning("SECRET_KEY is not set! Using development key.")
    SECRET_KEY = "dev-key-dev-key-dev-key-dev-key-dev-key-dev-key-dev-key"

# handle raw host(s), or http(s):// host(s), or no host.
if "CURRENT_HOST" in os.environ:
    HOSTS = []
    for h in env.list("CURRENT_HOST"):
        if "://" in h:
            h = h.split("://")[1]
        HOSTS.append(h)
else:
    HOSTS = ["localhost"]

ALLOWED_HOSTS = HOSTS

# Enable Django security precautions if *not* running locally
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "{{cookiecutter.application_name}}",
    "django_cloudtask",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_ROOT = "/app/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATIC_HOST = "/"
STATIC_URL = "/static/"

MEDIA_ROOT = "media/"  # where files are stored on the local FS (in this case)
MEDIA_URL = "/media/"  # what is prepended to the image URL (in this case)


ROOT_URLCONF = "{{cookiecutter.application_name}}.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "{{cookiecutter.application_name}}.wsgi.application"

DATABASES = {"default": env.db(default="postgres:///django")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-au"
TIME_ZONE = "Australia/Melbourne"
USE_I18N = True
USE_L10N = True
USE_TZ = True


LOGIN_URL = "/admin/login/"
LOGIN_ERROR_URL = LOGIN_URL
LOGIN_REDIRECT_URL = "/admin/"  # Default redirect after logging in.

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

try:
    _, project_id = default_creds()
except Exception:
    project_id = "development"

if not project_id:
    project_id = env("PROJECT_ID", default="development")


# django_cloudtask specific
TASK_DOMAIN = env("TASK_DOMAIN", default=HOSTS[0])
PROJECT_ID = project_id
PROJECT_REGION = "{{cookiecutter.gcp_region}}"
TASK_SERVICE_ACCOUNT = f"{{cookiecutter.application_name}}-app@{PROJECT_ID}.iam.gserviceaccount.com"
TASK_DEFAULT_QUEUE = "default"


if DEBUG:

    def show_toolbar(request):
        # because docker
        return True

    INSTALLED_APPS.append("debug_toolbar")
    INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]
    MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": show_toolbar,
    }
