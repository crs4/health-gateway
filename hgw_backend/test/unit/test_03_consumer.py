import json
import logging
import os

from django.test import TestCase
from mock.mock import call, patch

from hgw_backend.management.commands.channel_consumer import Command
from hgw_backend.models import FailedConnector, Source
from hgw_backend.settings import KAFKA_CHANNEL_NOTIFICATION_TOPIC
from hgw_common.utils.mocks import MockKafkaConsumer, MockMessage

from . import (HGW_FRONTEND_CLIENT_NAME, SOURCE_ENDPOINT_CLIENT_NAME,
               GenericTestCase)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


DEST_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\n' \
                  'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp4TF/ETwYKG+eAYZz3wo\n' \
                  '8IYqrPIlQyz1/xljqDD162ZAYJLCYeCfs9yczcazC8keWzGd5/tn4TF6II0oINKh\n' \
                  'kCYLqTIVkVGC7/tgH5UEe/XG1trRZfMqwl1hEvZV+/zanV0cl7IjTR9ajb1TwwQY\n' \
                  'MOjcaaBZj+xfD884pwogWkcSGTEODGfoVACHjEXHs+oVriHqs4iggiiMYbO7TBjg\n' \
                  'Be9p7ZDHSVBbXtQ3XuGKnxs9MTLIh5L9jxSRb9CgAtv8ubhzs2vpnHrRVkRoddrk\n' \
                  '8YHKRryYcVDHVLAGc4srceXU7zrwAMbjS7msh/LK88ZDUWfIZKZvbV0L+/topvzd\n' \
                  'XQIDAQAB\n' \
                  '-----END PUBLIC KEY-----'


class TestConsumer(GenericTestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        logger = logging.getLogger('hgw_backend_tests')
        logger.warning("Logs related to Kafka errors can be safely ignored for this testSuite 03")

        self.base_messages = [{
            'channel_id': 'KKa8QqqTBGePJStJpQMbspEvvV4LJJCY',
            'source_id': 'LD2j7v35BvUlzWDe8G89JGzz4SOincB7',
            'destination': {
                'destination_id': 'ZQM4kvxYBaMf2nnVCdEfSLtswtthHY2Z',
                'kafka_public_key': DEST_PUBLIC_KEY
            },
            'profile': {
                "code": "PROF002",
                "version": "hgw.document.profile.v0",
                "start_time_validity": "2017-06-23T10:13:39Z",
                "end_time_validity": "2018-06-23T23:59:59Z",
                "payload": "{\"clinical_domain\": \"Laboratory\"}"
            },
            'person_id': 'AAAABBBBCCCCDDDD',
            'start_validity': '2017-10-23T10:00:54+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }, {
            'channel_id': 'KKa8QqqTBGePJStJpQMbspEvvV4LJJCY',
            'source_id': 'LD2j7v35BvUlzWDe8G89JGzz4SOincB7',
            'destination': {
                'destination_id': 'ZQM4kvxYBaMf2nnVCdEfSLtswtthHY2Z',
                'kafka_public_key': DEST_PUBLIC_KEY
            },
            'profile': {
                "code": "PROF002",
                "version": "hgw.document.profile.v0",
                "payload": "{\"clinical_domain\": \"Laboratory\"}"
            },
            'person_id': 'AAAABBBBCCCCDDDD',
            'start_validity': None,
            'expire_validity': None
        }]
    
        self.create_messages = [m.copy() for m in self.base_messages]
        for m in self.create_messages:
            m.update({'action': 'CREATED'})
        
        self.update_messages = [m.copy() for m in self.base_messages]
        for m in self.update_messages:
            m.update({'action': 'UPDATED'})
        
        self.delete_messages = [m.copy() for m in self.base_messages]
        for m in self.delete_messages:
            m.update({'action': 'REVOKED'})

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, json_enc=True, encoding='utf-8'):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        topic = KAFKA_CHANNEL_NOTIFICATION_TOPIC
        mock_kc_klass.MESSAGES = {i: MockMessage(offset=i,
                                                 topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_correct_connector_creation(self):
        """
        Test correct connector creation
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True) as mocked_create_connector:
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.create_messages, True)
            Command().handle()
            self.assertEqual(FailedConnector.objects.count(), 0)
            calls = []

            for m in self.create_messages:
                source_obj = Source.objects.get(source_id=m['source_id'])
                connector = {
                    'profile': m['profile'],
                    'person_identifier': m['person_id'],
                    'dest_public_key': m['destination']['kafka_public_key'],
                    'channel_id': m['channel_id'],
                    'start_validity': m['start_validity'][:10] if m['start_validity'] is not None else None,
                    'expire_validity': m['expire_validity'][:10] if m['expire_validity'] is not None else None
                }
                calls.append(call(source_obj, connector))
            mocked_create_connector.assert_has_calls(calls)
        
    def test_correct_connector_update(self):
        """
        Test correct connector update
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.update_connector', return_value=True) as mocked_update_connector:
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.update_messages, True)
            Command().handle()
            self.assertEqual(FailedConnector.objects.count(), 0)
            calls = []

            for m in self.update_messages:
                source_obj = Source.objects.get(source_id=m['source_id'])
                connector = {
                    'channel_id': m['channel_id'],
                    'profile': m['profile'],
                    'start_validity': m['start_validity'][:10] if m['start_validity'] is not None else None,
                    'expire_validity': m['expire_validity'][:10] if m['expire_validity'] is not None else None
                }
                calls.append(call(source_obj, connector))
            mocked_update_connector.assert_has_calls(calls)
    
    def test_correct_connector_delete(self):
        """
        Test correct connector delete
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.delete_connector', return_value=True) as mocked_delete_connector:
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.delete_messages, True)
            Command().handle()
            self.assertEqual(FailedConnector.objects.count(), 0)
            calls = []

            for m in self.delete_messages:
                source_obj = Source.objects.get(source_id=m['source_id'])
                connector = {
                    'channel_id': m['channel_id']
                }
                calls.append(call(source_obj, connector))
            mocked_delete_connector.assert_has_calls(calls)
    
    def test_message_failure_db_error(self):
        """
        Test correct message send
        """

        mock = self._get_db_error_mock()
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True) as mocked_create_connector, \
                patch('hgw_backend.management.commands.channel_consumer.Source', mock):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.create_messages, True)
            Command().handle()
            mocked_create_connector.assert_not_called()
        self.assertEqual(FailedConnector.objects.count(), len(self.create_messages))
        for index, failed in enumerate(FailedConnector.objects.all()):
            self.assertEqual(json.loads(failed.message), self.create_messages[index])
            self.assertEqual(failed.reason, FailedConnector.DATABASE_ERROR)
            self.assertEqual(failed.retry, True)

    def test_send_message_fail(self):
        """
        Test failure sending message
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.create_messages, True)
            Command().handle()
            self.assertEqual(FailedConnector.objects.count(), 2)
            for index, failed in enumerate(FailedConnector.objects.all()):
                self.assertEqual(json.loads(failed.message), self.create_messages[index])
                self.assertEqual(failed.reason, FailedConnector.SENDING_ERROR)
                self.assertEqual(failed.retry, True)

    def test_consume_message_fail_to_json_decode(self):
        """
        Tests failure because of json decode
        """
        messages = ['(a)']
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True):
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, False)
            command = Command()
            command.handle()

            self.assertEqual(FailedConnector.objects.count(), 1)
            f = FailedConnector.objects.first()
            self.assertEqual(f.message, json.dumps(messages[0]))
            self.assertEqual(f.reason, FailedConnector.JSON_DECODING)
            self.assertEqual(f.retry, False)

    def test_consume_message_fail_to_message_structure(self):
        """
        Tests failure beacuse of incorrect message structure
        """
        del self.create_messages[0]['channel_id']
        print(FailedConnector.objects.count())
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.create_messages, True)
            command = Command()
            command.handle()

            self.assertEqual(FailedConnector.objects.count(), 1)
            f = FailedConnector.objects.first()
            self.assertEqual(json.loads(f.message), self.create_messages[0])
            self.assertEqual(f.reason, FailedConnector.WRONG_MESSAGE_STRUCTURE)
            self.assertEqual(f.retry, False)

    def test_consume_message_fail_to_unknown_source_id(self):
        """
        Tests failure beacuse of unknown source
        """
        self.create_messages[0]['source_id'] = 'a' * 32  # generates an unknown source_id. 32 is the character length of a source_id
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.create_messages, True)
            command = Command()
            command.handle()

            self.assertEqual(FailedConnector.objects.count(), 1)
            f = FailedConnector.objects.first()
            self.assertEqual(json.loads(f.message), self.create_messages[0])
            self.assertEqual(f.reason, FailedConnector.SOURCE_NOT_FOUND)
            self.assertEqual(f.retry, False)

    def test_consume_message_fail_to_unicode_error(self):
        """
        Tests failure because of unicode decoding error. In this case the message won't be saved on db
        """
        messages = ['(a)']
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True):
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, True, 'utf-16')
            command = Command()
            command.handle()

            # Django will fail to insert the message into the db because of the wrong encoding
            self.assertEqual(FailedConnector.objects.count(), 0)

    def test_consume_message_fail_to_wrong_start_date_format(self):
        """
        Tests failure beacuse of unicode decoding error. In this case the message won't be saved on db
        """
        self.create_messages[0]['start_validity'] = 'WRONG_DATE'
        self.create_messages[1]['expire_validity'] = 'WRONG_DATE'
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_backend.models.OAuth2Authentication.create_connector', return_value=True):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.create_messages, True)
            command = Command()
            command.handle()

            # Django will fail to insert the messages into the db because of the wrong date formats
            self.assertEqual(FailedConnector.objects.count(), 2)
            failed_connectors = FailedConnector.objects.all()
            for index, failed_connector in enumerate(failed_connectors):
                self.assertEqual(json.loads(failed_connector.message), self.create_messages[index])
                self.assertEqual(failed_connector.reason, FailedConnector.WRONG_DATE_FORMAT)
                self.assertEqual(failed_connector.retry, False)
