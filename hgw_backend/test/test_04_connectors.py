import json
import logging
import os
from datetime import datetime, timedelta
from test.utils import MockSourceEndpointHandler

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, client
from mock import MagicMock, patch

from hgw_backend.models import (AccessToken, FailedConnector,
                                OAuth2Authentication, Source)
from hgw_backend.settings import KAFKA_CONNECTOR_NOTIFICATION_TOPIC
from hgw_common.utils.mocks import (MockMessage, start_mock_server,
                                    stop_mock_server)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CERT_SOURCE_PORT = 40000
OAUTH_SOURCE_PORT = 40001

PROFILE = {
    'code': 'PROF_001',
    'version': 'v0',
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
    'start_validity': '2017-10-23',
    'expire_validity': '2018-10-23',
}


class TestConnectorCreation(TestCase):
    fixtures = ['test_data.json']

    """
    Test creation of connectors into the source endpoint
    """
    @classmethod
    def setUpClass(cls):
        super(TestConnectorCreation, cls).setUpClass()
        logger = logging.getLogger('hgw_backend')
        logger.setLevel(logging.CRITICAL)
        cls.oauth_thread, cls.oauth_server = start_mock_server('certs', MockSourceEndpointHandler, OAUTH_SOURCE_PORT)
        cls.cert_thread, cls.cert_server = start_mock_server('certs', MockSourceEndpointHandler, CERT_SOURCE_PORT)

    @classmethod
    def tearDownClass(cls):
        stop_mock_server(cls.oauth_thread, cls.oauth_server)
        stop_mock_server(cls.cert_thread, cls.cert_server)
        return super().tearDownClass()

    @staticmethod
    def _get_source_from_auth_obj(auth):
        content_type = ContentType.objects.get_for_model(auth)
        return Source.objects.get(content_type=content_type, object_id=auth.id)

    @staticmethod
    def configure_mock_kafka_consumer(mock_kc_klass, n_messages=1):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = n_messages
        mock_kc_klass.MESSAGES = {i: MockMessage(key='09876'.encode('utf-8'), offset=i,
                                                 topic='vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj'.encode('utf-8'),
                                                 value=json.dumps(CHANNEL_MESSAGE).encode('utf-8')) for i in
                                  range(mock_kc_klass.FIRST, mock_kc_klass.END)}

    def test_create_connector_oauth2_source_fails_connector_unreachable(self):
        """
        Tests creation of new connector failure because of source endpoint unreachable whne calling /v1/connectors
        """
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            source = self._get_source_from_auth_obj(auth)
            source.url = 'https://localhost:1000'
            res = auth.create_connector(source, CONNECTOR)
            self.assertIsNone(res)
            MockKafkaProducer().send.assert_not_called()

    def test_create_connector_oauth2_source_fails_wrong_connector_url(self):
        """
        Tests creation of new connector failure because of wrong connector url
        """
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            source = self._get_source_from_auth_obj(auth)
            source.url = 'http://localhost:40000/wrong_url/'
            res = auth.create_connector(source, CONNECTOR)
            self.assertIsNone(res)
            MockKafkaProducer().send.assert_not_called()

    def test_create_connector_oauth2_source_fails_oauth2_unreachable(self):
        """
        Tests creation of new connector failure because of source enpoint unreachable when calling /oauth2/token
        """

        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            auth.token_url = 'https://localhost:1000/'
            source = self._get_source_from_auth_obj(auth)
            res = auth.create_connector(source, CONNECTOR)
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
            self.assertIsNone(res)
            MockKafkaProducer().send.assert_not_called()

    def test_create_connector_oauth2_source_fails_wrong_oauth2_url(self):
        """
        Tests creation of new connector failure because of source enpoint wrong oauth2 url
        """
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            auth.token_url = 'http://localhost:40000/wrong_url/'
            source = self._get_source_from_auth_obj(auth)
            res = auth.create_connector(source, CONNECTOR)
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
            self.assertIsNone(res)
            MockKafkaProducer().send.assert_not_called()

    def test_create_connector_oauth2_source_fails_create_token_wrong_client_id(self):
        """
        Tests creation of new connector failure because of token creation failure in case of wrong client id
        """
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            auth.client_id = "unkn"
            source = self._get_source_from_auth_obj(auth)
            res = auth.create_connector(source, CONNECTOR)
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
            self.assertIsNone(res)
            MockKafkaProducer().send.assert_not_called()

    def test_create_connector_oauth2_source_fails_create_token_wrong_client_secret(self):
        """
        Tests creation of new connector failure because of token creation failure in case of wrong client secret
        """
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            auth.client_secret = "unkn"
            source = self._get_source_from_auth_obj(auth)
            res = auth.create_connector(source, CONNECTOR)
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
            self.assertIsNone(res)
            MockKafkaProducer().send.assert_not_called()

    def test_create_connector_oauth2_source_fail_refresh_token_connection_error(self):
        """
        Tests creation of new connector failure when the token refresh fails becuase of a connection error
        """
        # Create an expired token in the db
        auth_obj = OAuth2Authentication.objects.first()
        AccessToken.objects.create(oauth2_authentication=auth_obj, access_token='something',
                                   token_type='Bearer', expires_in=3600, expires_at=datetime.now())

        # Break the OAuth2Authentication object with a wrong url
        auth = OAuth2Authentication.objects.first()
        auth.token_url = 'https://localhost:1000/'
        auth.save()

        source = self._get_source_from_auth_obj(auth)
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            res = source.create_connector(CONNECTOR)
            # The token is canceled but recreation fails
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)

            MockKafkaProducer().send.assert_not_called()
            self.assertIsNone(res)

    def test_create_connector_oauth2_source_fail_refresh_token_wrong_client_id(self):
        """
        Tests creation of new connector failure when the token refresh fails becuase of a connection error
        """
        # Create an expired token in the db
        auth_obj = OAuth2Authentication.objects.first()
        AccessToken.objects.create(oauth2_authentication=auth_obj, access_token='something',
                                   token_type='Bearer', expires_in=3600, expires_at=datetime.now())

        # Break the OAuth2Authentication object with a wrong url
        auth = OAuth2Authentication.objects.first()
        auth.client_id = 'wrong_client'
        auth.save()

        source = self._get_source_from_auth_obj(auth)
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            res = source.create_connector(CONNECTOR)
            # The token is canceled but recreation fails
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)

            MockKafkaProducer().send.assert_not_called()
            self.assertIsNone(res)

    def test_create_connector_oauth2_source_fail_refresh_token_wrong_client_secret(self):
        """
        Tests creation of new connector failure when the token refresh fails becuase of a connection error
        """
        # Create an expired token in the db
        auth_obj = OAuth2Authentication.objects.first()
        AccessToken.objects.create(oauth2_authentication=auth_obj, access_token='something',
                                   token_type='Bearer', expires_in=3600, expires_at=datetime.now())

        # Break the OAuth2Authentication object with a wrong url
        auth = OAuth2Authentication.objects.first()
        auth.client_secret = 'wrong_client'
        auth.save()

        source = self._get_source_from_auth_obj(auth)
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            res = source.create_connector(CONNECTOR)
            # The token is canceled but recreation fails
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)

            MockKafkaProducer().send.assert_not_called()
            self.assertIsNone(res)

    def test_create_connector_oauth2_source_new_token(self):
        """
        Tests creation of new connector success when creating the first token
        """
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            auth = OAuth2Authentication.objects.first()
            self.assertRaises(AccessToken.DoesNotExist, AccessToken.objects.get, oauth2_authentication=auth)
            source = self._get_source_from_auth_obj(auth)
            res = source.create_connector(CONNECTOR)
            token = AccessToken.objects.get(oauth2_authentication=auth)
            self.assertIsNotNone(token)
            self.assertIsNotNone(res)
            MockKafkaProducer().send.assert_called_once()
            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CONNECTOR_NOTIFICATION_TOPIC)
            self.assertEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                             {'channel_id': CONNECTOR['channel_id']})

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
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            res = source.create_connector(CONNECTOR)
            token = AccessToken.objects.get(oauth2_authentication=auth)
            self.assertIsNotNone(token)
            self.assertNotEqual(AccessToken.objects.get(oauth2_authentication=auth_obj).access_token,
                                'expired')
            self.assertIsNotNone(res)
            MockKafkaProducer().send.assert_called_once()
            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CONNECTOR_NOTIFICATION_TOPIC)
            self.assertEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                             {'channel_id': CONNECTOR['channel_id']})

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
        with patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            res = source.create_connector(CONNECTOR)
            token = AccessToken.objects.get(oauth2_authentication=auth)
            self.assertIsNotNone(token)
            self.assertNotEqual(AccessToken.objects.get(oauth2_authentication=auth).access_token,
                                'expired')
            self.assertIsNotNone(res)
            MockKafkaProducer().send.assert_called_once()
            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CONNECTOR_NOTIFICATION_TOPIC)
            self.assertEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                             {'channel_id': CONNECTOR['channel_id']})
