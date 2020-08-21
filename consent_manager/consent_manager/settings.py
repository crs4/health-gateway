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

import saml2
import yaml
from django.conf.global_settings import LOGIN_REDIRECT_URL
from saml2 import BINDING_HTTP_REDIRECT
from yaml.error import YAMLError
from yaml.scanner import ScannerError

from hgw_common.saml_config import get_saml_config


def get_path(base_path, file_path):
    return file_path if os.path.isabs(file_path) else os.path.join(base_path, file_path)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The order of the paths is important. We will give priority to the one in etc
_CONF_FILES_PATH = ['/etc/hgw_service/consent_manager_config.yml', get_path(BASE_DIR, 'config.local.yml')]

cfg = None
_conf_file = None
for cf in _CONF_FILES_PATH:
    try:
        with open(cf, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
    except (IOError, ScannerError, YAMLError):
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
LOG_LEVEL = cfg['logging']['level']

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
    'webpack_loader',
    'martor',
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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '{asctime} - {name} - {levelname} - {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        'consent_manager': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True
        },
        'hgw_common': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True
        },
        'djangosaml2': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True
        }
    }
}

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

DB_ENGINE = cfg['django']['database']['engine']
if DB_ENGINE == 'sqlite3':
    DEFAULT_DB_NAME = os.environ.get('DEFAULT_DB_NAME') or get_path(BASE_CONF_DIR, cfg['django']['database']['name'])
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.{}'.format(DB_ENGINE),
            'NAME': DEFAULT_DB_NAME
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.{}'.format(DB_ENGINE),
            'NAME': cfg['django']['database']['name'],
            'USER': cfg['django']['database']['user'],
            'PASSWORD': cfg['django']['database']['password'],
            'HOST': cfg['django']['database']['host'],
            'PORT': cfg['django']['database']['port'],
        }
    }


AUTH_PASSWORD_VALIDATORS = []

CORS_ORIGIN_ALLOW_ALL = DEBUG

LANGUAGE_CODE = 'en-us'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
TIME_ZONE = cfg['django']['timezone']
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = 'consent_manager.ConsentManagerUser'
USER_ID_FIELD = 'fiscalNumber'
STATIC_URL = '/static/'
LOGIN_URL = '/saml2/login/'
# LOGIN_REDIRECT_URL = '/'
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
SAML_LOGOUT_REQUEST_PREFERRED_BINDING = saml2.BINDING_HTTP_REDIRECT
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
    """
    oAuth2 custom class to handle scopes
    """

    @staticmethod
    def get_all_scopes():
        """
        Returns all scopes
        """
        return SCOPES

    @staticmethod
    def get_available_scopes(*args, application=None, request=None, **kwargs):
        """
        Returns available scopes
        """
        if application.scopes:
            return application.scopes.split(" ")
        return SCOPES.keys()

    @staticmethod
    def get_default_scopes(*args, application=None, request=None, **kwargs):
        """
        Returns all scopes
        """
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

NOTIFICATION_TYPE = cfg['notification']['type']
if NOTIFICATION_TYPE == 'kafka':
    KAFKA_BROKER = cfg['notification']['kafka']['uri']
    KAFKA_NOTIFICATION_TOPIC = cfg['notification']['kafka']['topic']
    KAFKA_SSL = cfg['notification']['kafka']['ssl']
    KAFKA_CA_CERT = get_path(BASE_CONF_DIR, cfg['notification']['kafka']['ca_cert'])
    KAFKA_CLIENT_CERT = get_path(BASE_CONF_DIR, cfg['notification']['kafka']['client_cert'])
    KAFKA_CLIENT_KEY = get_path(BASE_CONF_DIR, cfg['notification']['kafka']['client_key'])


MARTOR_ENABLE_CONFIGS = {
    'emoji': 'false',        # to enable/disable emoji icons.
    'imgur': 'false',        # to enable/disable imgur/custom uploader.
    'mention': 'false',     # to enable/disable mention
    'jquery': 'true',       # to include/revoke jquery (require for admin default django)
    'living': 'false',      # to enable/disable live updates in preview
    'spellcheck': 'false',  # to enable/disable spellcheck in form textareas
    'hljs': 'true',         # to enable/disable hljs highlighting in preview
}