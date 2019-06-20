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
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import requests

from test_data import (ACTIVE_CHANNEL_ID, ACTIVE_CONSENT_ID,
                       CONSENT_WITH_NO_PROCESS_ID, DESTINATION, FLOW_ID,
                       PENDING_CONSENT_ID, PERSON_ID, PROCESS_ID, SOURCES,
                       UNKNOWN_OAUTH_CLIENT)


class MockRequestHandler(BaseHTTPRequestHandler):
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def _handle_oauth(self, post_data):
        if UNKNOWN_OAUTH_CLIENT.encode('utf-8') in post_data:
            payload = {u'error': u'invalid_client'}
            status_code = 401
        else:
            payload = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                       'token_type': 'Bearer',
                       'expires_in': 36000,
                       'expires_at': 1499976952.401335,
                       'scope': ['read', 'write']}
            status_code = 201
        return payload, status_code

    def do_POST(self):
        if re.search(self.OAUTH2_PATTERN, self.path):
            length = int(self.headers['content-length'])
            post_data = self.rfile.read(length)
            payload, status_code = self._handle_oauth(post_data)
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
        raise NotImplementedError

    def log_message(self, *args, **kwargs):
        pass


class MockBackendRequestHandler(MockRequestHandler):
    SINGLE_SOURCE_PATTERN = re.compile(r'/v1/sources/\w+')
    SOURCES_PATTERN = re.compile(r'/v1/sources/\w*')

    def do_GET(self):

        if re.search(self.SOURCES_PATTERN, self.path):
            payload = SOURCES
        elif re.search(self.SINGLE_SOURCE_PATTERN, self.path):
            payload = SOURCES[0]
        else:
            payload = {}
        return self._send_response(payload)


class MockFrontendRequestHandler(MockRequestHandler):
    CHANNELS_PATTERN = re.compile(r'/v1/channels/search/\?consent_id=(\w+)')
    FLOW_REQUESTS_PATTERN = re.compile(r'/v1/flow_requests/search/\?channel_id=(\w+)')

    def do_GET(self):
        flow_request = {
            'flow_id': FLOW_ID,
            'process_id': PROCESS_ID,
            'status': 'AC',
            'profile': {'code': 'PROF_001',
                        'version': 'v0',
                        'payload': '[{"clinical_domain": "Laboratory"}]'},
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00',
            'sources': [{'source_id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT'}]
        }

        channel = {
            'channel_id': ACTIVE_CHANNEL_ID,
            'status': 'CR',
            'destination_id': 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj',
            'profile': {
                'code': 'PROF_001',
                'version': 'v0',
                'payload': '[{"clinical_domain": "Laboratory"}]'
            },
            'source': {
                'source_id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                'name': 'source_1',
                'profile': {
                    'code': 'PROF_001',
                    'version': 'v0',
                    'payload': '[{"clinical_domain": "Laboratory"}]'
                }
            }
        }

        payload = None
        fr_pattern = re.search(self.FLOW_REQUESTS_PATTERN, self.path)
        if fr_pattern:
            channel_id = fr_pattern.groups()[0]
            print("channel_id requested ", channel_id)
            if channel_id == ACTIVE_CHANNEL_ID:
                payload = flow_request
                status_code = requests.codes.ok
            else:
                payload = {'errors': ['not_found']}
                status_code = requests.codes.not_found
        else:
            channel_pattern = re.search(self.CHANNELS_PATTERN, self.path)
            if channel_pattern:
                consent_id = channel_pattern.groups()[0]
                if consent_id == ACTIVE_CONSENT_ID:
                    payload = channel
                    status_code = requests.codes.ok
                else:
                    payload = {'errors': ['not_found']}
                    status_code = requests.codes.not_found

        return self._send_response(payload, status_code)


class MockConsentManagerRequestHandler(MockRequestHandler):
    CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{}|{})/'.format(ACTIVE_CONSENT_ID, PENDING_CONSENT_ID,
                                                                    CONSENT_WITH_NO_PROCESS_ID))
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def do_GET(self):
        consent_search = re.search(self.CONSENT_PATTERN, self.path)
        if consent_search:
            profile_data = {
                'code': 'PROF_001',
                'version': 'v0',
                'payload': '[{"clinical_domain": "Laboratory"}]'
            }

            consent_id = consent_search.groups()[0]
            if consent_id in (ACTIVE_CONSENT_ID, CONSENT_WITH_NO_PROCESS_ID):
                payload = {
                    'source': {
                        'id': SOURCES[0]['source_id'],
                        'name': SOURCES[0]['name'],
                    },
                    'destination': DESTINATION,
                    'profile': profile_data,
                    'person_id': PERSON_ID,
                    'status': 'AC',
                    'consent_id': consent_id,
                    'confirm_id': 'confirm_id'
                }
            else:
                payload = {
                    'source': {
                        'id': SOURCES[1]['source_id'],
                        'name': SOURCES[1]['name'],
                    },
                    'destination': DESTINATION,
                    'profile': profile_data,
                    'person_id': PERSON_ID,
                    'status': 'PE',
                    'consent_id': consent_id,
                    'confirm_id': 'confirm_id'
                }
            status_code = requests.codes.ok
        else:
            payload = {'errors': ['not_found']}
            status_code = requests.codes.not_found
        return self._send_response(payload, status_code)


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def start_mock_server(cls, port=None):
    port = port or get_free_port()
    mock_server = HTTPServer(('localhost', port), cls)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()
