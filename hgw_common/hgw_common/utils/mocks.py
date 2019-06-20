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
import time

from django.utils.crypto import get_random_string
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import requests
from unittest.mock import MagicMock, Mock


class MockOAuth2Session(MagicMock):
    RESPONSES = []
    RAISES = None

    def __init__(self, *args, **kwargs):
        super(MockOAuth2Session, self).__init__(*args, **kwargs)
        self.token = None
        self.fetch_token = Mock(side_effect=self._fetch_token)
        self.get = Mock(side_effect=self._get)
        self._get_counter = 0

    def _fetch_token(self, **kwargs):
        if self.RAISES is None:
            self.token = {
                'access_token': get_random_string(30),
                'token_type': 'Bearer',
                'expires_in': 36000,
                'expires_at': time.time() + 36000,
                'scope': ['read', 'write']
            }
            return self.token
        else:
            raise self.RAISES()

    def _get(self, url, *args, **kwargs):
        res = self.RESPONSES[self._get_counter % len(self.RESPONSES)]
        self._get_counter += 1

        if isinstance(res, Exception):
            raise res
        else:
            response = Mock()
            response.status_code = res
            return response


class MockMessage(object):
    def __init__(self, topic, value, offset, key=None, headers=None):
        self.key = key
        self.topic = topic
        self.value = value
        self.offset = offset
        self.headers = headers if headers is not None else []


class MockRequestHandler(BaseHTTPRequestHandler):
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')
    OAUTH2_TOKEN = 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3'

    def _handle_oauth(self):
        payload = {'access_token': self.OAUTH2_TOKEN,
                   'token_type': 'Bearer',
                   'expires_in': 1800,
                   'expires_at': time.time() + 1800,
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

    def _content_data(self):
        length = int(self.headers['content-length'])
        return self.rfile.read(length).decode('utf-8')

    def _json_data(self):
        return json.loads(self._content_data())

    def do_GET(self):
        raise NotImplementedError

    def log_message(self, *args, **kwargs): pass


class MockKafkaConsumer(object):
    """
    Simulates a KafkaConsumer
    """

    MESSAGES = []
    FIRST = 0
    END = 1

    def __init__(self, *args, **kwargs):
        super(MockKafkaConsumer, self).__init__()
        self.counter = 0

    def beginning_offsets(self, topics_partition):
        return {topics_partition[0]: self.FIRST}

    def end_offsets(self, topics_partition):
        return {topics_partition[0]: self.END}

    def seek(self, topics_partition, index):
        self.counter = index

    def __getattr__(self, item):
        return MagicMock()

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            m = self.MESSAGES[self.counter]
        except KeyError:
            raise StopIteration
        else:
            self.counter += 1
            return m


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
    return mock_server_thread, mock_server

def stop_mock_server(mock_server_thread, mock_server):
    mock_server.shutdown()
    mock_server_thread.join()
