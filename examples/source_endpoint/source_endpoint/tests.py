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

# from oauth2_provider.models import get_application_model
import time

from django.test import TestCase, client
from oauth2_provider.models import get_application_model
from oauth2_provider.settings import oauth2_settings

from hgw_common.utils.test import MockRequestHandler, start_mock_server, get_free_port
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


class TestSourceEndpointAPI(TestCase):
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(TestSourceEndpointAPI, cls).setUpClass()
        start_mock_server('certs', MockConsentManagerRequestHandler, CONSENT_MANAGER_PORT)

    def __init__(self, *args, **kwargs):
        super(TestSourceEndpointAPI, self).__init__(*args, **kwargs)
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
            'start_time_validity': '2017-06-23T10:13:39+02:00',
            'end_time_validity': '2018-06-23T23:59:59+02:00',
            'payload': json.dumps(payload)
        }

        self.data = {
            'person_identifier': 'some_guy',
            'dest_public_key': 'some_string',
            'channel_id': WRONG_CHANNEL_ID,
            'profile': profile
        }

    @staticmethod
    def _get_client_data(client_index):
        app = get_application_model().objects.all()[client_index]
        return app.client_id, app.client_secret

    def _get_oauth_token(self, client_index=0, scopes=oauth2_settings.DEFAULT_SCOPES):
        c_id, c_secret = self._get_client_data(client_index)
        params = {
            'grant_type': 'client_credentials',
            'client_id': c_id,
            'client_secret': c_secret,
            'scope': ' '.join(scopes)
        }
        res = self.client.post('/oauth2/token/', data=params)
        return res.json()

    def _get_oauth_header(self, client_index=0, scopes=oauth2_settings.DEFAULT_SCOPES):
        res = self._get_oauth_token(client_index, scopes)
        access_token = res['access_token']
        return {'Authorization': 'Bearer {}'.format(access_token)}

    def test_get_oauth_header(self):
        token = self._get_oauth_header()
        self.assertIn('Authorization', token)

    def test_unauthorized(self):
        res = self.client.get('/v1/connectors/')
        self.assertEquals(res.status_code, 401)
        self.data['channel_id'] = CORRECT_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=json.dumps(self.data), content_type='application/json')
        self.assertEquals(res.status_code, 401)

        wrong_header = {'Authorization': 'Bearer fake'}
        res = self.client.get('/v1/connectors/', **wrong_header)
        self.assertEquals(res.status_code, 401)
        self.data['channel_id'] = CORRECT_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=json.dumps(self.data), content_type='application/json',
                               **wrong_header)
        self.assertEquals(res.status_code, 401)

    def test_token_expires(self):
        oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS = 2
        token = self._get_oauth_token()
        self.assertEquals(token['expires_in'], 2)
        time.sleep(2)
        res = self.client.get('/v1/connectors/', Authorization='Bearer {}'.format(token['access_token']))
        print(res.content)

    def test_forbidden(self):
        oauth2_header = self._get_oauth_header(scopes=['write'])
        res = self.client.get('/v1/connectors/', **oauth2_header)
        self.assertEquals(res.status_code, 403)

        oauth2_header = self._get_oauth_header(scopes=['read'])
        self.data['channel_id'] = CORRECT_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=json.dumps(self.data), content_type='application/json',
                               **oauth2_header)
        self.assertEquals(res.status_code, 403)

    def test_get_connectors(self):
        oauth2_header = self._get_oauth_header()
        res = self.client.get('/v1/connectors/', **oauth2_header)
        self.assertEquals(res.status_code, 200)

    @patch('source_endpoint.serializers.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_create_connector_invalid_consent_status(self):
        oauth2_header = self._get_oauth_header()
        self.data['channel_id'] = WRONG_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=self.data, content_type='application/json',
                               auth=oauth2_header)
        self.assertEquals(res.status_code, 400)

    @patch('source_endpoint.serializers.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_create_connector_valid_consent_status(self):
        oauth2_header = self._get_oauth_header()
        self.data['channel_id'] = CORRECT_CHANNEL_ID
        res = self.client.post('/v1/connectors/', data=json.dumps(self.data), content_type='application/json',
                               **oauth2_header)
        self.assertEquals(res.status_code, 201)
