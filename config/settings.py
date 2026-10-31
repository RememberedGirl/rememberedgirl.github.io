from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'local-static-export-no-authentication')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']
INSTALLED_APPS = ['django.contrib.staticfiles', 'board']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.middleware.common.CommonMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True}]
DATABASES = {}  # The public site reads a sanitized snapshot, never the collector database.
STATIC_URL = '/assets/'
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True
LANGUAGE_CODE = 'ru'
PUBLIC_SNAPSHOT = BASE_DIR / 'data' / 'clan.json'
