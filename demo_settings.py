"""Isolated, read-only portfolio demo. Never point this at client data."""
from brownie_car_rent.settings.base import *

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
CSRF_TRUSTED_ORIGINS = ['https://' + h for h in ALLOWED_HOSTS if h.endswith('.onrender.com')]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'portfolio_demo.sqlite3'}}
ROOT_URLCONF = 'demo_urls'
WSGI_APPLICATION = 'demo_wsgi.application'
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'debug_toolbar']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'demo_middleware.PortfolioDemoMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'demo_static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
MEDIA_URL = '/static/demo/'
MEDIA_ROOT = BASE_DIR / 'demo_static' / 'demo'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_NAME = 'car_rental_demo_session'
SESSION_COOKIE_SECURE = bool(os.environ.get('RENDER'))
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = bool(os.environ.get('RENDER'))
SECURE_HSTS_SECONDS = 3600
SESSION_COOKIE_HTTPONLY = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
FILE_UPLOAD_MAX_MEMORY_SIZE = 65536
CORS_ALLOW_ALL_ORIGINS = False
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'console': {'class': 'logging.StreamHandler'}}, 'root': {'handlers': ['console'], 'level': 'WARNING'}}
DEMO_TITLE = 'Brownie Car Rental'
DEMO_LINKS = [('/', 'Home'), ('/car/carlist/', 'Browse sample fleet'), ('/demo/start/', 'Explore customer account'), ('/demo/admin/', 'View admin demo')]
DEMO_PROFILE_PATH = '/car/newcar/'
