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


import json
import re
import socket
from itertools import product
from threading import Thread

import requests
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import get_random_string
from http.server import BaseHTTPRequestHandler, HTTPServer
from oauth2_provider.ext.rest_framework import TokenHasScope
from oauth2_provider.ext.rest_framework.permissions import SAFE_HTTP_METHODS
from oauth2_provider.settings import oauth2_settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


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
    #
    # def has_permission(self, request, view):
    #     token = request.auth
    #
    #     if not token:
    #         return False
    #
    #     if hasattr(token, 'scope'):  # OAuth 2
    #         required_scopes = self.get_scopes(request, view)
    #         return token.is_valid(required_scopes)
    #
    #     assert False, ('TokenHasScope requires the'
    #                    '`oauth2_provider.rest_framework.OAuth2Authentication` authentication '
    #                    'class to be used.')

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
            if view.action in view_specific_scopes and 'read' in view_specific_scopes[view.action]:
                scope_type.extend(view_specific_scopes[view.action]['read'])
        else:
            scope_type = [oauth2_settings.WRITE_SCOPE]
            if view.action in view_specific_scopes and 'write' in view_specific_scopes[view.action]:
                scope_type.extend(view_specific_scopes[view.action]['write'])

        required_scopes = [
            '{0}:{1}'.format(combined_scope[0], combined_scope[1]) for combined_scope in
            product(view_scopes, scope_type)
        ]
        return required_scopes


def generate_id():
    return get_random_string(32)


class MockMessage(object):
    def __init__(self, key, topic, value, offset=0):
        self.key = key
        self.topic = topic
        self.value = value
        self.offset = offset


class MockRequestHandler(BaseHTTPRequestHandler):
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def _handle_oauth(self):
        payload = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                   'token_type': 'Bearer',
                   'expires_in': 36000,
                   'expires_at': 1499976952.401335,
                   'scope': ['read', 'write']}
        status_code = 201
        return payload, status_code

    def do_POST(self):
        if re.search(self.OAUTH2_PATTERN, self.path):
            payload, status_code = self._handle_oauth()
            return self._send_response(payload, status_code)

    def _path_match(self, path):
        return re.search(path, self.path)

    def _send_response(self, payload, status_code=requests.codes.ok):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps(payload)
        self.wfile.write(response.encode('utf-8'))

    def do_GET(self):
        raise NotImplemented

    def log_message(self, *args, **kwargs): pass


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def start_mock_server(certs_dir, cls, port=None):
    port = port or get_free_port()
    mock_server = HTTPServer(('localhost', port), cls)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()


def get_oauth_token(server_uri, client_id, client_secret):
    client = BackendApplicationClient(client_id)
    oauth_session = OAuth2Session(client=client)
    token_url = '{}/oauth2/token/'.format(server_uri)
    access_token = oauth_session.fetch_token(token_url=token_url, client_id=client_id,
                                             client_secret=client_secret)

    access_token = access_token["access_token"]
    access_token_header = {"Authorization": "Bearer {}".format(access_token)}
    return oauth_session, access_token_header
