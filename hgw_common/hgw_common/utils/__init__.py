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
from itertools import product

import yaml
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.http import Http404
from django.utils.crypto import get_random_string
from kafka import KafkaConsumer, TopicPartition
from oauth2_provider.ext.rest_framework import TokenHasScope
from oauth2_provider.ext.rest_framework.permissions import SAFE_HTTP_METHODS
from oauth2_provider.settings import oauth2_settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler
from yaml.scanner import ScannerError


class TokenHasResourceDetailedScope(TokenHasScope):
    """
    A different version of TokenHasResourceScope. It allows the View class to specify a custom scope type for
    actions. If it is specified the view will require also the combined scope.
    The view_specific_scopes has this structure

    .. python:

        view_custom_instance = {<action_name>: {'read': <list_of_custom_scopes>, 'write': <list_custom_scopes>}}

    For example: if the View class specifies `required_scopes = ['myscope']` and
    `view_custom_instance = {'myaction': {'read': ['custom']}}`
    the token must have ['myscope:read', 'myscope:custom'] to access the view
    """

    def get_scopes(self, request, view):

        try:
            view_specific_scopes = getattr(view, 'view_specific_scopes')
        except AttributeError:
            view_specific_scopes = {}

        try:
            view_scopes = (
                super(TokenHasResourceDetailedScope, self).get_scopes(request, view)
            )
        except ImproperlyConfigured:
            view_scopes = []

        if request.method.upper() in SAFE_HTTP_METHODS:
            scope_type = [oauth2_settings.READ_SCOPE]
            try:
                if view.action in view_specific_scopes and 'read' in view_specific_scopes[view.action]:
                    scope_type.extend(view_specific_scopes[view.action]['read'])
            except AttributeError:
                pass
        else:
            scope_type = [oauth2_settings.WRITE_SCOPE]
            try:
                if view.action in view_specific_scopes and 'write' in view_specific_scopes[view.action]:
                    scope_type.extend(view_specific_scopes[view.action]['write'])
            except AttributeError:
                pass

        required_scopes = [
            '{0}:{1}'.format(combined_scope[0], combined_scope[1]) for combined_scope in
            product(view_scopes, scope_type)
        ]

        return required_scopes


class IsAuthenticatedOrTokenHasResourceDetailedScope(TokenHasResourceDetailedScope):

    def has_permission(self, request, view):
        # The authenticated user can perform all the actions
        if request.user and not request.user.is_anonymous():
            return request.user.is_authenticated
        else:
            try:
                # Some actions cannot be performed by external clients
                if view.action not in view.oauth_views:
                    return False
                else:
                    # Check the scopes
                    return super(IsAuthenticatedOrTokenHasResourceDetailedScope, self).has_permission(request, view)
            except AttributeError:
                return False


class KafkaConsumerCommand(BaseCommand):
    """
    This class implements a Django Command that consumes message from a kafka topic.
    It provides connection funcionalities. Subclasses must implement only the 
    real handling of the messages
    """

    def handle(self, *args, **options):
        consumer_params = {
            'bootstrap_servers': settings.KAFKA_BROKER,
            'client_id': self.client_id,
            'group_id': self.group_id,
        }
        if settings.KAFKA_SSL:
            consumer_params.update({
                'bootstrap_servers': settings.KAFKA_BROKER,
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': settings.KAFKA_CA_CERT,
                'ssl_certfile': settings.KAFKA_CLIENT_CERT,
                'ssl_keyfile': settings.KAFKA_CLIENT_KEY
            })

        consumer = KafkaConsumer(**consumer_params)
        partitions = [TopicPartition(topic, 0) for topic in self.topics]
        consumer.assign(partitions)
        for msg in consumer:
            self.handle_message(msg)

    def handle_message(self, message):
        raise NotImplementedError


def generate_id():
    """
    Generates a random string of 32 characters to be used as an id for objects
    """
    return get_random_string(32)


def get_oauth_token(server_uri, client_id, client_secret):
    """
    Obtains an OAuth2 token from :param:`server_uri` using :param:`client_id` and
    :param:`client_secret` as authentication parameters
    """
    client = BackendApplicationClient(client_id)
    oauth_session = OAuth2Session(client=client)
    token_url = '{}/oauth2/token/'.format(server_uri)
    access_token = oauth_session.fetch_token(token_url=token_url, client_id=client_id,
                                             client_secret=client_secret)

    access_token = access_token["access_token"]
    access_token_header = {"Authorization": "Bearer {}".format(access_token)}
    return oauth_session, access_token_header


def get_logger(logger_name):
    """
    Create, configure and returns a logger
    """
    level = logging.DEBUG if settings.DEBUG is True else logging.INFO
    logger = logging.getLogger(logger_name)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handlers = [logging.StreamHandler()]
    if hasattr(settings, 'LOG_FILE'):
        handlers.append(logging.handlers.RotatingFileHandler(settings.LOG_FILE))

    for handler in handlers:
        handler.setLevel(level)
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(level)

    return logger


def load_config_file(paths):
    cfg = None
    for path in paths:
        try:
            with open(path, 'r') as f:
                cfg = yaml.load(f, Loader=yaml.FullLoader)
                print(cfg)
        except (IOError, ScannerError, YAMLError):
            continue
        else:
            return cfg


class ERRORS:
    MISSING_PARAMETERS = 'missing_parameters'
    FORBIDDEN = 'forbidden'
    NOT_AUTHENTICATED = 'not_authenticated'
    NOT_FOUND = 'not_found'
    DUPLICATED = 'duplicated'


def custom_exception_handler(exc, context):
    """
    Configures the Django Rest Framework return messages
    """
    if isinstance(exc, Http404):
        response = Response({'errors': [ERRORS.NOT_FOUND]}, status=status.HTTP_404_NOT_FOUND)
    elif isinstance(exc, NotAuthenticated):
        response = Response({'errors': [ERRORS.NOT_AUTHENTICATED]}, status=status.HTTP_401_UNAUTHORIZED)
    elif isinstance(exc, PermissionDenied):
        response = Response({'errors': [ERRORS.FORBIDDEN]}, status=status.HTTP_403_FORBIDDEN)
    else:
        response = exception_handler(exc, context)

    return response
