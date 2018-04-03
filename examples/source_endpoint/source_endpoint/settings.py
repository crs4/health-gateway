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

_CONF_FILES_PATH = ['/etc/hgw_service/source_endpoint_config.yml', get_path(BASE_DIR, './config.yml')]

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

DEBUG = True

HOSTNAME = cfg['django']['hostname']

ALLOWED_HOSTS = [HOSTNAME]

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
    'source_endpoint',
]

if DEBUG is True:
    INSTALLED_APPS.append('sslserver')

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

ROOT_URLCONF = 'source_endpoint.urls'

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

WSGI_APPLICATION = 'source_endpoint.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
CONSENT_MANAGER_URI = cfg['consent_manager']['uri']
CLIENT_ID = cfg['consent_manager']['client_id']
CLIENT_SECRET = cfg['consent_manager']['client_secret']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': get_path(BASE_CONF_DIR, cfg['django']['database']['name']),
    }
}

AUTH_PASSWORD_VALIDATORS = []

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('oauth2_provider.ext.rest_framework.authentication.OAuth2Authentication',),
    'DEFAULT_PERMISSION_CLASSES': ('oauth2_provider.ext.rest_framework.permissions.TokenHasScope',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
MAX_API_VERSION = 1
SOURCE_ID = cfg['source']['id']

# OAUTH2 CONFIG
SCOPES = {'read': 'Read scope', 'write': 'Write scope'}
OAUTH2_PROVIDER = {
    'SCOPES': SCOPES,
    'DEFAULT_SCOPES': SCOPES.keys()
}

KAFKA_BROKER = cfg['kafka']['uri']
KAFKA_CA_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['ca_cert'])
KAFKA_CLIENT_CERT = get_path(BASE_CONF_DIR, cfg['kafka']['client_cert'])
KAFKA_CLIENT_KEY = get_path(BASE_CONF_DIR, cfg['kafka']['client_key'])
