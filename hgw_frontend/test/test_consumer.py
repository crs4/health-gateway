import json

from django.test import TestCase
from mock.mock import call, patch

from hgw_common.models import (FailedMessages, Profile, ProfileDomain,
                               ProfileSection)
from hgw_common.utils.mocks import MockKafkaConsumer, MockMessage
from hgw_frontend.management.commands.backend_notification_consumer import \
    Command as BackendNotificationCommand
from hgw_frontend.management.commands.consent_manager_notification_consumer import (FAILED_MESSAGE_TYPE,
                                                                                    FAILED_REASON)
from hgw_frontend.management.commands.consent_manager_notification_consumer import \
    Command as ConsentNotificationCommand
from hgw_frontend.models import Channel, ConsentConfirmation, Source
from hgw_frontend.settings import (KAFKA_CHANNEL_NOTIFICATION_TOPIC,
                                   KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                   KAFKA_SOURCE_NOTIFICATION_TOPIC)

from . import (CORRECT_CONSENT_ID, DEST_1_ID, DEST_1_NAME, DEST_PUBLIC_KEY,
               PERSON_ID, PROFILE_1, PROFILE_2, SOURCE_1_ID, SOURCE_1_NAME,
               SOURCE_3_ID, SOURCE_3_NAME)


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
            BackendNotificationCommand().handle()

            for message in self.source_notification_messages:
                sources = Source.objects.filter(source_id=message['source_id'])
                self.assertEqual(sources.count(), 1)
                source = sources.first()
                self.assertEqual(source.source_id, message['source_id'])
                self.assertEqual(source.name, message['name'])
                self.assertEqual(source.profile.code, message['profile']['code'])
                self.assertEqual(source.profile.version, message['profile']['version'])
                domains = ProfileDomain.objects.filter(profile=source.profile)
                self.assertEqual(domains.count(), 1)
                self.assertEqual(domains[0].code, PROFILE_1['domains'][0]['code'])
                self.assertEqual(domains[0].name, PROFILE_1['domains'][0]['name'])
                self.assertEqual(domains[0].coding_system, PROFILE_1['domains'][0]['coding_system'])
                sections = ProfileSection.objects.filter(profile_domain=domains[0])
                self.assertEqual(sections.count(), 1)
                self.assertEqual(sections[0].code, PROFILE_1['domains'][0]['sections'][0]['code'])
                self.assertEqual(sections[0].name, PROFILE_1['domains'][0]['sections'][0]['name'])
                self.assertEqual(sections[0].coding_system, PROFILE_1['domains'][0]['sections'][0]['coding_system'])

    def test_correct_source_update(self):
        """
        Tests that the message is consumed and that the source is updated
        """
        # Adds the source to update
        profile = Profile.objects.create(code='PROF_LAB_0001', version='1.0.0')
        domain = ProfileDomain.objects.create(name='Laboratory', code='LAB', coding_system='local', profile=profile)
        section = ProfileSection.objects.create(name='Coagulation Studies', code='COS', coding_system='local', profile_domain=domain)
        Source.objects.create(source_id=SOURCE_3_ID, name=SOURCE_3_NAME, profile=profile)
        messages = [{
            'source_id': SOURCE_3_ID,
            'name': 'NEW_NAME',
            'profile': PROFILE_2
        }]
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, True)
            BackendNotificationCommand().handle()

            for message in messages:
                sources = Source.objects.filter(source_id=message['source_id'])
                self.assertEqual(sources.count(), 1)
                source = sources.first()
                self.assertEqual(source.source_id, message['source_id'])
                self.assertEqual(source.name, message['name'])
                self.assertEqual(source.profile.code, message['profile']['code'])
                self.assertEqual(source.profile.version, message['profile']['version'])
                domains = ProfileDomain.objects.filter(profile=source.profile)
                self.assertEqual(domains.count(), 1)
                self.assertEqual(domains[0].code, PROFILE_2['domains'][0]['code'])
                self.assertEqual(domains[0].name, PROFILE_2['domains'][0]['name'])
                self.assertEqual(domains[0].coding_system, PROFILE_2['domains'][0]['coding_system'])
                sections = ProfileSection.objects.filter(profile_domain=domains[0])
                self.assertEqual(sections.count(), 1)
                self.assertEqual(sections[0].code, PROFILE_2['domains'][0]['sections'][0]['code'])
                self.assertEqual(sections[0].name, PROFILE_2['domains'][0]['sections'][0]['name'])
                self.assertEqual(sections[0].coding_system, PROFILE_2['domains'][0]['sections'][0]['coding_system'])

    def test_failure_to_json_decoding(self):
        """
        Tests that the message is consumed but json decoding fails
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            messages = ['(a)']
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                         KAFKA_SOURCE_NOTIFICATION_TOPIC, False)
            BackendNotificationCommand().handle()

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
            BackendNotificationCommand().handle()

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
            BackendNotificationCommand().handle()

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

            BackendNotificationCommand().handle()

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
            BackendNotificationCommand().handle()

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
            BackendNotificationCommand().handle()

    def test_failure_because_of_wrong_structure(self):
        """
        Tests that the message is received but nothing happens because the structure of the message was wrong
        """
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, [{'wrong': 'str'}, 'wrong'],
                                         KAFKA_CONNECTOR_NOTIFICATION_TOPIC, True)
            BackendNotificationCommand().handle()


class TestConsentConsumer(TestCase):
    """
    Test consumer for consent updates from consent manager
    """

    fixtures = ['test_data.json']

    def setUp(self):
        self.in_messages = [{
            'consent_id': CORRECT_CONSENT_ID,
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
            'start_validity': None,
            'expire_validity': None
        }]
        self.out_messages = [{
            'channel_id': CORRECT_CONSENT_ID,
            'source_id': SOURCE_1_ID,
            'destination': {
                'destination_id': DEST_1_ID,
                'kafka_public_key': DEST_PUBLIC_KEY
            },
            'profile': PROFILE_1,
            'person_id': PERSON_ID,
            'start_validity': None,
            'expire_validity': None
        }]
        return super(TestConsentConsumer, self).setUp()

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, topic, json_enc=True, encoding='utf-8'):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        key = 'key'
        mock_kc_klass.MESSAGES = {i: MockMessage(key=key, offset=i, topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    def test_correct_notification(self):
        self.set_mock_kafka_consumer(MockKafkaConsumer, self.in_messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        for consent in self.in_messages:
            channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
            self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)
        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.notifier.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()
            for index, consent in enumerate(self.in_messages):
                channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
                self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)
                self.assertEqual(channel.source, Source.objects.get(source_id=consent['source']['id']))
                self.assertEqual(channel.flow_request.profile, Profile.objects.get(code=consent['profile']['code']))
                self.assertEqual(channel.flow_request.person_id, consent['person_id'])
                self.assertEqual(MockKafkaProducer().send.call_args_list[index][0][0], KAFKA_CHANNEL_NOTIFICATION_TOPIC)
                self.assertDictEqual(json.loads(MockKafkaProducer().send.call_args_list[index][1]['value'].decode('utf-8')),
                                     self.out_messages[index])
            self.assertEqual(FailedMessages.objects.count(), 0)

    def test_failure_because_of_wrong_input_structure(self):
        """
        Test that no action has been performed because the input message misses some needed key
        """
        messages = []
        for key in self.in_messages[0]:
            message = self.in_messages[0].copy()
            del message[key]
            messages.append(message)

        self.set_mock_kafka_consumer(MockKafkaConsumer, messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.notifier.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()
            for consent in self.in_messages:
                channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
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
        self.in_messages[0]['consent_id'] = 'UNKNOWN'
        self.set_mock_kafka_consumer(MockKafkaConsumer, self.in_messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.notifier.KafkaProducer') as MockKafkaProducer:
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
        self.in_messages[0]['person_id'] = 'UNKNOWN'
        self.set_mock_kafka_consumer(MockKafkaConsumer, self.in_messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.notifier.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()
            for consent in self.in_messages:
                channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
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
        self.in_messages[0]['source']['id'] = 'UNKNOWN'
        self.set_mock_kafka_consumer(MockKafkaConsumer, self.in_messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer), \
                patch('hgw_common.notifier.KafkaProducer') as MockKafkaProducer:
            ConsentNotificationCommand().handle()
            for consent in self.in_messages:
                channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
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
        self.set_mock_kafka_consumer(MockKafkaConsumer, self.in_messages,
                                     KAFKA_CHANNEL_NOTIFICATION_TOPIC, True)

        with patch('hgw_common.utils.KafkaConsumer', MockKafkaConsumer):
            ConsentNotificationCommand().handle()
            for consent in self.in_messages:
                channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
                self.assertEqual(channel.status, Channel.WAITING_SOURCE_NOTIFICATION)
            self.assertEqual(FailedMessages.objects.count(), 1)
            message = FailedMessages.objects.first()
            self.assertEqual(message.reason, FAILED_REASON.FAILED_NOTIFICATION)
            self.assertEqual(message.retry, True)
            self.assertEqual(message.message_type, FAILED_MESSAGE_TYPE)
