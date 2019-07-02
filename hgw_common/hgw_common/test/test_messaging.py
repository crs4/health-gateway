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
from unittest import TestCase

from kafka.errors import (KafkaError, KafkaTimeoutError,
                          TopicAuthorizationFailedError)
from mock import Mock, patch

from hgw_common.messaging import UnknownSender
from hgw_common.messaging.sender import KafkaSender, get_sender
from hgw_common.messaging.serializer import JSONSerializer

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
        Tests that, when the sender is unknown the get_sender function raises an error
        """
        self.assertRaises(UnknownSender, get_sender, TOPIC)

    @patch('hgw_common.messaging.sender.settings', SettingsSSLMock)
    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_get_kafka_ssl_sender(self, mocked_kafka_producer):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is Kafkasender
        """
        sender = get_sender(TOPIC)
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
        sender = get_sender(TOPIC)
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
        sender = get_sender(TOPIC)
        self.assertTrue(sender.send('message'))
        mocked_kafka_producer().send.assert_called_once()
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][0][0], TOPIC)
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][1]['value'], b'"message"')

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_no_broker(self):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is KafkaSender
        """
        sender = get_sender(TOPIC)
        self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_no_topic_authorization(self):
        """
        Tests failuer in case of no topic authorization
        """
        future_mock = Mock()
        future_mock.get.side_effect = TopicAuthorizationFailedError
        with patch('hgw_common.messaging.sender.KafkaProducer.send', return_value=future_mock):
            sender = get_sender(TOPIC)
            self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_kafka_error(self):
        """
        Tests failure in case of KafkaError
        """
        future_mock = Mock()
        future_mock.get.side_effect = KafkaError
        with patch('hgw_common.messaging.sender.KafkaProducer.send', return_value=future_mock):
            sender = get_sender(TOPIC)
            self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_timeout_error(self):
        """
        Tests failuer in case of no topic authorization
        """
        with patch('hgw_common.messaging.sender.KafkaProducer.send', side_effect=KafkaTimeoutError):
            sender = get_sender(TOPIC)
            self.assertFalse(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_send_message_fail_serialization_error(self):
        """
        Tests failure in case of SerializationError
        """
        sender = get_sender(TOPIC)
        # a set is not json serializable so it will raise a TypeError and consequently a serialization error
        self.assertFalse(sender.send({'message'}))
