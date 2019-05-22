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
import logging
import os
import sys

from Cryptodome.PublicKey import RSA
from django.test import TestCase, client
from kafka.errors import (KafkaError, KafkaTimeoutError, NoBrokersAvailable,
                          TopicAuthorizationFailedError)
from mock import MagicMock, patch
from oauth2_provider.settings import oauth2_settings

from _ssl import SSLError

from hgw_backend import settings
from hgw_backend.models import RESTClient
from hgw_backend.serializers import SourceSerializer
from hgw_common.cipher import Cipher

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/management/')))

DEST_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\n' \
                  'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp4TF/ETwYKG+eAYZz3wo\n' \
                  '8IYqrPIlQyz1/xljqDD162ZAYJLCYeCfs9yczcazC8keWzGd5/tn4TF6II0oINKh\n' \
                  'kCYLqTIVkVGC7/tgH5UEe/XG1trRZfMqwl1hEvZV+/zanV0cl7IjTR9ajb1TwwQY\n' \
                  'MOjcaaBZj+xfD884pwogWkcSGTEODGfoVACHjEXHs+oVriHqs4iggiiMYbO7TBjg\n' \
                  'Be9p7ZDHSVBbXtQ3XuGKnxs9MTLIh5L9jxSRb9CgAtv8ubhzs2vpnHrRVkRoddrk\n' \
                  '8YHKRryYcVDHVLAGc4srceXU7zrwAMbjS7msh/LK88ZDUWfIZKZvbV0L+/topvzd\n' \
                  'XQIDAQAB\n' \
                  '-----END PUBLIC KEY-----'

SOURCE_ENDPOINT_CLIENT_NAME = 'SOURCE MOCK'
HGW_FRONTEND_CLIENT_NAME = 'HGW FRONTEND'


def _get_client_data(client_name=SOURCE_ENDPOINT_CLIENT_NAME):
    app = RESTClient.objects.get(name=client_name)
    return app.client_id, app.client_secret

class GenericTestCase(TestCase):
    """
    Generic test case class
    """

    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(GenericTestCase, cls).setUpClass()
        logger = logging.getLogger('hgw_backend')
        logger.setLevel(logging.ERROR)

    def setUp(self):
        self.maxDiff = None
        self.client = client.Client()

    def _call_token_creation(self, data):
        return self.client.post('/oauth2/token/', data=data)

    def _get_oauth_token(self, client_name=SOURCE_ENDPOINT_CLIENT_NAME):
        c_id, c_secret = _get_client_data(client_name)
        params = {
            'grant_type': 'client_credentials',
            'client_id': c_id,
            'client_secret': c_secret
        }
        res = self._call_token_creation(params)
        return res.json()

    def _get_oauth_header(self, client_name=SOURCE_ENDPOINT_CLIENT_NAME):
        res = self._get_oauth_token(client_name)
        return {'Authorization': 'Bearer {}'.format(res['access_token'])}


class TestOAuth2API(GenericTestCase):
    """
    Tests for oauth2 provider api
    """

    def test_create_token(self):
        """
        Tests correct oauth2 token creation
        """
        res = self._get_oauth_token(client_name=SOURCE_ENDPOINT_CLIENT_NAME)
        for k in ['access_token', 'token_type', 'expires_in', 'scope']:
            self.assertIn(k, res)
        self.assertEqual(res['token_type'], 'Bearer')
        self.assertIn(res['scope'], settings.DEFAULT_SCOPES)
        self.assertEqual(res['expires_in'], oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

    def test_create_token_wrong_client(self):
        """
        Tests failed token creation due to wrong client_id or client_secret
        """
        for client_data in [('wrong', _get_client_data(SOURCE_ENDPOINT_CLIENT_NAME)[1]), 
                            (_get_client_data(SOURCE_ENDPOINT_CLIENT_NAME)[0], 'wrong')]:
            wrong_client_data = {
                'grant_type': 'client_credentials',
                'client_id': client_data[0],
                'client_secret': client_data[1]
            }
            res = self._call_token_creation(wrong_client_data)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json(), {'error': 'invalid_client'})

    def test_create_token_wrong_grant_type(self):
        """
        Tests failed token creation due to wrong grant_type
        """
        client_id, client_secret = _get_client_data(SOURCE_ENDPOINT_CLIENT_NAME)
        wrong_client_data = {
            'grant_type': 'wrong',
            'client_id': client_id,
            'client_secret': client_secret
        }
        res = self._call_token_creation(wrong_client_data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'error': 'unsupported_grant_type'})

    def test_create_token_invalid_scope(self):
        """
        Tests failed token creation due to wrong grant_type
        """
        client_id, client_secret = _get_client_data(SOURCE_ENDPOINT_CLIENT_NAME)
        wrong_client_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'wrong'
        }
        res = self._call_token_creation(wrong_client_data)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'error': 'invalid_scope'})


class TestSourcesAPI(GenericTestCase):
    """
    Tests /v1/sources API
    """
    @classmethod
    def setUpClass(cls):
        super(TestSourcesAPI, cls).setUpClass()

    def setUp(self):
        super(TestSourcesAPI, self).setUp()
        with open(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/fixtures/test_data.json'))) as fixtures_file:
            self.fixtures = json.load(fixtures_file)
        self.profiles = [obj['fields'] for obj in self.fixtures if obj['model'] == 'hgw_common.profile']
        self.sources = [obj['fields'] for obj in self.fixtures if obj['model'] == 'hgw_backend.source']

    def test_get_sources(self):
        """
        Test getting sources
        """
        oauth2_header = self._get_oauth_header(client_name=HGW_FRONTEND_CLIENT_NAME)

        res = self.client.get('/v1/sources/', **oauth2_header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/json')
        self.assertEqual(len(res.json()), 2)

        for i, s in enumerate(self.sources):
            ret_source = res.json()[i]
            req_source = {k: s[k] for k in SourceSerializer.Meta.fields}
            req_source['profile'] = self.profiles[int(s['profile'] - 1)]
            self.assertEqual(ret_source, req_source)

    def test_get_sources_forbidden(self):
        """
        Test error getting sources using a client without the correct scope
        """
        oauth2_header = self._get_oauth_header(client_name=SOURCE_ENDPOINT_CLIENT_NAME)

        res = self.client.get('/v1/sources/', **oauth2_header)
        self.assertEqual(res.status_code, 403)

    def test_get_sources_not_authorized(self):
        """
        Test getting sources
        """
        res = self.client.get('/v1/sources/')
        self.assertEqual(res.status_code, 401)

    def test_get_profiles(self):
        """
        Test getting profiles
        """
        oauth2_header = self._get_oauth_header(client_name=HGW_FRONTEND_CLIENT_NAME)

        res = self.client.get('/v1/profiles/', **oauth2_header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/json')
        self.assertEqual(len(res.json()), 2)
        for p in res.json():
            self.assertEqual(len(p['sources']), 1)

    def test_get_profiles_forbidden(self):
        """
        Test error getting profiles using a client without the correct scope
        """
        oauth2_header = self._get_oauth_header(client_name=SOURCE_ENDPOINT_CLIENT_NAME)

        res = self.client.get('/v1/profiles/', **oauth2_header)
        self.assertEqual(res.status_code, 403)

    def test_get_profiles_not_authorized(self):
        """
        Test getting profiles
        """
        res = self.client.get('/v1/profiles/')
        self.assertEqual(res.status_code, 401)


class TestMessagesAPI(GenericTestCase):

    def setUp(self):
        self.encrypter = Cipher(public_key=RSA.importKey(DEST_PUBLIC_KEY))

    def test_send_message_bytes(self):
        """
        Tests sending correct message using encryption and bytes object
        :return:
        """
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')
        data = {
            'channel_id': channel_id,
            'payload': payload
        }

        oauth2_header = self._get_oauth_header()
        source_id = RESTClient.objects.get(pk=1).source.source_id
        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            res = self.client.post('/v1/messages/', data=data, **oauth2_header)
            self.assertEqual(MockKP().send.call_args_list[0][0][0], source_id)
            self.assertEqual(MockKP().send.call_args_list[0][1]['key'], data['channel_id'].encode('utf-8'))
            self.assertEqual(MockKP().send.call_args_list[0][1]['value'], data['payload'])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {})

    def test_send_message_string(self):
        """
        Tests send correct message using a string. This is tested for example for java clients
        :return:
        """
        channel_id = 'channel_id'
        payload = '\u07fbpayload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }

        oauth2_header = self._get_oauth_header()
        source_id = RESTClient.objects.get(pk=1).source.source_id
        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            res = self.client.post('/v1/messages/', data=data, **oauth2_header)
            self.assertEqual(MockKP().send.call_args_list[0][0][0], source_id)
            self.assertEqual(MockKP().send.call_args_list[0][1]['key'], data['channel_id'].encode('utf-8'))
            self.assertEqual(MockKP().send.call_args_list[0][1]['value'], data['payload'].encode('utf-8'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {})

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
            res = self.client.post('/v1/messages/', data=params,
                                   **oauth2_header)
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json(), {'error': 'missing_parameters'})

    def test_send_message_not_encrypted_string(self):
        channel_id = 'channel_id'
        payload = 'not_encrypted_payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'error': 'not_encrypted_payload'})

    def test_send_message_not_encrypted_bytes(self):
        channel_id = 'channel_id'
        payload = b'not_encrypted_payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'error': 'not_encrypted_payload'})

    def test_send_message_unauthorized(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header(SOURCE_ENDPOINT_CLIENT_NAME)
        oauth2_header['Authorization'] = 'Bearer wrong'

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'detail': 'Authentication credentials were not provided.'})

    def test_send_message_forbidden(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header(HGW_FRONTEND_CLIENT_NAME)

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'detail': 'You do not have permission to perform this action.'})

    def test_send_message_no_broker_available(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            MockKP.side_effect = NoBrokersAvailable
            res = self.client.post('/v1/messages/', data, **oauth2_header)

            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_wrong_broker_credentials(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            MockKP.side_effect = SSLError
            res = self.client.post('/v1/messages/', data=data, **oauth2_header)

            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_missing_topic(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            MockKP().send.side_effect = KafkaTimeoutError
            res = self.client.post('/v1/messages/', data, **oauth2_header)

            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_no_authorization(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            mock_future_record_metadata = MagicMock()
            mock_future_record_metadata().get.side_effect = TopicAuthorizationFailedError
            MockKP().send.side_effect = mock_future_record_metadata

            res = self.client.post('/v1/messages/', data=data, **oauth2_header)

            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_generic_kafka_error(self):
        channel_id = 'channel_id'
        payload = self.encrypter.encrypt('payload')
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            mock_future_record_metadata = MagicMock()
            mock_future_record_metadata().get.side_effect = KafkaError
            MockKP().send.side_effect = mock_future_record_metadata

            res = self.client.post('/v1/messages/', data=data, **oauth2_header)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'error': 'cannot_send_message'})
