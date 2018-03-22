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

# from oauth2_provider.scopes import BaseScopes

from hgw_common.saml_config import get_saml_config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_NAME = os.environ.get('DEFAULT_DB_NAME') or os.path.join(BASE_DIR, 'consent_manager_db.sqlite3')
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'i*w3i*-y589ynfl_sar!h9r1mpra8mkjpwobeage5h5a(0x!d$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

HOSTNAME = 'consentmanager'
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
    'consent_manager',
    'hgw_common',
    'corsheaders',
    'drf_yasg'
]

if DEBUG is True:
    INSTALLED_APPS.append('sslserver')
    ROOT_URL = 'https://' + HOSTNAME + ':8002'
else:
    ROOT_URL = 'https://' + HOSTNAME

ROOT_URLCONF = 'consent_manager.urls'

SAML_SP_NAME = 'Consent Manager Service Provider'
SAML_SP_KEY_PATH = os.path.join(os.path.dirname(__file__), '../certs/spid.key.pem')
SAML_SP_CRT_PATH = os.path.join(os.path.dirname(__file__), '../certs/spid.cert.pem')
SAML_CONFIG = get_saml_config(ROOT_URL, SAML_SP_NAME, SAML_SP_KEY_PATH, SAML_SP_CRT_PATH)
SAML_ATTRIBUTE_MAPPING = {
    'spidCode': ('username',),
    'fiscalNumber': ('fiscalNumber',)
}
SAML_AUTHN_CUSTOM_ARGS = {
    'attribute_consuming_service_index': '1'
}

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
    'DEFAULT_AUTHENTICATION_CLASSES': ('oauth2_provider.ext.rest_framework.authentication.OAuth2Authentication',),
    'DEFAULT_PERMISSION_CLASSES': ('oauth2_provider.ext.rest_framework.permissions.TokenHasScope',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = 'consent_manager.ConsentManagerUser'
STATIC_ROOT = os.path.join(BASE_DIR, './static/')
STATIC_URL = '/static/'
LOGIN_URL = '/saml2/login/'

SESSION_COOKIE_NAME = 'consent_manager'


OAUTH2_PROVIDER_APPLICATION_MODEL = 'consent_manager.RESTClient'

SCOPES = {
    'consent:read': 'Read scope',
    'consent:write': 'Write scope'
}
DEFAULT_SCOPES = ['consent:read', 'consent:write']

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


OAUTH2_PROVIDER = {
    'SCOPES': SCOPES,
    'SCOPES_BACKEND_CLASS': ApplicationBasedScope,
    'DEFAULT_SCOPES': DEFAULT_SCOPES
}

REQUEST_VALIDITY_SECONDS = 60
