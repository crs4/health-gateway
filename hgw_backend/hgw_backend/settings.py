# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os

import sys
import yaml


def get_path(base_path, file_path):
    return file_path if os.path.isabs(file_path) else os.path.join(base_path, file_path)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The order of the paths is important. We will give priority to the one in etc
_CONF_FILES_PATH = ['/etc/hgw_service/hgw_backend_config.yml', get_path(BASE_DIR, './config.yml')]

cfg = None
_conf_file = None
for cf in _CONF_FILES_PATH:
    try:
        with open(cf, 'r') as f:
            cfg = yaml.load(f)
    except FileNotFoundError:
        continue
    else:
        _conf_file = cf
        break
if cfg is None:
    sys.exit("Config file not found")

SECRET_KEY = cfg['django']['secret_key']

BASE_CONF_DIR = os.path.dirname(os.path.abspath(_conf_file))

DEFAULT_DB_NAME = os.environ.get('DEFAULT_DB_NAME') or get_path(BASE_CONF_DIR, cfg['django']['database']['name'])


DEBUG = cfg['django']['debug']

ALLOWED_HOSTS = cfg['django']['hostname'].split(',')
HOSTNAME = ALLOWED_HOSTS[0]

MAX_API_VERSION = 1

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
    'rest_framework',
    'hgw_common',
    'hgw_backend',
]


AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('oauth2_provider.ext.rest_framework.authentication.OAuth2Authentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_PARSER_CLASSES': ('rest_framework.parsers.JSONParser',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

ROOT_URLCONF = 'hgw_backend.urls'

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

WSGI_APPLICATION = 'hgw_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DEFAULT_DB_NAME,
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = cfg['django']['timezone']
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOG_FILE = 'hgw_backend_logs'

STATIC_ROOT = os.path.join(BASE_DIR, '../static/')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, '../media/'))

SESSION_COOKIE_NAME = 'hgw_backend'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# OAUTH2 CONFIGURATIONS
SCOPES = {
    'messages:write': 'Write messages',
    'source:read': 'Read Source data'
}
DEFAULT_SCOPES = SCOPES


class ApplicationBasedScope(object):
    """
    Oauth2 custom class to handle scopes assignments to rest clients
    """

    @staticmethod
    def get_all_scopes():
        return SCOPES

    @staticmethod
    def get_available_scopes(application=None, request=None, *args, **kwargs):
        if application.scopes:
            return application.scopes.split(" ")
        return SCOPES.keys()

    @staticmethod
    def get_default_scopes(application=None, request=None, *args, **kwargs):
        if application.scopes:
            return application.scopes.split(" ")
        return DEFAULT_SCOPES


OAUTH2_PROVIDER_APPLICATION_MODEL = 'hgw_backend.RESTClient'

OAUTH2_PROVIDER = {
    'SCOPES': SCOPES,
    'SCOPES_BACKEND_CLASS': ApplicationBasedScope,
    'DEFAULT_SCOPES': DEFAULT_SCOPES
}

REQUEST_VALIDITY_SECONDS = 60

NOTIFICATION_TYPE = 'kafka'
KAFKA_BROKER = cfg['kafka']['uri']
KAFKA_CHANNEL_NOTIFICATION_TOPIC = 'channel_notification'
KAFKA_SOURCE_NOTIFICATION_TOPIC = 'hgw_backend_source_notification'
KAFKA_CONNECTOR_NOTIFICATION_TOPIC = 'hgw_backend_connector_notification'
KAFKA_SSL = cfg['kafka']['ssl']
KAFKA_CA_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['ca_cert'])
KAFKA_CLIENT_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['client_cert'])
KAFKA_CLIENT_KEY = get_path(BASE_CONF_DIR, cfg['kafka']['client_key'])
