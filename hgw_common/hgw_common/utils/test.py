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

"""
Module with utlities to be used in unit tests
"""

import json
import re
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import requests


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
            self._send_response(payload, status_code)
            return True
        return False

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