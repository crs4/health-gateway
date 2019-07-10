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

from hgw_common.messaging.receiver import create_receiver
from hgw_common.messaging.sender import create_sender

TOPIC_KEY = 'test-topic'
TOPIC_NO_KEY = 'test-topic-no-key'
CLIENT_KAFKA_CACERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/kafka.chain.cert.pem')
CLIENT_KAFKA_CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/client/cert.pem')
CLIENT_KAFKA_KEY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/client/key.pem')


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

        extra_hosts = {"kafka": "127.0.1.1"}
        ports = {"9092": "9092", "9093": "9093"}

        docker_client.containers.run("crs4/kafka",
                                     name=cls.CONTAINER_NAME,
                                     environment=container_env,
                                     volumes=container_volumes,
                                     extra_hosts=extra_hosts,
                                     ports=ports,
                                     detach=True)

        print("Waiting Kafka to be ready")
        time.sleep(10)

    @classmethod
    def setUpClass(cls):
        cls._stop_and_remove()
        cls._create_container()

    @classmethod
    def tearDownClass(cls):
        cls._stop_and_remove()

    def setUp(self):
        self.config_params_no_ssl = {
            'broker_type': 'kafka',
            'broker_url': 'kafka:9092',
            'ssl': False,
            'ca_cert': None,
            'client_cert': None,
            'client_key': None
        }
        self.config_params_ssl = {
            'broker_type': 'kafka',
            'broker_url': 'kafka:9092',
            'ssl': True,
            'ca_cert': CLIENT_KAFKA_CACERT,
            'client_cert': CLIENT_KAFKA_CERT,
            'client_key': CLIENT_KAFKA_KEY
        }
        self.message_num = 10
        self._send_messages(TOPIC_KEY, 'key')
        self._send_messages(TOPIC_NO_KEY, None)

    def _send_messages(self, topic, key):
        def sender_fun(num):
            sender = create_sender(self.config_params_no_ssl)
            for _ in range(num):
                sender.send(topic, 'message', key=key)

        sender_process = multiprocessing.Process(target=sender_fun, args=(self.message_num,))
        sender_process.start()
        sender_process.join()

    def test_receive_01_none_key(self):
        """
        Test correct message receiving
        """
        receiver = create_receiver(TOPIC_NO_KEY, 'test_receive_none_key', self.config_params_no_ssl)
        for i, m in enumerate(receiver):
            self.assertEqual(m['success'], True)
            self.assertEqual(m['id'], i)
            self.assertEqual(m['data'], 'message')
            self.assertEqual(m['key'], None)
            self.assertEqual(m['queue'], TOPIC_NO_KEY)
            if i + 1 == self.message_num:
                break

    def test_receive_02_with_key(self):
        """
        Test correct message receiving
        """
        receiver = create_receiver(TOPIC_KEY, 'test_receive_with_key', self.config_params_no_ssl)
        for i, m in enumerate(receiver):
            self.assertEqual(m['success'], True)
            self.assertEqual(m['id'], i)
            self.assertEqual(m['data'], 'message')
            self.assertEqual(m['key'], 'key')
            self.assertEqual(m['queue'], TOPIC_KEY)
            if i + 1 == self.message_num:
                break

    def test_receive_03_by_id(self):
        """
        Test correct message receiving
        """
        receiver = create_receiver(TOPIC_NO_KEY, 'test_receive_by_id', self.config_params_no_ssl)
        message = receiver.get_by_id(3, TOPIC_NO_KEY)
        self.assertEqual(message['success'], True)
        self.assertEqual(message['id'], 3)
        self.assertEqual(message['data'], 'message')
        self.assertEqual(message['key'], None)
        self.assertEqual(message['queue'], TOPIC_NO_KEY)

    def test_receive_04_range(self):
        """
        Test correct message receiving of messages in a range of id
        """
        receiver = create_receiver(TOPIC_NO_KEY, 'test_receive_range', self.config_params_no_ssl)
        messages = receiver.get_range(2, 5, TOPIC_NO_KEY)
        self.assertEqual(len(messages), 4)
        for index, message in enumerate(messages):
            self.assertEqual(message['success'], True)
            self.assertEqual(message['id'], index + 2)
            self.assertEqual(message['data'], 'message')
            self.assertEqual(message['key'], None)
            self.assertEqual(message['queue'], TOPIC_NO_KEY)

    def test_receive_05_restart_from_last_offset(self):
        """
        Test that when the receiver is deleted and recreated, it restarts consuming messages from the last consumed offset
        """
        client_name = 'test_restart_from_last_offset'
        receiver = create_receiver(TOPIC_NO_KEY, client_name, self.config_params_no_ssl)
        # first we create a receiver that consumes 5 messages
        for index, message in enumerate(receiver):
            if index == self.message_num // 2:
                break
            self.assertEqual(message['id'], index)
        self.assertEqual(receiver.get_current_id(TOPIC_NO_KEY), self.message_num//2)
        del receiver
        # create a new receiver that substitute the first
        receiver = create_receiver(TOPIC_NO_KEY, client_name, self.config_params_no_ssl)
        self.assertEqual(receiver.get_current_id(TOPIC_NO_KEY), self.message_num//2)

    def test_send(self):
        """
        Test sending message
        """
        sender = create_sender(self.config_params_no_ssl)
        for _ in range(100):
            self.assertTrue(TOPIC_KEY, sender.send(TOPIC_KEY, 'message'))

    def test_send_with_key(self):
        """
        Test sending message specifying a key
        """
        sender = create_sender(self.config_params_no_ssl)
        for _ in range(100):
            self.assertTrue(TOPIC_NO_KEY, sender.send(TOPIC_NO_KEY, 'message', key='key'))
