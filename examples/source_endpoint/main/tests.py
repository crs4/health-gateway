# -*- coding: utf-8 -*-

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


from __future__ import unicode_literals

import json

import os
import re
from django.test import TestCase, client
from hgw_common.utils import MockRequestHandler, start_mock_server, get_free_port
from mock import patch

CORRECT_CHANNEL_ID = 'correct'
WRONG_CHANNEL_ID = 'wrong'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CONSENT_MANAGER_PORT = get_free_port()
CONSENT_MANAGER_URI = 'http://localhost:{}'.format(CONSENT_MANAGER_PORT)


class MockConsentManagerRequestHandler(MockRequestHandler):
    CONSENT_PATTERN = re.compile(r'/v1/consents/{}'.format(CORRECT_CHANNEL_ID))
    WRONG_CONSENT_PATTERN = re.compile(r'/v1/consents/{}'.format(WRONG_CHANNEL_ID))

    def do_GET(self):
        if re.search(self.CONSENT_PATTERN, self.path):

            payload = {
                'status': 'AC',
            }

        elif re.search(self.WRONG_CONSENT_PATTERN, self.path):
            payload = {
                "status": "PE"
            }
        else:
            payload = {}
        return self._send_response(payload)


class TestAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestAPI, cls).setUpClass()
        start_mock_server('certs', MockConsentManagerRequestHandler, CONSENT_MANAGER_PORT)

    def __init__(self, *args, **kwargs):
        super(TestAPI, self).__init__(*args, **kwargs)
        self.client = client.Client()
        payload = [{'clinical_domain': 'Laboratory',
                    'filters': [{'includes': 'immunochemistry', 'excludes': 'HDL'}]},
                   {'clinical_domain': 'Radiology',
                    'filters': [{'includes': 'Tomography', 'excludes': 'Radiology'}]},
                   {'clinical_domain': 'Emergency',
                    'filters': [{'includes': '', 'excludes': ''}]},
                   {'clinical_domain': 'Prescription',
                    'filters': [{'includes': '', 'excludes': ''}]}]

        profile = {
            'code': 'PROF002',
            'version': 'hgw.document.profile.v0',
            'start_time_validity': '2017-06-23T10:13:39Z',
            'end_time_validity': '2018-06-23T23:59:59Z',
            'payload': json.dumps(payload)
        }

        self.data = {
            'person_identifier': 'some_guy',
            'dest_public_key': 'some_string',
            'channel_id': WRONG_CHANNEL_ID,
            'profile': profile
        }

    @patch('main.serializers.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_create_connector_invalid_consent_status(self):
        self.data['channel_id'] = WRONG_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=self.data, content_type='application/json')
        self.assertEquals(res.status_code, 400)

    @patch('main.serializers.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_create_connector_valid_consent_status(self):
        self.data['channel_id'] = CORRECT_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=json.dumps(self.data), content_type='application/json')
        self.assertEquals(res.status_code, 201)
