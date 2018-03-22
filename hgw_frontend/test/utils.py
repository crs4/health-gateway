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

from django.utils.crypto import get_random_string
from mock import MagicMock

from hgw_common.utils import MockRequestHandler, MockMessage
from hgw_frontend.models import FlowRequest
from . import CORRECT_CONSENT_ID, WRONG_CONFIRM_ID, CORRECT_CONFIRM_ID, WRONG_CONSENT_ID, \
    TEST_PERSON1_ID, CORRECT_CONSENT_ID2, WRONG_CONSENT_ID2, CORRECT_CONFIRM_ID2, WRONG_CONFIRM_ID2


class MockConsentManagerRequestHandler(MockRequestHandler):
    CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(CORRECT_CONSENT_ID, CORRECT_CONSENT_ID2))
    WRONG_CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(WRONG_CONSENT_ID, WRONG_CONSENT_ID2))
    CONSENTS_PATTERN = re.compile(r'/v1/consents/')
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def do_POST(self):
        if re.search(self.CONSENTS_PATTERN, self.path):
            length = int(self.headers['content-length'])
            if TEST_PERSON1_ID.encode('utf-8') in self.rfile.read(length):
                payload = {"consent_id": get_random_string(32),
                           "confirm_id": get_random_string(32),
                           "status": "PE"}
                status_code = 201
            else:
                payload = []
                status_code = 400
        elif re.search(self.OAUTH2_PATTERN, self.path):
            payload = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                       'token_type': 'Bearer',
                       'expires_in': 36000,
                       'expires_at': 1499976952.401335,
                       'scope': ['read', 'write']}
            status_code = 201
        else:
            payload = {}
            status_code = 200
        return self._send_response(payload, status_code)

    def do_GET(self):
        consent_search = re.search(self.CONSENT_PATTERN, self.path)
        if consent_search:
            profile_payload = [{'clinical_domain': 'Laboratory',
                                'filters': [{'includes': 'immunochemistry', 'excludes': 'HDL'}]},
                               {'clinical_domain': 'Radiology',
                                'filters': [{'includes': 'Tomography', 'excludes': 'Radiology'}]},
                               {'clinical_domain': 'Emergency',
                                'filters': [{'includes': '', 'excludes': ''}]},
                               {'clinical_domain': 'Prescription',
                                'filters': [{'includes': '', 'excludes': ''}]}]
            profile_data = {
                'code': 'PROF002',
                'version': 'hgw.document.profile.v0',
                'payload': json.dumps(profile_payload)
            }

            consent_id = consent_search.groups()[0]
            confirm_id = CORRECT_CONFIRM_ID if consent_search.groups()[0] == CORRECT_CONSENT_ID \
                else CORRECT_CONFIRM_ID2

            payload = {
                'source': {
                    'id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                    'name': 'Source 1'
                },
                'destination': {
                    'id': 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj',
                    'name': 'Destination 1'
                },
                'profile': profile_data,
                'patient_id': TEST_PERSON1_ID,
                'status': FlowRequest.ACTIVE,
                'consent_id': consent_id,
                'confirm_id': confirm_id
            }
        else:
            consent_search = re.search(self.WRONG_CONSENT_PATTERN, self.path)
            if consent_search:
                consent_id = consent_search.groups()[0]
                confirm_id = WRONG_CONFIRM_ID if consent_search.groups()[0] == WRONG_CONSENT_ID else \
                    WRONG_CONFIRM_ID2
                payload = {
                    "consent_id": consent_id,
                    "confirm_id": confirm_id,
                    "status": "PE"
                }
            else:
                payload = {}
        return self._send_response(payload)


class MockBackendRequestHandler(MockRequestHandler):
    SINGLE_SOURCE_PATTERN = re.compile(r'/v1/sources/\w+')
    SOURCES_PATTERN = re.compile(r'/v1/sources/\w*')

    def do_GET(self):
        source = {
              "source_id": "iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT",
              "name": "SOURCE_ENDPOINT_MOCKUP",
              "url": "https://source_endpoint_mockup:8444/v1/connectors/"
            }
        if self._path_match(self.SOURCES_PATTERN):
            payload = [source]

        elif self._path_match(self.SINGLE_SOURCE_PATTERN):
            payload = source
        else:
            payload = {}
        return self._send_response(payload)


class MockKafkaConsumer(object):
    """
    Simulates a KafkaConsumer
    """

    def __init__(self, *args, **kwargs):
        super(MockKafkaConsumer, self).__init__()
        self.first = 3
        self.end = 33
        self.messages = {i: MockMessage(key="09876".encode('utf-8'), offset=i,
                                        topic='vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj'.encode('utf-8'),
                                        value=b'first_message') for i in range(self.first, self.end)}
        self.counter = 0

    def beginning_offsets(self, topics_partition):
        return {topics_partition[0]: self.first}

    def end_offsets(self, topics_partition):
        return {topics_partition[0]: self.end}

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
            m = self.messages[self.counter]
        except KeyError:
            raise StopIteration
        else:
            self.counter += 1
            return m

