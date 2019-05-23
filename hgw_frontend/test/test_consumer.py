import json
import os

from django.test import TestCase, client
from mock.mock import call, patch

from hgw_common.models import Profile
from hgw_common.utils.mocks import MockKafkaConsumer, MockMessage
from hgw_frontend.management.commands.backend_notification_consumer import \
    Command
from hgw_frontend.models import Channel, ConsentConfirmation, Source
from hgw_frontend.settings import (KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                   KAFKA_SOURCE_NOTIFICATION_TOPIC)

from . import PROFILE_1, PROFILE_2, SOURCE_3_ID, SOURCE_3_NAME


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
        key = 'key'
        mock_kc_klass.MESSAGES = {i: MockMessage(key=key, offset=i, topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_correct_source_add(self):
        """
        Tests that the message is consumed and that a new Source is created in the db
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.source_notification_messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            Command().handle()

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
        with patch('hgw_common.utils.KafkaConsumer',
                   MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            Command().handle()

            for message in messages:
                sources = Source.objects.filter(source_id=message['source_id'])
                self.assertEqual(sources.count(), 1)
                source = sources.first()
                self.assertEqual(source.source_id, message['source_id'])
                self.assertEqual(source.name, message['name'])
                self.assertEqual(source.profile.code, message['profile']['code'])
                self.assertEqual(source.profile.version, message['profile']['version'])
                self.assertEqual(source.profile.payload, message['profile']['payload'])

    def test_failure_to_json_decoding(self):
        """
        Tests that the message is consumed but json decoding fails
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            messages = ['(a)']
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, False)
            Command().handle()

            self.assertEqual(Source.objects.count(), 0)

    def test_source_failure_to_message_structure(self):
        """
        Tests that the message is consumed but it doesn't have the correct structure
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
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
            Command().handle()

            self.assertEqual(Source.objects.count(), 0)

    def test_source_failure_to_invalid_profile_structure(self):
        """
        Tests that the message is consumed but it doesn't have the correct structure
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
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
            Command().handle()

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
        key = 'key'
        mock_kc_klass.MESSAGES = {i: MockMessage(key=key, offset=i, topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_correct_connector_notification(self):
        """
        Tests that the message is received and the status of the corresponding Channel is set to ACTIVE
        """
        for connector in self.connector_notification_messages:
            channel = ConsentConfirmation.objects.get(consent_id=connector['channel_id']).channel
            self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.connector_notification_messages,
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)

            Command().handle()

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

        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, self.connector_notification_messages,
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            Command().handle()

            for connector in self.connector_notification_messages:
                channel = ConsentConfirmation.objects.get(consent_id=connector['channel_id']).channel
                self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)

    def test_failure_because_of_channel_not_found(self):
        """
        Tests that the message is received but nothing happens because the channel was not found
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, [{'channel_id': 'wrong'}],
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            Command().handle()

    def test_failure_because_of_wrong_structure(self):
        """
        Tests that the message is received but nothing happens because the structure of the message was wrong
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, [{'wrong': 'str'}, 'wrong'],
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            Command().handle()
