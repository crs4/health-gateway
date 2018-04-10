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
import os
import sys

from django.test import TestCase, client
from mock import patch
from oauth2_provider.settings import oauth2_settings

from hgw_backend import settings
from hgw_backend.models import OAuth2Authentication, RESTClient
from hgw_common.cipher import MAGIC_BYTES
from hgw_common.utils.test import start_mock_server, MockKafkaConsumer, MockMessage
from test.utils import MockSourceEnpointHandler

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CERT_SOURCE_PORT = 40000
OAUTH_SOURCE_PORT = 40001

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/management/')))

from commands.kafka_consumer import Command


class TestHGWBackendAPI(TestCase):
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(TestHGWBackendAPI, cls).setUpClass()
        start_mock_server('certs', MockSourceEnpointHandler, OAUTH_SOURCE_PORT)
        start_mock_server('certs', MockSourceEnpointHandler, CERT_SOURCE_PORT)

    def setUp(self):
        self.messages_source_oauth = []
        self.client = client.Client()
        payload = [{'clinical_domain': 'Laboratory',
                    'filters': [{'includes': 'immunochemistry', 'excludes': 'HDL'}]},
                   {'clinical_domain': 'Radiology',
                    'filters': [{'includes': 'Tomography', 'excludes': 'Radiology'}]},
                   {'clinical_domain': 'Emergency',
                    'filters': [{'includes': '', 'excludes': ''}]},
                   {'clinical_domain': 'Prescription',
                    'filters': [{'includes': '', 'excludes': ''}]}]
        self.profile_data = {
            'code': 'PROF002',
            'version': 'hgw.document.profile.v0',
            'start_time_validity': '2017-06-23T10:13:39Z',
            'end_time_validity': '2018-06-23T23:59:59Z',
            'payload': json.dumps(payload)
        }
        with open(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/fixtures/test_data.json'))) as fixtures_file:
            self.fixtures = json.load(fixtures_file)

    @staticmethod
    def set_mock_kafka_consumer(mock_kc_klass):
        with open(os.path.join(os.path.dirname(__file__), './channels_data.json')) as cd:
            messages = json.load(cd)
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = len(messages)
        mock_kc_klass.MESSAGES = {i: MockMessage(key="09876".encode('utf-8'), offset=i,
                                                 topic='vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj'.encode('utf-8'),
                                                 value=json.dumps(v).encode('utf-8')) for i, v in enumerate(messages)}

    @staticmethod
    def _get_client_data(client_index=0):
        app = RESTClient.objects.all()[client_index]
        return app.client_id, app.client_secret

    def _call_token_creation(self, data):
        return self.client.post('/oauth2/token/', data=data)

    def _get_oauth_token(self, client_index=0):
        c_id, c_secret = self._get_client_data(client_index)
        params = {
            'grant_type': 'client_credentials',
            'client_id': c_id,
            'client_secret': c_secret
        }
        res = self._call_token_creation(params)
        return res.json()

    def _get_oauth_header(self, client_index=0):
        res = self._get_oauth_token(client_index)
        return {'Authorization': 'Bearer {}'.format(res['access_token'])}

    def test_create_token(self):
        """
        Tests correct oauth2 token creation
        """
        res = self._get_oauth_token(client_index=0)
        for k in ['access_token', 'token_type', 'expires_in', 'scope']:
            self.assertIn(k, res)
        self.assertEquals(res['token_type'], 'Bearer')
        self.assertIn(res['scope'], settings.DEFAULT_SCOPES)
        self.assertEquals(res['expires_in'], oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

    def test_create_token_wrong_client(self):
        """
        Tests failed token creation due to wrong client_id or client_secret
        """
        for client_data in [('wrong', self._get_client_data(0)[1]), (self._get_client_data(0)[0], 'wrong')]:
            wrong_client_data = {
                'grant_type': 'client_credentials',
                'client_id': client_data[0],
                'client_secret': client_data[1]
            }
            res = self._call_token_creation(wrong_client_data)
            self.assertEquals(res.status_code, 401)
            self.assertEquals(res.json(), {'error': 'invalid_client'})

    def test_create_token_wrong_grant_type(self):
        """
        Tests failed token creation due to wrong grant_type
        """
        client_id, client_secret = self._get_client_data(0)
        wrong_client_data = {
            'grant_type': 'wrong',
            'client_id': client_id,
            'client_secret': client_secret
        }
        res = self._call_token_creation(wrong_client_data)
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.json(), {'error': 'unsupported_grant_type'})

    def test_create_token_invalid_scope(self):
        """
        Tests failed token creation due to wrong grant_type
        """
        client_id, client_secret = self._get_client_data(0)
        wrong_client_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'wrong'
        }
        res = self._call_token_creation(wrong_client_data)
        self.assertEquals(res.status_code, 401)
        self.assertEquals(res.json(), {'error': 'invalid_scope'})

    def test_get_sources(self):
        res = self.client.get('/v1/sources/')
        json_res = json.loads(res.content.decode())
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'application/json')
        self.assertEquals(len(json_res), 2)

    # def test_add_connector(self):
    #     with patch('commands.kafka_consumer.KafkaConsumer', MockKafkaConsumer):
    #         self.set_mock_kafka_consumer(MockKafkaConsumer)
    #         self.assertIsNone(OAuth2Authentication.objects.get().token)
    #         res = Command().handle()
    #         self.assertIsNotNone(OAuth2Authentication.objects.get().token)

    @patch('hgw_backend.views.KafkaProducer')
    def test_send_message(self, mock_kp):
        channel_id = 'channel_id'
        payload = '{}encrypted_paylaod'.format(MAGIC_BYTES.decode('utf-8'))

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()
        source_id = RESTClient.objects.get().source.source_id
        res = self.client.post('/v1/messages/', json.dumps(data), content_type='application/json', **oauth2_header)
        self.assertEquals(mock_kp().send.call_args_list[0][0][0], source_id)
        self.assertEquals(mock_kp().send.call_args_list[0][0][1], data['channel_id'].encode('utf-8'))
        self.assertEquals(mock_kp().send.call_args_list[0][0][2], data['payload'].encode('utf-8'))
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res.json(), {})

    def test_send_message_missing_paramaters(self):
        channel_id = 'channel_id'
        payload = 'encrypted_payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()
        for k, v in data.items():
            params = {k: v}
            res = self.client.post('/v1/messages/', data=json.dumps(params), content_type='application/json', **oauth2_header)
            self.assertEquals(res.status_code, 400)
            self.assertEquals(res.json(), {'error': 'missing_parameters'})

    def test_send_message_not_encrypted(self):
        channel_id = 'channel_id'
        payload = 'not_encrypted_payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        res = self.client.post('/v1/messages/', data=json.dumps(data), content_type='application/json', **oauth2_header)
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.json(), {'error': 'not_encrypted_payload'})

    def test_send_message_unauthorized(self):
        channel_id = 'channel_id'
        payload = 'payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()
        oauth2_header['Authorization'] = 'Bearer wrong'

        res = self.client.post('/v1/messages/', json.dumps(data), content_type='application/json', **oauth2_header)
        self.assertEquals(res.status_code, 401)
        self.assertEquals(res.json(), {'detail': 'Authentication credentials were not provided.'})

    def test_send_message_server_error(self):
        channel_id = 'channel_id'
        payload = '{}encrypted_paylaod'.format(MAGIC_BYTES.decode('utf-8'))

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        res = self.client.post('/v1/messages/', json.dumps(data), content_type='application/json', **oauth2_header)

        self.assertEquals(res.status_code, 500)
        self.assertEquals(res.json(), {'error': 'cannot_send_message'})

