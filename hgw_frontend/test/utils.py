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

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.utils.crypto import get_random_string
from mock.mock import Mock, NonCallableMock

from hgw_common.utils.mocks import MockRequestHandler
from hgw_frontend.models import FlowRequest
from hgw_frontend.settings import (CONSENT_MANAGER_CLIENT_ID,
                                   HGW_BACKEND_CLIENT_ID)

from . import (CORRECT_CONFIRM_ID, CORRECT_CONFIRM_ID2, CORRECT_CONSENT_ID_AC,
               CORRECT_CONSENT_ID_CR, PERSON_ID, PROFILES_DATA, SOURCES_DATA, ABORTED_CONSENT_ID, ABORTED_CONSENT_ID2,
               WRONG_CONFIRM_ID, WRONG_CONFIRM_ID2, WRONG_CONSENT_ID,
               WRONG_CONSENT_ID2, ABORTED_CONFIRM_ID, ABORTED_CONFIRM_ID2)


class MockConsentManagerRequestHandler(MockRequestHandler):
    """
    Consent manager mockup
    """

    CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(CORRECT_CONSENT_ID_AC, CORRECT_CONSENT_ID_CR))
    ABORTED_CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(ABORTED_CONSENT_ID, ABORTED_CONSENT_ID2))
    WRONG_CONSENT_PATTERN = re.compile(r'/v1/consents/({}|{})/'.format(WRONG_CONSENT_ID, WRONG_CONSENT_ID2))
    CONSENTS_PATTERN = re.compile(r'/v1/consents/')
    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')

    def do_POST(self):
        if self._path_match(self.CONSENTS_PATTERN):
            # Mock the consent creation. The behaviour is: if the person is PERSON_ID the consent is created.
            # Otherwise the consent is not created and a 400 status code is returned
            consent_data = self._json_data()

            if PERSON_ID == consent_data['person_id']:
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
            confirm_id = CORRECT_CONFIRM_ID if consent_search.groups()[0] == CORRECT_CONSENT_ID_AC \
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
                'person_id': PERSON_ID,
                'status': FlowRequest.ACTIVE,
                'consent_id': consent_id,
                'confirm_id': confirm_id,
                'start_validity': '2017-10-23T10:00:54.123000+02:00',
                'expire_validity': '2018-10-23T10:00:00+02:00',
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
                consent_search = re.search(self.ABORTED_CONSENT_PATTERN, self.path)
                if consent_search:
                    consent_id = consent_search.groups()[0]
                    confirm_id = ABORTED_CONFIRM_ID if consent_search.groups()[0] == ABORTED_CONSENT_ID else \
                        ABORTED_CONFIRM_ID2
                    payload = {
                        "consent_id": consent_id,
                        "confirm_id": confirm_id,
                        "status": "NV"
                    }
                else:
                    payload = {}
        return self._send_response(payload)


class MockBackendRequestHandler(MockRequestHandler):
    SINGLE_SOURCE_PATTERN = re.compile(r'/v1/sources/(\w+)')
    SOURCES_PATTERN = re.compile(r'/v1/sources/$')
    PROFILES_PATTERN = re.compile(r'/v1/profiles/$')
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
        return self._send_response(payload, status_code)

    def do_GET(self):

        if self._path_match(self.SOURCES_PATTERN):
            payload = SOURCES_DATA
        elif self._path_match(self.PROFILES_PATTERN):
            payload = PROFILES_DATA
        else:
            match = self._path_match(self.SINGLE_SOURCE_PATTERN)
            if match:
                source = list(filter(lambda item: item['source_id'] == match.groups()[0], SOURCES_DATA))
                payload = source[0] if len(source) == 1 else None
            else:
                payload = {}
        return self._send_response(payload)


def get_db_error_mock():
    mock = NonCallableMock()
    mock.DoesNotExist = ObjectDoesNotExist
    mock.objects = NonCallableMock()
    mock.objects.all = Mock(side_effect=DatabaseError)
    mock.objects.filter = Mock(side_effect=DatabaseError)
    mock.objects.get = Mock(side_effect=DatabaseError)
    mock.objects.create = Mock(side_effect=DatabaseError)
    mock.objects.get_or_create = Mock(side_effect=DatabaseError)
    return mock
