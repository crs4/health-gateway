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

from hgw_common.utils.test import MockRequestHandler
from hgw_frontend.models import FlowRequest
from hgw_frontend.settings import HGW_BACKEND_CLIENT_ID, CONSENT_MANAGER_CLIENT_ID

from . import CORRECT_CONSENT_ID, WRONG_CONFIRM_ID, CORRECT_CONFIRM_ID, WRONG_CONSENT_ID, \
    TEST_PERSON1_ID, CORRECT_CONSENT_ID2, WRONG_CONSENT_ID2, CORRECT_CONFIRM_ID2, WRONG_CONFIRM_ID2

SOURCES_DATA = [
    {
        'source_id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
        'name': 'source_1',
        'profile': {
            'code': 'PROF_001',
            'version': 'v0',
            'payload': '[{"clinical_domain": "Laboratory"}]'}
    }, {
        'source_id': 'TptQ5kPSNliFIOYyAB1tV5mt2PvwXsaS',
        'name': 'oauth2_source',
        'profile': {
            'code': 'PROF_002',
            'version': 'v0',
            'payload': '[{"clinical_domain": "Radiology"}]'
        }
    }]


class MockConsentManagerRequestHandler(MockRequestHandler):
    """
    Consent manager mockup
    """

    CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(CORRECT_CONSENT_ID, CORRECT_CONSENT_ID2))
    WRONG_CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(WRONG_CONSENT_ID, WRONG_CONSENT_ID2))
    CONSENTS_PATTERN = re.compile(r'/v1/consents/')
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def do_POST(self):
        if self._path_match(self.CONSENTS_PATTERN):
            # Mock the consent creation. The behaviour is: if the person is TEST_PERSON1_ID the consent is created.
            # Otherwise the consent is not created and a 400 status code is returned
            consent_data = self._json_data()

            if TEST_PERSON1_ID == consent_data['person_id']:
                payload = {"consent_id": get_random_string(32),
                           "confirm_id": get_random_string(32),
                           "status": "PE"}
                status_code = 201
            else:
                payload = []
                status_code = 400
        elif self._path_match(self.OAUTH2_PATTERN):
            client_data = self._content_data()
            if CONSENT_MANAGER_CLIENT_ID in client_data:
                payload = {'access_token': get_random_string(30),
                           'token_type': 'Bearer',
                           'expires_in': 36000,
                           'expires_at': 1499976952.401335,
                           'scope': ['read', 'write']}
                status_code = 201
            elif 'wrong_client_id' in client_data:
                status_code = 401
                payload = {'error': 'invalid_client'}
            else:
                status_code = 400
                payload = {'error': 'invalid_grant_type'}
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
                'person_id': TEST_PERSON1_ID,
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
    SINGLE_SOURCE_PATTERN = re.compile(r'/v1/sources/(\w+)')
    SOURCES_PATTERN = re.compile(r'/v1/sources/$')
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def do_POST(self):
        if self._path_match(self.OAUTH2_PATTERN):
            client_data = self._content_data()
            if HGW_BACKEND_CLIENT_ID in client_data:
                payload = {'access_token': get_random_string(30),
                           'token_type': 'Bearer',
                           'expires_in': 36000,
                           'expires_at': 1499976952.401335,
                           'scope': ['read', 'write']}
                status_code = 201
            elif 'wrong_client_id' in client_data:
                status_code = 401
                payload = {'error': 'invalid_client'}
            else:
                status_code = 400
                payload = {'error': 'invalid_grant_type'}
        else:
            payload = ""
            status_code = 400
        print(payload, status_code)
        return self._send_response(payload, status_code)

    def do_GET(self):

        if self._path_match(self.SOURCES_PATTERN):
            payload = SOURCES_DATA
        else:
            match = self._path_match(self.SINGLE_SOURCE_PATTERN)
            if match:
                source = list(filter(lambda item: item['source_id'] == match.groups()[0], SOURCES_DATA))
                payload = source[0] if len(source) == 1 else None
            else:
                payload = {}
        return self._send_response(payload)
