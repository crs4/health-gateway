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
from _ssl import SSLError
from datetime import datetime, timedelta

from Cryptodome.PublicKey import RSA
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, client
from kafka.errors import KafkaTimeoutError, NoBrokersAvailable, TopicAuthorizationFailedError, KafkaError
from mock import patch, MagicMock
from oauth2_provider.settings import oauth2_settings

from hgw_backend import settings
from hgw_backend.models import RESTClient, OAuth2Authentication, Source, AccessToken
from hgw_backend.serializers import SourceSerializer
from hgw_common.cipher import Cipher
from hgw_common.utils.mocks import start_mock_server, MockMessage
from test.utils import MockSourceEndpointHandler

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CERT_SOURCE_PORT = 40000
OAUTH_SOURCE_PORT = 40001

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/management/')))

PROFILE = {
    'code': 'PROF001',
    'version': 'hgw.document.profile.v0',
    'payload': '{\'domain\': \'Laboratory\'}'
}

PERSON_ID = 'AAAABBBBCCCCDDDD'
DEST_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\n' \
                  'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp4TF/ETwYKG+eAYZz3wo\n' \
                  '8IYqrPIlQyz1/xljqDD162ZAYJLCYeCfs9yczcazC8keWzGd5/tn4TF6II0oINKh\n' \
                  'kCYLqTIVkVGC7/tgH5UEe/XG1trRZfMqwl1hEvZV+/zanV0cl7IjTR9ajb1TwwQY\n' \
                  'MOjcaaBZj+xfD884pwogWkcSGTEODGfoVACHjEXHs+oVriHqs4iggiiMYbO7TBjg\n' \
                  'Be9p7ZDHSVBbXtQ3XuGKnxs9MTLIh5L9jxSRb9CgAtv8ubhzs2vpnHrRVkRoddrk\n' \
                  '8YHKRryYcVDHVLAGc4srceXU7zrwAMbjS7msh/LK88ZDUWfIZKZvbV0L+/topvzd\n' \
                  'XQIDAQAB\n' \
                  '-----END PUBLIC KEY-----'

CHANNEL_MESSAGE = {
    'channel_id': 'KKa8QqqTBGePJStJpQMbspEvvV4LJJCY',
    'source_id': 'LD2j7v35BvUlzWDe8G89JGzz4SOincB7',
    'destination': {
        'destination_id': 'random_dest_id',
        'kafka_public_key': DEST_PUBLIC_KEY
    },
    'profile': PROFILE,
    'person_id': PERSON_ID
}

CONNECTOR = {
    'profile': PROFILE,
    'person_identifier': PERSON_ID,
    'dest_public_key': DEST_PUBLIC_KEY,
    'channel_id': CHANNEL_MESSAGE['channel_id'],
    'start_validity': '2017-10-23T10:00:54.123000+02:00',
    'expire_validity': '2018-10-23T10:00:00+02:00',
}


class TestHGWBackendAPI(TestCase):
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(TestHGWBackendAPI, cls).setUpClass()
        logger = logging.getLogger('hgw_backend')
        logger.setLevel(logging.ERROR)
        start_mock_server('certs', MockSourceEndpointHandler, OAUTH_SOURCE_PORT)
        start_mock_server('certs', MockSourceEndpointHandler, CERT_SOURCE_PORT)

    def setUp(self):
        self.maxDiff = None
        self.messages_source_oauth = []
        self.client = client.Client()
        with open(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/fixtures/test_data.json'))) as fixtures_file:
            self.fixtures = json.load(fixtures_file)
        self.profiles = [obj['fields'] for obj in self.fixtures if obj['model'] == 'hgw_common.profile']
        self.sources = [obj['fields'] for obj in self.fixtures if obj['model'] == 'hgw_backend.source']
        # print(self.sources)
        # self.profiles_with_source = [p.update({'sources': self.sources[i]}) for i, p in enumerate(self.profiles)]
        # print(self.profiles_with_source)
        self.encypter = Cipher(public_key=RSA.importKey(DEST_PUBLIC_KEY))

    @staticmethod
    def configure_mock_kafka_consumer(mock_kc_klass, n_messages=1):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = n_messages
        mock_kc_klass.MESSAGES = {i: MockMessage(key='09876'.encode('utf-8'), offset=i,
                                                 topic='vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj'.encode('utf-8'),
                                                 value=json.dumps(CHANNEL_MESSAGE).encode('utf-8')) for i in
                                  range(mock_kc_klass.FIRST, mock_kc_klass.END)}

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

    @staticmethod
    def _get_source_from_auth_obj(auth):
        ct = ContentType.objects.get_for_model(auth)
        return Source.objects.get(content_type=ct, object_id=auth.id)

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
        """
        Test getting sources
        """
        oauth2_header = self._get_oauth_header(client_index=1)

        res = self.client.get('/v1/sources/', **oauth2_header)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'application/json')
        self.assertEquals(len(res.json()), 2)

        for i, s in enumerate(self.sources):
            ret_source = res.json()[i]
            req_source = {k: s[k] for k in SourceSerializer.Meta.fields}
            req_source['profile'] = self.profiles[int(s['profile'] - 1)]
            self.assertEquals(ret_source, req_source)

    def test_get_sources_forbidden(self):
        """
        Test error getting sources using a client without the correct scope
        """
        oauth2_header = self._get_oauth_header(client_index=0)

        res = self.client.get('/v1/sources/', **oauth2_header)
        self.assertEquals(res.status_code, 403)

    def test_get_sources_not_authorized(self):
        """
        Test getting sources
        """
        res = self.client.get('/v1/sources/')
        self.assertEquals(res.status_code, 401)

    def test_get_profiles(self):
        """
        Test getting profiles
        """
        oauth2_header = self._get_oauth_header(client_index=1)

        res = self.client.get('/v1/profiles/', **oauth2_header)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'application/json')
        self.assertEquals(len(res.json()), 2)
        for p in res.json():
            self.assertEqual(len(p['sources']), 1)

    def test_get_profiles_forbidden(self):
        """
        Test error getting profiles using a client without the correct scope
        """
        oauth2_header = self._get_oauth_header(client_index=0)

        res = self.client.get('/v1/profiles/', **oauth2_header)
        self.assertEquals(res.status_code, 403)

    def test_get_profiles_not_authorized(self):
        """
        Test getting profiles
        """
        res = self.client.get('/v1/profiles/')
        self.assertEquals(res.status_code, 401)

    def test_create_connector_oauth2_source_fails_connector_unreachable(self):
        """
        Tests creation of new connector failure because of source endpoint unreachable whne calling /v1/connectors
        """
        auth = OAuth2Authentication.objects.first()
        source = self._get_source_from_auth_obj(auth)
        source.url = 'https://localhost:1000'
        res = auth.create_connector(source, CONNECTOR)
        self.assertIsNone(res)

    def test_create_connector_oauth2_source_fails_wrong_connector_url(self):
        """
        Tests creation of new connector failure because of wrong connector url
        """
        auth = OAuth2Authentication.objects.first()
        source = self._get_source_from_auth_obj(auth)
        source.url = 'http://localhost:40000/wrong_url/'
        res = auth.create_connector(source, CONNECTOR)
        self.assertIsNone(res)

    def test_create_connector_oauth2_source_fails_oauth2_unreachable(self):
        """
        Tests creation of new connector failure because of source enpoint unreachable when calling /oauth2/token
        """
        auth = OAuth2Authentication.objects.first()
        auth.token_url = 'https://localhost:1000/'
        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
        self.assertIsNone(res)

    def test_create_connector_oauth2_source_fails_wrong_oauth2_url(self):
        """
        Tests creation of new connector failure because of source enpoint wrong oauth2 url
        """
        auth = OAuth2Authentication.objects.first()
        auth.token_url = 'http://localhost:40000/wrong_url/'
        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
        self.assertIsNone(res)

    def test_create_connector_oauth2_source_fails_create_token_wrong_client_id(self):
        """
        Tests creation of new connector failure because of token creation failure in case of wrong client id
        """
        auth = OAuth2Authentication.objects.first()
        auth.client_id = "unkn"
        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
        self.assertIsNone(res)

    def test_create_connector_oauth2_source_fails_create_token_wrong_client_secret(self):
        """
        Tests creation of new connector failure because of token creation failure in case of wrong client secret
        """
        auth = OAuth2Authentication.objects.first()
        auth.client_secret = "unkn"
        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
        self.assertIsNone(res)

    def test_create_connector_oauth2_source_new_token(self):
        """
        Tests creation of new connector success when creating the first token
        """
        auth = OAuth2Authentication.objects.first()
        self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        token = AccessToken.objects.get(oauth2_authentication=auth)
        self.assertIsNotNone(token)
        self.assertIsNotNone(res)

    def test_create_connector_oauth2_source_refresh_token_token_expired_exception(self):
        """
        Tests token refresh in case of oauth2 library exception in case of oauth2 library raising TokenExpired exception
        """
        # Create an expired token in the db
        auth_obj = OAuth2Authentication.objects.first()
        AccessToken.objects.create(oauth2_authentication=auth_obj, access_token='something',
                                   token_type='Bearer', expires_in=3600, expires_at=datetime.now())

        auth = OAuth2Authentication.objects.first()
        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        token = AccessToken.objects.get(oauth2_authentication=auth)
        self.assertIsNotNone(token)
        self.assertNotEquals(AccessToken.objects.get(oauth2_authentication=auth_obj).access_token,
                             'expired')
        self.assertIsNotNone(res)

    def test_create_connector_oauth2_source_refresh_token_unauthorized_response(self):
        """
        Tests token refresh in case of unauthorized exception from server. When the server return 401
        the client still needs to refresh the token
        """
        # Create an expired token in the db
        auth = OAuth2Authentication.objects.first()
        AccessToken.objects.create(oauth2_authentication=auth, access_token='expired',
                                   token_type='Bearer', expires_in=3600,
                                   expires_at=datetime.now() - timedelta(seconds=3600))

        source = self._get_source_from_auth_obj(auth)
        res = auth.create_connector(source, CONNECTOR)
        token = AccessToken.objects.get(oauth2_authentication=auth)
        self.assertIsNotNone(token)
        self.assertNotEquals(AccessToken.objects.get(oauth2_authentication=auth).access_token,
                             'expired')

        self.assertIsNotNone(res)

    # def test_add_connector_oauth2_source(self):
    #     """
    #     Tests adding connector correctly in case of a Source Endpoint that support OAuth2 authentication
    #     """
    #     with patch('kafka_consumer.KafkaConsumer', MockKafkaConsumer):
    #         self.configure_mock_kafka_consumer(MockKafkaConsumer, 1)
    #         source_id = CHANNEL_MESSAGE['source_id']
    #         source = Source.objects.get(source_id=source_id)
    #         with self.assertRaises(AccessToken.DoesNotExist):
    #             AccessToken.objects.get(oauth2_authentication__id=source.object_id)
    #         Command().handle()
    #         token = AccessToken.objects.get(oauth2_authentication__id=source.object_id)
    #         self.assertIsNotNone(token)
    #
    # def test_add_connector_refresh_token(self):
    #     """
    #     Tests adding connector correctly
    #     """
    #     auth_obj = OAuth2Authentication.objects.first()
    #     AccessToken.objects.create(oauth2_authentication=auth_obj, access_token='expired',
    #                                token_type='Bearer', expires_in=3600, expires_at=datetime.now())
    #     with patch('kafka_consumer.KafkaConsumer', MockKafkaConsumer):
    #         self.configure_mock_kafka_consumer(MockKafkaConsumer, 1)
    #         Command().handle()
    #         self.assertNotEquals(AccessToken.objects.get(oauth2_authentication=auth_obj).access_token,
    #                              'expired')

    def test_send_message_bytes(self):
        """
        Tests sending correct message using encryption and bytes object
        :return:
        """
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')
        data = {
            'channel_id': channel_id,
            'payload': payload
        }

        oauth2_header = self._get_oauth_header()
        source_id = RESTClient.objects.get(pk=1).source.source_id
        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            res = self.client.post('/v1/messages/', data=data, **oauth2_header)

            self.assertEquals(MockKP().send.call_args_list[0][0][0], source_id)
            self.assertEquals(MockKP().send.call_args_list[0][1]['key'], data['channel_id'].encode('utf-8'))
            self.assertEquals(MockKP().send.call_args_list[0][1]['value'], data['payload'])
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res.json(), {})

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

            self.assertEquals(MockKP().send.call_args_list[0][0][0], source_id)
            self.assertEquals(MockKP().send.call_args_list[0][1]['key'], data['channel_id'].encode('utf-8'))
            self.assertEquals(MockKP().send.call_args_list[0][1]['value'], data['payload'].encode('utf-8'))
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
            res = self.client.post('/v1/messages/', data=params,
                                   **oauth2_header)
            self.assertEquals(res.status_code, 400)
            self.assertEquals(res.json(), {'error': 'missing_parameters'})

    def test_send_message_not_encrypted_string(self):
        channel_id = 'channel_id'
        payload = 'not_encrypted_payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.json(), {'error': 'not_encrypted_payload'})

    def test_send_message_not_encrypted_bytes(self):
        channel_id = 'channel_id'
        payload = b'not_encrypted_payload'
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.json(), {'error': 'not_encrypted_payload'})

    def test_send_message_unauthorized(self):
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')
        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()
        oauth2_header['Authorization'] = 'Bearer wrong'

        res = self.client.post('/v1/messages/', data=data, **oauth2_header)
        self.assertEquals(res.status_code, 401)
        self.assertEquals(res.json(), {'detail': 'Authentication credentials were not provided.'})

    def test_send_message_no_broker_available(self):
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            MockKP.side_effect = NoBrokersAvailable
            res = self.client.post('/v1/messages/', data, **oauth2_header)

            self.assertEquals(res.status_code, 500)
            self.assertEquals(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_wrong_broker_credentials(self):
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            MockKP.side_effect = SSLError
            res = self.client.post('/v1/messages/', data=data, **oauth2_header)

            self.assertEquals(res.status_code, 500)
            self.assertEquals(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_missing_topic(self):
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')

        data = {
            'channel_id': channel_id,
            'payload': payload
        }
        oauth2_header = self._get_oauth_header()

        with patch('hgw_backend.views.KafkaProducer') as MockKP:
            MockKP().send.side_effect = KafkaTimeoutError
            res = self.client.post('/v1/messages/', data, **oauth2_header)

            self.assertEquals(res.status_code, 500)
            self.assertEquals(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_no_authorization(self):
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')

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

            self.assertEquals(res.status_code, 500)
            self.assertEquals(res.json(), {'error': 'cannot_send_message'})

    def test_send_message_generic_kafka_error(self):
        channel_id = 'channel_id'
        payload = self.encypter.encrypt('payload')
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
            self.assertEquals(res.status_code, 500)
            self.assertEquals(res.json(), {'error': 'cannot_send_message'})
