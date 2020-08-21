from datetime import datetime
import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.test import TestCase
from mock.mock import Mock, NonCallableMock, patch

from hgw_common.models import FailedMessages, Profile
from hgw_common.utils.mocks import MockKafkaConsumer, MockMessage
from hgw_frontend.management.commands.connector_notification_consumer import \
    Command as ConnectorNotificationCommand
from hgw_frontend.management.commands.consent_manager_notification_consumer import (
    ACTION, FAILED_MESSAGE_TYPE, FAILED_REASON)
from hgw_frontend.management.commands.consent_manager_notification_consumer import \
    Command as ConsentNotificationCommand
from hgw_frontend.management.commands.source_notification_consumer import \
    Command as SourceNotificationCommand
from hgw_frontend.models import Channel, ConsentConfirmation, Source
from hgw_frontend.settings import (DATETIME_FORMAT,
                                   KAFKA_CHANNEL_NOTIFICATION_TOPIC,
                                   KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                   KAFKA_SOURCE_NOTIFICATION_TOPIC)

from . import (CORRECT_CONSENT_ID_AC, CORRECT_CONSENT_ID_CR, DEST_1_ID,
               DEST_1_NAME, DEST_PUBLIC_KEY, PERSON_ID, PROFILE_1, PROFILE_2,
               SOURCE_1_ID, SOURCE_1_NAME, SOURCE_2_ID, SOURCE_2_NAME,
               SOURCE_3_ID, SOURCE_3_NAME)


def _get_db_error_mock():
    mock = NonCallableMock()
    mock.DoesNotExist = ObjectDoesNotExist
    mock.objects = NonCallableMock()
    mock.objects.all = Mock(side_effect=DatabaseError)
    mock.objects.filter = Mock(side_effect=DatabaseError)
    mock.objects.get = Mock(side_effect=DatabaseError)
    mock.objects.create = Mock(side_effect=DatabaseError)
    mock.objects.get_or_create = Mock(side_effect=DatabaseError)
    return mock


class TestSourceConsumer(TestCase):
    """
    Tests consumer for source updates from hgw backend
    """

    def setUp(self):
        self.source_notification_messages = [{
            'source_id': SOURCE_3_ID,
            'name': SOURCE_3_NAME,
            'profile': PROFILE_1
        }]

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, topic, json_enc=True, encoding='utf-8'):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        mock_kc_klass.MESSAGES = {i: MockMessage(offset=i, topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_correct_source_add(self):
        """
        Tests that the message is consumed and that a new Source is created in the db
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.source_notification_messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            SourceNotificationCommand().handle()

            for message in self.source_notification_messages:
                sources = Source.objects.filter(source_id=message['source_id'])
                self.assertEqual(sources.count(), 1)
                source = sources.first()
                self.assertEqual(source.source_id, message['source_id'])
                self.assertEqual(source.name, message['name'])
                self.assertEqual(source.profile.code, message['profile']['code'])
                self.assertEqual(source.profile.version, message['profile']['version'])
                self.assertEqual(source.profile.payload, message['profile']['payload'])

    def test_correct_source_update(self):
        """
        Tests that the message is consumed and that a new Source is created in the db
        """
        # Adds the source to update
        profile = Profile.objects.create(**PROFILE_1)
        Source.objects.create(source_id=SOURCE_3_ID, name=SOURCE_3_NAME, profile=profile)
        messages = [{
            'source_id': SOURCE_3_ID,
            'name': 'NEW_NAME',
            'profile': PROFILE_2
        }]
        with patch('hgw_common.messaging.receiver.KafkaConsumer',
                   MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            SourceNotificationCommand().handle()

            for message in messages:
                sources = Source.objects.filter(source_id=message['source_id'])
                self.assertEqual(sources.count(), 1)
                source = sources.first()
                self.assertEqual(source.source_id, message['source_id'])
                self.assertEqual(source.name, message['name'])
                self.assertEqual(source.profile.code, message['profile']['code'])
                self.assertEqual(source.profile.version, message['profile']['version'])
                self.assertEqual(source.profile.payload, message['profile']['payload'])

    def test_failure_to_db_error(self):
        """
        Tests that the message is consumed but db error occurs
        """
        mock = _get_db_error_mock()
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_frontend.management.commands.source_notification_consumer.Source', mock):
            messages = ['(a)']
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, False)
            SourceNotificationCommand().handle()

            self.assertEqual(Source.objects.count(), 0)

    def test_failure_to_json_decoding(self):
        """
        Tests that the message is consumed but json decoding fails
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = ['(a)']
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, False)
            SourceNotificationCommand().handle()

            self.assertEqual(Source.objects.count(), 0)

    def test_source_failure_to_message_structure(self):
        """
        Tests that the message is consumed but it doesn't have the correct structure
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = [{
                'name': SOURCE_3_NAME,
                'profile': PROFILE_1
            }, {
                'source_id': SOURCE_3_ID,
                'profile': PROFILE_1,
            }, {
                'source_id': SOURCE_3_ID,
                'name': SOURCE_3_NAME,
            }, 'wrong_type']
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            SourceNotificationCommand().handle()

            self.assertEqual(Source.objects.count(), 0)

    def test_source_failure_to_invalid_profile_structure(self):
        """
        Tests that the message is consumed but it doesn't have the correct structure
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = [{
                'source_id': SOURCE_3_ID,
                'name': SOURCE_3_NAME,
                'profile': {
                    'code': 'PROF_003',
                    'payload': '[{"clinical_domain": "Anatomical Pathology"}]'
                }
            }, {
                'source_id': SOURCE_3_ID,
                'name': SOURCE_3_NAME,
                'profile': {
                    'version': 'v0',
                    'payload': '[{"clinical_domain": "Anatomical Pathology"}]'
                }
            }, {
                'source_id': SOURCE_3_ID,
                'name': SOURCE_3_NAME,
                'profile': {
                    'code': 'PROF_003',
                    'version': 'v0',
                }
            }]
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            SourceNotificationCommand().handle()

            self.assertEqual(Source.objects.count(), 0)


class TestConnectorConsumer(TestCase):
    """
    Test consumer for connector updates from hgw backend
    """
    fixtures = ['test_data.json']

    def setUp(self):
        self.connector_notification_messages = [{
            'channel_id': 'wrong_consent2'  # This channel is set as WS in the test data
        }]

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, topic, json_enc=True, encoding='utf-8'):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        mock_kc_klass.MESSAGES = {i: MockMessage(offset=i, topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_correct_connector_notification(self):
        """
        Tests that the message is received and the status of the corresponding Channel is set to ACTIVE
        """
        for connector in self.connector_notification_messages:
            channel = ConsentConfirmation.objects.get(consent_id=connector['channel_id']).channel
            self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.connector_notification_messages,
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)

            ConnectorNotificationCommand().handle()

            for connector in self.connector_notification_messages:
                channel = ConsentConfirmation.objects.get(consent_id=connector['channel_id']).channel
                self.assertEqual(channel.status, Channel.ACTIVE)

    def test_failure_when_consent_status_is_wrong(self):
        """
        Tests that the message is received but nothing happens because the channel was not in 
        WAITING_SOURCE_NOTIFICATION status
        """
        for connector in self.connector_notification_messages:
            channel = ConsentConfirmation.objects.get(consent_id=connector['channel_id']).channel
            channel.status = Channel.CONSENT_REQUESTED
            channel.save()

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.connector_notification_messages,
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            ConnectorNotificationCommand().handle()

            for connector in self.connector_notification_messages:
                channel = ConsentConfirmation.objects.get(consent_id=connector['channel_id']).channel
                self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)

    def test_failure_because_of_channel_not_found(self):
        """
        Tests that the message is received but nothing happens because the channel was not found
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, [{'channel_id': 'wrong'}],
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            ConnectorNotificationCommand().handle()

    def test_failure_because_of_wrong_structure(self):
        """
        Tests that the message is received but nothing happens because the structure of the message was wrong
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, [{'wrong': 'str'}, 'wrong'],
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            ConnectorNotificationCommand().handle()


class TestConsentConsumer(TestCase):
    """
    Test consumer for consent updates from consent manager
    """

    fixtures = ['test_data.json']

    def setUp(self):
        self.base_consent = {
            'consent_id': CORRECT_CONSENT_ID_CR,
            'status': 'AC',
            'source': {
                'id': SOURCE_1_ID,
                'name': SOURCE_1_NAME
            },
            'destination': {
                'id': DEST_1_ID,
                'name': DEST_1_NAME
            },
            'person_id': PERSON_ID,
            'profile': PROFILE_1,
            'start_validity': '2017-10-23T10:00:00+0200',
            'expire_validity': '2018-10-23T10:00:00+0200',
        }

        self.out_message = {
            'channel_id': CORRECT_CONSENT_ID_CR,
            'source_id': SOURCE_1_ID,
            'destination': {
                'destination_id': DEST_1_ID,
                'kafka_public_key': DEST_PUBLIC_KEY
            },
            'profile': PROFILE_1,
            'person_id': PERSON_ID,
            'start_validity': '2017-10-23T10:00:00+0200',
            'expire_validity': '2018-10-23T10:00:00+0200',
        }

        return super(TestConsentConsumer, self).setUp()

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, topic, json_enc=True, encoding='utf-8'):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        mock_kc_klass.MESSAGES = {i: MockMessage(offset=i, topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_consent_confirmed(self):
        """
        Test correct consent notification
        """
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)
        self.out_message.update({'action': ACTION.CREATED})

        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)
        start_validity = datetime.strptime(self.base_consent['start_validity'], DATETIME_FORMAT)
        expire_validity = datetime.strptime(self.base_consent['expire_validity'], DATETIME_FORMAT)
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)
            self.assertEqual(channel.source, Source.objects.get(source_id=self.base_consent['source']['id']))
            self.assertEqual(channel.start_validity, start_validity)
            self.assertEqual(channel.expire_validity, expire_validity)
            self.assertEqual(channel.start_validity, channel.flow_request.start_validity)
            self.assertEqual(channel.expire_validity, channel.flow_request.expire_validity)
            self.assertEqual(channel.flow_request.profile, Profile.objects.get(code=self.base_consent['profile']['code']))
            self.assertEqual(channel.flow_request.person_id, self.base_consent['person_id'])

            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CHANNEL_NOTIFICATION_TOPIC)
            print(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')))
            self.assertDictEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                                 self.out_message)
            self.assertEqual(FailedMessages.objects.count(), 0)
    
    def test_consent_confirmed_change_date(self):
        """
        Test that the date of the confirmed consent differs from the original request (i.e., the flow request values)
        """
        self.base_consent.update({
            'start_validity': '2018-10-23T10:00:00+0200',
            'expire_validity': '2019-10-23T10:00:00+0200',      
        })
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)
        
        self.out_message.update({
            'action': ACTION.CREATED,
            'start_validity': '2018-10-23T10:00:00+0200',
            'expire_validity': '2019-10-23T10:00:00+0200'
        })

        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)
        new_start_validity = datetime.strptime(self.base_consent['start_validity'], DATETIME_FORMAT)
        new_expire_validity = datetime.strptime(self.base_consent['expire_validity'], DATETIME_FORMAT)
        self.assertNotEqual(channel.start_validity, new_start_validity)
        self.assertNotEqual(channel.expire_validity, new_expire_validity)
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)
            self.assertEqual(channel.source, Source.objects.get(source_id=self.base_consent['source']['id']))
            self.assertEqual(channel.start_validity, new_start_validity)
            self.assertEqual(channel.expire_validity, new_expire_validity)
            self.assertEqual(channel.flow_request.profile, Profile.objects.get(code=self.base_consent['profile']['code']))
            self.assertEqual(channel.flow_request.person_id, self.base_consent['person_id'])

            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CHANNEL_NOTIFICATION_TOPIC)
            self.assertDictEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                                 self.out_message)
            self.assertEqual(FailedMessages.objects.count(), 0)

    def test_consent_confirmed_failure_because_of_inconsistent_status(self):
        """
        Test failure when confirming a consent which has not the right status
        """

        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        channel.status = Channel.CONSENT_REVOKED
        channel.save()

        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REVOKED)
            MockKafkaProducer().send.assert_not_called()

        self.assertEqual(FailedMessages.objects.count(), 1)
        message = FailedMessages.objects.first()
        self.assertEqual(message.reason, FAILED_REASON.INCONSISTENT_STATUS)
        self.assertEqual(message.retry, False)
        self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_consent_revoked(self):
        """
        Test correct revoke
        """

        for status in (Channel.ACTIVE, Channel.WAITING_SOURCE_NOTIFICATION):
            self.base_consent.update({
                'status': 'RE'
            })
            self.out_message.update({'action': ACTION.REVOKED})
            self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                         KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            channel.status = status
            channel.save()
            with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                    patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
                ConsentNotificationCommand().handle()

                channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
                self.assertEqual(channel.status, Channel.CONSENT_REVOKED)
                self.assertEqual(channel.source, Source.objects.get(source_id=self.base_consent['source']['id']))
                self.assertEqual(channel.flow_request.profile, Profile.objects.get(code=self.base_consent['profile']['code']))
                self.assertEqual(channel.flow_request.person_id, self.base_consent['person_id'])
                self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CHANNEL_NOTIFICATION_TOPIC)
                self.assertDictEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                                     self.out_message)
                self.assertEqual(FailedMessages.objects.count(), 0)

    def test_consent_revoked_failure_because_of_inconsistent_status(self):
        """
        Test failure when confirming a consent which has not the right status
        """

        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        channel.status = Channel.CONSENT_REQUESTED
        channel.save()

        self.base_consent.update({
            'status': 'RE'
        })
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)
            MockKafkaProducer().send.assert_not_called()

        self.assertEqual(FailedMessages.objects.count(), 1)
        message = FailedMessages.objects.first()
        self.assertEqual(message.reason, FAILED_REASON.INCONSISTENT_STATUS)
        self.assertEqual(message.retry, False)
        self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_consent_changed(self):
        """
        Test the channel update according to the consent.
        """
        self.base_consent.update({
            'consent_id': CORRECT_CONSENT_ID_AC,
            'start_validity': '2018-10-23T10:00:00+0200',
            'expire_validity': '2019-10-23T10:00:00+0200',
            'source': {
                'id': SOURCE_2_ID,
                'name': SOURCE_2_NAME
            },
        })

        self.out_message.update({
            'action': ACTION.UPDATED,
            'channel_id': CORRECT_CONSENT_ID_AC,
            'start_validity': '2018-10-23T10:00:00+0200',
            'expire_validity': '2019-10-23T10:00:00+0200',
            'source_id': SOURCE_2_ID
        })

        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)
        new_start_validity = datetime.strptime(self.base_consent['start_validity'], DATETIME_FORMAT)
        new_expire_validity = datetime.strptime(self.base_consent['expire_validity'], DATETIME_FORMAT)
        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        self.assertEqual(channel.status, Channel.ACTIVE)
        self.assertNotEqual(channel.start_validity, new_start_validity)
        self.assertNotEqual(channel.expire_validity, new_expire_validity)
        
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.ACTIVE)
            self.assertEqual(channel.source, Source.objects.get(source_id=self.base_consent['source']['id']))
            self.assertEqual(channel.flow_request.profile, Profile.objects.get(code=self.base_consent['profile']['code']))
            self.assertEqual(channel.flow_request.person_id, self.base_consent['person_id'])
            self.assertEqual(channel.start_validity, new_start_validity)
            self.assertEqual(channel.expire_validity, new_expire_validity)

            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CHANNEL_NOTIFICATION_TOPIC)
            self.assertDictEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                                 self.out_message)
            self.assertEqual(FailedMessages.objects.count(), 0)

    def test_consent_changed_none_date(self):
        """
        Test the channel update according to the consent.
        """
        self.base_consent.update({
            'consent_id': CORRECT_CONSENT_ID_AC,
            'start_validity': None,
            'expire_validity': None,
            'source': {
                'id': SOURCE_2_ID,
                'name': SOURCE_2_NAME
            },
        })

        self.out_message.update({
            'action': ACTION.UPDATED,
            'channel_id': CORRECT_CONSENT_ID_AC,
            'start_validity': None,
            'expire_validity': None,
            'source_id': SOURCE_2_ID
        })

        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)
        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        self.assertEqual(channel.status, Channel.ACTIVE)
        self.assertIsNotNone(channel.start_validity)
        self.assertIsNotNone(channel.expire_validity)
        
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.ACTIVE)
            self.assertEqual(channel.source, Source.objects.get(source_id=self.base_consent['source']['id']))
            self.assertEqual(channel.flow_request.profile, Profile.objects.get(code=self.base_consent['profile']['code']))
            self.assertEqual(channel.flow_request.person_id, self.base_consent['person_id'])
            self.assertEqual(channel.start_validity, None)
            self.assertEqual(channel.expire_validity, None)

            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_CHANNEL_NOTIFICATION_TOPIC)
            self.assertDictEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')),
                                 self.out_message)
            self.assertEqual(FailedMessages.objects.count(), 0)

    def test_consent_changed_failure_because_of_inconsistent_status(self):
        """
        Test failure when confirming a consent which has not the right status
        """
        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        channel.status = Channel.CONSENT_REVOKED
        channel.save()

        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REVOKED)
            MockKafkaProducer().send.assert_not_called()

        self.assertEqual(FailedMessages.objects.count(), 1)
        message = FailedMessages.objects.first()
        self.assertEqual(message.reason, FAILED_REASON.INCONSISTENT_STATUS)
        self.assertEqual(message.retry, False)
        self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_consent_changed_failure_because_of_no_changes(self):
        """
        Test failure when changing a channel but there's no differences with the old Channel
        """
        # Same data as the channel in the test_data
        self.base_consent.update({
            'consent_id': CORRECT_CONSENT_ID_AC,
            'start_validity': '2017-10-23T10:00:00+0200',
            'expire_validity': '2018-10-23T10:00:00+0200',
            'source': {
                'id': SOURCE_2_ID,
                'name': SOURCE_2_NAME
            },
        })
        
        channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
        old_start_validity = channel.start_validity
        old_expire_validity = channel.expire_validity        

        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        start_validity = datetime.strptime(self.base_consent['start_validity'], DATETIME_FORMAT)
        expire_validity = datetime.strptime(self.base_consent['expire_validity'], DATETIME_FORMAT)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.ACTIVE)
            self.assertEqual(channel.start_validity, old_start_validity)
            self.assertEqual(channel.expire_validity, old_expire_validity)
            MockKafkaProducer().send.assert_not_called()

            self.assertEqual(FailedMessages.objects.count(), 1)
            message = FailedMessages.objects.first()
            self.assertEqual(message.reason, FAILED_REASON.INCONSISTENT_STATUS)
            self.assertEqual(message.retry, False)
            self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_failure_because_of_wrong_input_structure(self):
        """
        Test that no action has been performed because the input message misses some needed key
        """
        messages = []
        for key in self.base_consent:
            message = self.base_consent.copy()
            del message[key]
            messages.append(message)

        self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()
            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)
            MockKafkaProducer().send.assert_not_called()
            self.assertEqual(FailedMessages.objects.count(), len(messages))
            for message in FailedMessages.objects.all():
                self.assertEqual(message.reason, FAILED_REASON.INVALID_STRUCTURE)
                self.assertEqual(message.retry, False)
                self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_failure_because_of_unknown_consent(self):
        """
        Test that no action has been performed because the consent has not been found in the db
        """
        self.base_consent['consent_id'] = 'UNKNOWN'
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()
            MockKafkaProducer().send.assert_not_called()
            self.assertEqual(FailedMessages.objects.count(), 1)
            message = FailedMessages.objects.first()
            self.assertEqual(message.reason, FAILED_REASON.UNKNOWN_CONSENT)
            self.assertEqual(message.retry, False)
            self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_failure_because_of_different_person_id(self):
        """
        Test that no action have been performed becaue the consent has a different person id than the channel
        """
        self.base_consent['person_id'] = 'UNKNOWN'
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)

            MockKafkaProducer().send.assert_not_called()
            self.assertEqual(FailedMessages.objects.count(), 1)
            message = FailedMessages.objects.first()
            self.assertEqual(message.reason, FAILED_REASON.MISMATCHING_PERSON)
            self.assertEqual(message.retry, False)
            self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_failure_because_of_different_source(self):
        """
        Test that no action have been performed becaue the consent has a different person id than the channel
        """
        self.base_consent['source']['id'] = 'UNKNOWN'
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.messaging.sender.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)

            MockKafkaProducer().send.assert_not_called()
            self.assertEqual(FailedMessages.objects.count(), 1)
            message = FailedMessages.objects.first()
            self.assertEqual(message.reason, FAILED_REASON.MISMATCHING_SOURCE)
            self.assertEqual(message.retry, False)
            self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)

    def test_failure_because_of_broker_connection_error(self):
        """
        Test that no action have been performed becaue the consent has a different person id than the channel
        """
        self.set_mock_kafka_consumer(MockKafkaConsumer, [self.base_consent],
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            ConsentNotificationCommand().handle()

            channel = ConsentConfirmation.objects.get(consent_id=self.base_consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)

            self.assertEqual(FailedMessages.objects.count(), 1)
            message = FailedMessages.objects.first()
            self.assertEqual(message.reason, FAILED_REASON.FAILED_NOTIFICATION)
            self.assertEqual(message.retry, True)
            self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)
