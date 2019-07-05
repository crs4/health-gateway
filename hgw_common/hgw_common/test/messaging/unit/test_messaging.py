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

"""
Tests senders
"""
import json
from unittest import TestCase

from kafka.errors import (KafkaError, KafkaTimeoutError,
                          TopicAuthorizationFailedError)
from mock import Mock, patch

from hgw_common.messaging import BrokerConnectionError, UnknownSender
from hgw_common.messaging.deserializer import JSONDeserializer
from hgw_common.messaging.receiver import KafkaReceiver, create_receiver
from hgw_common.messaging.sender import KafkaSender, create_sender
from hgw_common.messaging.serializer import JSONSerializer
from hgw_common.utils.mocks import MockKafkaConsumer, MockMessage

TOPIC = 'topic'


class SettingsSSLMock():
    NOTIFICATION_TYPE = 'kafka'
    KAFKA_BROKER = 'localhost:9092'
    KAFKA_SSL = True
    KAFKA_CA_CERT = 'cacert'
    KAFKA_CLIENT_CERT = 'client_cert'
    KAFKA_CLIENT_KEY = 'client_key'


class SettingsNoSSLMock():
    NOTIFICATION_TYPE = 'kafka'
    KAFKA_BROKER = 'localhost:9092'


class TestSenders(TestCase):
    """
    Test senders class
    """

    @patch('hgw_common.messaging.sender.settings.NOTIFICATION_TYPE', 'unknown')
    @patch('hgw_common.messaging.sender.settings')
    def test_raise_unknown_sender(self, mocked_settings):
        """
        Tests that, when the sender is unknown the factory function raises an error
        """
        self.assertRaises(UnknownSender, create_sender, TOPIC)

    @patch('hgw_common.messaging.sender.settings', SettingsSSLMock)
    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_get_kafka_ssl_sender(self, mocked_kafka_producer):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is Kafkasender
        """
        sender = create_sender(TOPIC)
        self.assertIsInstance(sender, KafkaSender)
        expected_config = {
            'bootstrap_servers': SettingsSSLMock.KAFKA_BROKER,
            'security_protocol': 'SSL',
            'ssl_check_hostname': True,
            'ssl_cafile': SettingsSSLMock.KAFKA_CA_CERT,
            'ssl_certfile': SettingsSSLMock.KAFKA_CLIENT_CERT,
            'ssl_keyfile': SettingsSSLMock.KAFKA_CLIENT_KEY
        }
        self.assertEqual(sender.topic, TOPIC)
        self.assertIsInstance(sender.serializer, JSONSerializer)
        self.assertDictEqual(expected_config, sender.config)

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_get_kafka_no_ssl_sender(self, mocked_kafka_producer):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is Kafkasender
        """
        sender = create_sender(TOPIC)
        self.assertIsInstance(sender, KafkaSender)
        expected_config = {
            'bootstrap_servers': SettingsSSLMock.KAFKA_BROKER,
            'security_protocol': 'PLAINTEXT',
            'ssl_check_hostname': True,
            'ssl_cafile': None,
            'ssl_certfile': None,
            'ssl_keyfile': None
        }
        self.assertEqual(sender.topic, TOPIC)
        self.assertIsInstance(sender.serializer, JSONSerializer)
        self.assertDictEqual(expected_config, sender.config)

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_message_send(self, mocked_kafka_producer):
        sender = create_sender(TOPIC)
        self.assertTrue(sender.send('message'))
        mocked_kafka_producer().send.assert_called_once()
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][0][0], TOPIC)
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][1]['data'], b'"message"')

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_no_broker(self):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is KafkaSender
        """
        sender = create_sender(TOPIC)
        self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_no_topic_authorization(self):
        """
        Tests failuer in case of no topic authorization
        """
        future_mock = Mock()
        future_mock.get.side_effect = TopicAuthorizationFailedError
        with patch('hgw_common.messaging.sender.KafkaProducer.send', return_value=future_mock):
            sender = create_sender(TOPIC)
            self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_kafka_error(self):
        """
        Tests failure in case of KafkaError
        """
        future_mock = Mock()
        future_mock.get.side_effect = KafkaError
        with patch('hgw_common.messaging.sender.KafkaProducer.send', return_value=future_mock):
            sender = create_sender(TOPIC)
            self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_timeout_error(self):
        """
        Tests failuer in case of no topic authorization
        """
        with patch('hgw_common.messaging.sender.KafkaProducer.send', side_effect=KafkaTimeoutError):
            sender = create_sender(TOPIC)
            self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_serialization_error(self):
        """
        Tests failure in case of SerializationError
        """
        sender = create_sender(TOPIC)
        # a set is not json serializable so it will raise a TypeError and consequently a serialization error
        self.assertFalse(sender.send({'message'}))


class TestReceiver(TestCase):
    """
    Test senders class
    """

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, topic, json_enc=True, encoding='utf-8'):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        topic = topic.encode('utf-8')
        key = 'key'
        mock_kc_klass.MESSAGES = {i: MockMessage(key=key,
                                                 offset=i,
                                                 topic=topic,
                                                 value=json.dumps(m).encode(encoding) if json_enc is True else m.encode('utf-8'))
                                  for i, m in enumerate(messages)}

    @patch('hgw_common.messaging.receiver.settings', SettingsSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsSSLMock)
    def test_create_kafka_receiver(self):
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            receiver = create_receiver(TOPIC, 'test_client')
        self.assertIsInstance(receiver, KafkaReceiver)
        expected_config = {
            'bootstrap_servers': SettingsSSLMock.KAFKA_BROKER,
            'group_id': 'test_client',
            'security_protocol': 'SSL',
            'ssl_check_hostname': True,
            'ssl_cafile': SettingsSSLMock.KAFKA_CA_CERT,
            'ssl_certfile': SettingsSSLMock.KAFKA_CLIENT_CERT,
            'ssl_keyfile': SettingsSSLMock.KAFKA_CLIENT_KEY
        }
        self.assertEqual(receiver.topic, TOPIC)
        self.assertIsInstance(receiver.deserializer, JSONDeserializer)
        self.assertDictEqual(expected_config, receiver.config)

    @patch('hgw_common.messaging.receiver.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_create_kafka_receiver_no_ssl(self):
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            receiver = create_receiver(TOPIC, 'test_client')

        self.assertIsInstance(receiver, KafkaReceiver)
        expected_config = {
            'bootstrap_servers': SettingsNoSSLMock.KAFKA_BROKER,
            'group_id': 'test_client',
            'security_protocol': 'PLAINTEXT',
            'ssl_check_hostname': True,
            'ssl_cafile': None,
            'ssl_certfile': None,
            'ssl_keyfile': None
        }
        self.assertEqual(receiver.topic, TOPIC)
        self.assertIsInstance(receiver.deserializer, JSONDeserializer)
        self.assertDictEqual(expected_config, receiver.config)

    @patch('hgw_common.messaging.receiver.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_message_receive_no_broker_available(self):
        """
        Test correct message receiving
        """
        self.assertRaises(BrokerConnectionError, create_receiver, TOPIC, 'test_client')

    @patch('hgw_common.messaging.receiver.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_message_receive(self):
        """
        Test correct message receiving
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = ['message_{}'.format(i) for i in range(10)]

            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, TOPIC)

            receiver = create_receiver(TOPIC, 'test_client')

            for i, m in enumerate(receiver):
                self.assertEqual(m['success'], True)
                self.assertEqual(m['id'], i)
                self.assertEqual(m['data'], 'message_{}'.format(i))
                self.assertEqual(m['queue'], TOPIC)

    @patch('hgw_common.messaging.receiver.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_deserialization_error_to_json_decoding(self):
        """
        Test correct message receiving
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = ['(a)']

            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, TOPIC, False)

            receiver = create_receiver(TOPIC, 'test_client')

            for i, m in enumerate(receiver):
                self.assertEqual(m['id'], i)
                self.assertEqual(m['data'], b'(a)')  # notice the byte
                self.assertEqual(m['queue'], TOPIC)
                self.assertEqual(m['success'], False)
    
    @patch('hgw_common.messaging.receiver.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_consume_message_fail_to_unicode_error(self):
        """
        Tests failure because of unicode decoding error. In this case the message won't be saved on db
        """
        messages = ['(a)']
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, TOPIC, True, 'utf-16')
            
            receiver = create_receiver(TOPIC, 'test_client')

            for i, m in enumerate(receiver):
                self.assertEqual(m['id'], i)
                self.assertEqual(m['data'], '"(a)"'.encode('utf-16'))
                self.assertEqual(m['queue'], TOPIC)
                self.assertEqual(m['success'], False)
