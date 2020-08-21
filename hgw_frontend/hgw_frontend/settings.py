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
from yaml.error import YAMLError
from yaml.scanner import ScannerError

from hgw_common.saml_config import get_saml_config


def get_path(base_path, file_path):
    return file_path if os.path.isabs(file_path) else os.path.join(base_path, file_path)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The order of the paths is important. We will give priority to the one in etc
_CONF_FILES_PATH = ['/etc/hgw_service/hgw_frontend_config.yml', get_path(BASE_DIR, 'config.local.yml')]

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

ALLOWED_HOSTS = cfg['django']['hostname'].split(',')
HOSTNAME = ALLOWED_HOSTS[0]

DEBUG = cfg['django']['debug']
LOG_LEVEL = cfg['logging']['level']

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
    'corsheaders',
    'hgw_common',
    'hgw_frontend',
]

if 'port' in cfg['django']:
    ROOT_URL = 'https://{}:{}'.format(HOSTNAME, cfg['django']['port'])
else:
    ROOT_URL = 'https://{}'.format(HOSTNAME)

ROOT_URLCONF = 'hgw_frontend.urls'

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

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'level': LOG_LEVEL,
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'hgw_frontend': {
#             'handlers': ['console'],
#             'level': LOG_LEVEL,
#         },
#         'djangosaml2': {
#             'handlers': ['console'],
#             'level': LOG_LEVEL,
#         },
#     }
# }

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
        'hgw_frontend': {
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
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('oauth2_provider.ext.rest_framework.authentication.OAuth2Authentication',),
    'DEFAULT_PERMISSION_CLASSES': ('oauth2_provider.ext.rest_framework.permissions.TokenHasScope',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_PARSER_CLASSES': ('rest_framework.parsers.JSONParser',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'ALLOWED_VERSIONS': ['v{}'.format(version) for version in range(1, MAX_API_VERSION + 1)],
    'EXCEPTION_HANDLER': 'hgw_common.utils.custom_exception_handler',
    'NON_FIELD_ERRORS_KEY': 'generic_errors',
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')],
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

WSGI_APPLICATION = 'hgw_frontend.wsgi.application'

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

AUTH_USER_MODEL = 'hgw_frontend.HGWFrontendUser'
USER_ID_FIELD = 'fiscalNumber'
STATIC_ROOT = os.path.join(BASE_DIR, '../static/')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    # ('hgw_frontend', os.path.abspath(os.path.join(BASE_DIR, '../static/'))),
)
LOGIN_URL = '/saml2/login/'
LOGIN_REDIRECT_URL = '/'

SESSION_COOKIE_NAME = 'hgw_frontend'
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

SAML_ACS_FAILURE_RESPONSE_FUNCTION = 'hgw_frontend.views.site.saml_redirect_failures'

# OAUTH2 CONFIGURATIONS
FLOW_REQUESTS_SCOPES = {
    'flow_request:read': 'Read flow request belonging to the corrispondent destination',
    'flow_request:write': 'Write scope. You can add, update or delete a flow_request',
    'flow_request:query': 'Perform flow request query',
}
MESSAGES_SCOPES = {
    'messages:read': 'Read messages for a Destination'
}
SOURCES_SCOPES = {
    'sources:read': 'Read sources'
}
SCOPES = {**FLOW_REQUESTS_SCOPES, **MESSAGES_SCOPES}

DEFAULT_SCOPES = ['flow_request:read', 'flow_request:write']


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


OAUTH2_PROVIDER_APPLICATION_MODEL = 'hgw_frontend.RESTClient'

OAUTH2_PROVIDER = {
    'SCOPES': SCOPES,
    'SCOPES_BACKEND_CLASS': ApplicationBasedScope,
    'DEFAULT_SCOPES': DEFAULT_SCOPES
}

REQUEST_VALIDITY_SECONDS = cfg['django']['request_validity_seconds']

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'flow_request': {
            'type': 'oauth2',
            'tokenUrl': '{}/oauth2/token/'.format(ROOT_URL),
            'flow': 'application',
            'scopes': FLOW_REQUESTS_SCOPES
        },
        'messages': {
            'type': 'oauth2',
            'tokenUrl': '{}/oauth2/token/'.format(ROOT_URL),
            'flow': 'application',
            'scopes': MESSAGES_SCOPES
        }
    }
}

# SERVICES CONFIGURATION
CONSENT_MANAGER_URI = cfg['consent_manager']['uri']
CONSENT_MANAGER_CLIENT_ID = cfg['consent_manager']['client_id']
CONSENT_MANAGER_CLIENT_SECRET = cfg['consent_manager']['client_secret']
CONSENT_MANAGER_CONFIRMATION_PAGE = '{}/confirm_consents/'.format(CONSENT_MANAGER_URI)

# SERVICES CONFIGURATION
HGW_BACKEND_URI = cfg['hgw_backend']['uri']
HGW_BACKEND_CLIENT_ID = cfg['hgw_backend']['client_id']
HGW_BACKEND_CLIENT_SECRET = cfg['hgw_backend']['client_secret']

NOTIFICATION_TYPE = 'kafka'
if NOTIFICATION_TYPE == 'kafka':
    KAFKA_BROKER = cfg['kafka']['uri']
    KAFKA_CHANNEL_NOTIFICATION_TOPIC = 'channel-notification'
    KAFKA_SOURCE_NOTIFICATION_TOPIC = 'hgw-backend-source-notification'
    KAFKA_CONNECTOR_NOTIFICATION_TOPIC = 'hgw-backend-connector-notification'
    KAFKA_CONSENT_NOTIFICATION_TOPIC = 'consent-manager-notification'
    KAFKA_SSL = cfg['kafka']['ssl']
    KAFKA_CA_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['ca_cert'])
    KAFKA_CLIENT_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['client_cert'])
    KAFKA_CLIENT_KEY = get_path(BASE_CONF_DIR, cfg['kafka']['client_key'])

DB_FAILURE_EXP_RETRY_BASE_PERIOD = cfg['django']['database']['failure_exp_retry_base_period_sec']
DB_FAILURE_MAX_RETRY_WAIT = cfg['django']['database']['failure_max_retry_wait']
