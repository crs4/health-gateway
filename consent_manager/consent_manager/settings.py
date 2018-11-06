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


import logging
import os

import sys
import yaml

from hgw_common.saml_config import get_saml_config


def get_path(base_path, file_path):
    return file_path if os.path.isabs(file_path) else os.path.join(base_path, file_path)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The order of the paths is important. We will give priority to the one in etc
_CONF_FILES_PATH = ['/etc/hgw_service/consent_manager_config.yml', get_path(BASE_DIR, './config.yml')]

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

ALLOWED_HOSTS = cfg['django']['hostname'].split(',')
HOSTNAME = ALLOWED_HOSTS[0]

DEBUG = cfg['django']['debug']

ALLOWED_HOSTS = ['*']

MAX_API_VERSION = 1

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangosaml2',
    'oauth2_provider',
    'rest_framework',
    'hgw_common',
    'corsheaders',
    'drf_yasg',
    'webpack_loader',
    'consent_manager',
    'gui'
]

if 'port' in cfg['django']:
    ROOT_URL = 'https://{}:{}'.format(HOSTNAME, cfg['django']['port'])
else:
    ROOT_URL = 'https://{}'.format(HOSTNAME)

ROOT_URLCONF = 'consent_manager.urls'

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
    'djangosaml2.backends.Saml2Backend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
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
    'DEFAULT_AUTHENTICATION_CLASSES': ('oauth2_provider.ext.rest_framework.authentication.OAuth2Authentication',
                                       'rest_framework.authentication.SessionAuthentication'),
    'DEFAULT_PERMISSION_CLASSES': ('oauth2_provider.ext.rest_framework.permissions.TokenHasScope',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'EXCEPTION_HANDLER': 'hgw_common.utils.custom_exception_handler',
    'NON_FIELD_ERRORS_KEY': 'generic_errors',
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates'),
                 os.path.join(BASE_DIR, '../gui/templates')],
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

WSGI_APPLICATION = 'consent_manager.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DEFAULT_DB_NAME,
    }
}

AUTH_PASSWORD_VALIDATORS = []

CORS_ORIGIN_ALLOW_ALL = DEBUG

LANGUAGE_CODE = 'en-us'
TIME_ZONE = cfg['django']['timezone']
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = 'consent_manager.ConsentManagerUser'
USER_ID_FIELD = 'fiscalNumber'
STATIC_URL = '/static/'
LOGIN_URL = '/saml2/login/'
STATIC_ROOT = os.path.join(BASE_DIR, '../static/')
STATICFILES_DIRS = (
    ('gui', os.path.join(BASE_DIR, '../gui/assets/')),
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'gui/bundles/',  # must end with slash
        'STATS_FILE': os.path.join(BASE_DIR, '../gui/webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map']
    }
}

SESSION_COOKIE_NAME = 'consent_manager'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# SAML CONFIGURATIONS
SAML_SERVICE = cfg['saml']['service']
SAML_SP_NAME = cfg['saml']['sp_name']
SAML_IDP_URL = cfg['saml']['idp_url']
SAML_SP_KEY_PATH = get_path(BASE_CONF_DIR, cfg['saml']['sp_key'])
SAML_SP_CRT_PATH = get_path(BASE_CONF_DIR, cfg['saml']['sp_cert'])
SAML_CONFIG = get_saml_config(ROOT_URL, SAML_SP_NAME, SAML_SP_KEY_PATH, SAML_SP_CRT_PATH, SAML_SERVICE,
                              SAML_IDP_URL)
if SAML_SERVICE == 'spid':
    SAML_ATTRIBUTE_MAPPING = {
       'spidCode': ('username',),
       'fiscalNumber': ('fiscalNumber',)
    }
else:
    SAML_ATTRIBUTE_MAPPING = {
        'uid': ('username', ),
        'fiscalNumber': ('fiscalNumber', )
    }

SAML_AUTHN_CUSTOM_ARGS = {
    'attribute_consuming_service_index': '1'
}

# OAUTH2 CONFIGURATIONS
SCOPES = {
    'consent:read': 'Read scope',
    'consent:write': 'Write scope'
}
DEFAULT_SCOPES = ['consent:read', 'consent:write']


class ApplicationBasedScope(object):
    def get_all_scopes(self):
        return SCOPES

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        if application.scopes:
            return application.scopes.split(" ")
        return SCOPES.keys()

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        if application.scopes:
            return application.scopes.split(" ")
        return DEFAULT_SCOPES


OAUTH2_PROVIDER_APPLICATION_MODEL = 'consent_manager.RESTClient'

OAUTH2_PROVIDER = {
    'SCOPES': SCOPES,
    'SCOPES_BACKEND_CLASS': ApplicationBasedScope,
    'DEFAULT_SCOPES': DEFAULT_SCOPES
}

REQUEST_VALIDITY_SECONDS = 36000

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'consent': {
            'type': 'oauth2',
            'tokenUrl': '{}/oauth2/token/'.format(ROOT_URL),
            'flow': 'application',
            'scopes': DEFAULT_SCOPES
        }
    }
}
