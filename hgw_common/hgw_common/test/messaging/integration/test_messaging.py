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
import multiprocessing
import os
import time
from unittest import TestCase

import docker
from mock.mock import patch

from hgw_common.messaging import UnknownSender
from hgw_common.messaging.receiver import KafkaReceiver, create_receiver
from hgw_common.messaging.sender import KafkaSender, create_sender
from hgw_common.messaging.serializer import JSONSerializer
from hgw_common.utils import create_broker_parameters_from_settings

TOPIC_KEY = 'test-topic'
TOPIC_NO_KEY = 'test-topic-no-key'
CLIENT_KAFKA_CACERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/kafka.chain.cert.pem')
CLIENT_KAFKA_CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/client/cert.pem')
CLIENT_KAFKA_KEY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/client/key.pem')


class SettingsSSLMock():
    NOTIFICATION_TYPE = 'kafka'
    KAFKA_BROKER = 'kafka:9093'
    KAFKA_SSL = True
    KAFKA_CA_CERT = CLIENT_KAFKA_CACERT
    KAFKA_CLIENT_CERT = CLIENT_KAFKA_CERT
    KAFKA_CLIENT_KEY = CLIENT_KAFKA_KEY


class SettingsNoSSLMock():
    NOTIFICATION_TYPE = 'kafka'
    KAFKA_BROKER = 'kafka:9092'


class TestMessaging(TestCase):
    """
    Test senders class
    """

    CONTAINER_NAME = "test_kafka"

    @classmethod
    def _get_container(cls):
        docker_client = docker.from_env()
        try:
            print("Getting container")
            container = docker_client.containers.get(cls.CONTAINER_NAME)
        except docker.errors.NotFound:
            print("Container not found")
            return None
        else:
            return container

    @classmethod
    def _stop_and_remove(cls):
        container = cls._get_container()
        if container:
            print("Stopping container")
            container.stop()
            print("Removing container")
            container.remove()

    @classmethod
    def _create_container(cls):
        docker_client = docker.from_env()

        container_env = [
            "KAFKA_BROKER_ID=1",
            "KAFKA_PORT=9092",
            "KAFKA_SSL_PORT=9093",
            "KAFKA_ADVERTISED_HOST_NAME=kafka",
            "KAFKA_CREATE_TOPICS=true",
            "TZ=CET"
        ]

        certs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/server/')
        kafka_topic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kafka_topics.json')
        container_volumes = {
            certs_path: {
                'bind': '/container/certs/',
                'mode': 'rw'
            },
            kafka_topic_path: {
                'bind': '/kafka_topics.json',
                'mode': 'rw'
            }
        }

        extra_hosts = {
            "kafka": "127.0.1.1"
        }

        ports = {
            "9092": "9092",
            "9093": "9093"
        }

        docker_client.containers.run("crs4/kafka",
                                     name=cls.CONTAINER_NAME,
                                     environment=container_env,
                                     volumes=container_volumes,
                                     extra_hosts=extra_hosts,
                                     ports=ports,
                                     detach=True)

        print("Waiting Kafka to be ready")
        time.sleep(20)

    @classmethod
    def setUpClass(cls):
        cls._stop_and_remove()
        cls._create_container()

    @classmethod
    def tearDownClass(cls):
        cls._stop_and_remove()

    @patch('hgw_common.utils.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_message_receive_none_key(self):
        """
        Test correct message receiving
        """
        message_num = 10

        def sender_fun(num):
            sender = create_sender(TOPIC_NO_KEY)
            for _ in range(num):
                sender.send('message')

        receiver = create_receiver(TOPIC_NO_KEY, 'test_client_no_key', create_broker_parameters_from_settings())

        sender_process = multiprocessing.Process(target=sender_fun, args=(message_num,))
        sender_process.start()

        for i, m in enumerate(receiver):
            self.assertEqual(m['success'], True)
            self.assertEqual(m['id'], i)
            self.assertEqual(m['data'], 'message')
            self.assertEqual(m['key'], None)
            self.assertEqual(m['queue'], TOPIC_NO_KEY)
            if i + 1 == message_num:
                break

        sender_process.terminate()
        sender_process.join()

    @patch('hgw_common.utils.settings', SettingsNoSSLMock)
    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_message_receive_with_key(self):
        """
        Test correct message receiving
        """
        message_num = 10

        def sender_fun(num):
            sender = create_sender(TOPIC_KEY)
            for _ in range(num):
                sender.send('message', key='key')

        receiver = create_receiver(TOPIC_KEY, 'test_client_key', create_broker_parameters_from_settings())

        sender_process = multiprocessing.Process(target=sender_fun, args=(message_num,))
        sender_process.start()

        for i, m in enumerate(receiver):
            self.assertEqual(m['success'], True)
            self.assertEqual(m['id'], i)
            self.assertEqual(m['data'], 'message')
            self.assertEqual(m['key'], b'key')
            self.assertEqual(m['queue'], TOPIC_KEY)
            if i + 1 == message_num:
                break

    @patch('hgw_common.messaging.sender.settings.NOTIFICATION_TYPE', 'unknown')
    @patch('hgw_common.messaging.sender.settings')
    def test_raise_unknown_sender(self, mocked_settings):
        """
        Tests that, when the sender is unknown the factory function raises an error
        """
        self.assertRaises(UnknownSender, create_sender, TOPIC_NO_KEY)

    @patch('hgw_common.messaging.sender.settings', SettingsSSLMock)
    def test_get_kafka_ssl_sender(self):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is Kafkasender
        """
        sender = create_sender(TOPIC_NO_KEY)
        self.assertIsInstance(sender, KafkaSender)
        expected_config = {
            'bootstrap_servers': SettingsSSLMock.KAFKA_BROKER,
            'security_protocol': 'SSL',
            'ssl_check_hostname': True,
            'ssl_cafile': SettingsSSLMock.KAFKA_CA_CERT,
            'ssl_certfile': SettingsSSLMock.KAFKA_CLIENT_CERT,
            'ssl_keyfile': SettingsSSLMock.KAFKA_CLIENT_KEY
        }
        self.assertEqual(sender.topic, TOPIC_NO_KEY)
        self.assertIsInstance(sender.serializer, JSONSerializer)
        self.assertDictEqual(expected_config, sender.config)

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_get_kafka_no_ssl_sender(self):
        """
        Tests that, when the settings specifies a kafka sender, the instantiated sender is Kafkasender
        """
        sender = create_sender(TOPIC_NO_KEY)
        self.assertIsInstance(sender, KafkaSender)
        expected_config = {
            'bootstrap_servers': SettingsNoSSLMock.KAFKA_BROKER,
            'security_protocol': 'PLAINTEXT',
            'ssl_check_hostname': True,
            'ssl_cafile': None,
            'ssl_certfile': None,
            'ssl_keyfile': None
        }
        self.assertEqual(sender.topic, TOPIC_NO_KEY)
        self.assertIsInstance(sender.serializer, JSONSerializer)
        self.assertDictEqual(expected_config, sender.config)

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_message_send(self):
        """
        Test sending message
        """
        sender = create_sender(TOPIC_NO_KEY)
        for _ in range(100):
            self.assertTrue(sender.send('message'))

    @patch('hgw_common.messaging.sender.settings', SettingsNoSSLMock)
    def test_message_send_with_key(self):
        """
        Test sending message specifying a key
        """
        sender = create_sender(TOPIC_NO_KEY)
        for _ in range(100):
            self.assertTrue(sender.send('message', key='key'))
