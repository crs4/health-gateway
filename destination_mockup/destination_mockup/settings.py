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


from django.conf import settings
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%j0+-u7z_(ayc#!fs==r1u*n+t)p9tw8$_0c!a7$1nu5(89s67'

# TODO: remove default, destination_mockup should be a base app for building destination.
OAUTH_CLIENT_ID = getattr(settings, 'OAUTH_CLIENT_ID', 'xFfLPuIh2n8Kqj6RMUroYLUbVai1K7qeB1R2gExP')
OAUTH_CLIENT_SECRET = getattr(
    settings,
    'OAUTH_CLIENT_SECRET',
    'RjKAdqZqCkRA3eq7pjkwEVuku1BRVRBWiAg5VooBl3YcXnu26TpQGclL43X3WrP47DsbHIyIVXHTX8vdd6KZqr4kQMUpuWUlMvC3qPiDgt9j2jwmasRvdsF9R48um1LJ')

DESTINATION_ID = getattr(settings, 'DESTINATION_ID', None)
if DESTINATION_ID is None:
    DESTINATION_ID_PATHS = ['/etc/destination_mockup/destination_id', '/etc/destination_id', 'destination_id']
    for dp in DESTINATION_ID_PATHS:
        try:
            with open(dp, 'r') as f:
                DESTINATION_ID = f.read()
        except IOError:
            continue
        else:
            break
assert DESTINATION_ID is not None

KAFKA_BROKER = getattr(settings, 'KAFKA_BROKER', 'kafka:9093')
KAFKA_TOPIC = DESTINATION_ID
KAFKA_CA_CERT = getattr(settings, 'KAFKA_CA_CERT', os.path.join(os.path.dirname(__file__),
                                                                '../../certs/ca/kafka/certs/ca/kafka.chain.cert.pem'))
KAFKA_CLIENT_CERT = getattr(settings, 'KAFKA_CLIENT_CERT',
                            os.path.join(os.path.dirname(__file__),
                                         '../../certs/ca/kafka/certs/destinationmockup/cert.pem'))
KAFKA_CLIENT_KEY = getattr(settings, 'KAFKA_CLIENT_KEY',
                           os.path.join(os.path.dirname(__file__),
                                        '../../certs/ca/kafka/certs/destinationmockup/key.pem'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['localhost', 'destinationmockup']

HGW_FRONTEND_URI = 'https://hgwfrontend:8000'

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'destination_mockup'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

ROOT_URLCONF = 'destination_mockup.urls'

WSGI_APPLICATION = 'destination_mockup.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'destination_mockup_db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

SESSION_COOKIE_NAME = 'destination_mockup'
