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
import os
import time

import docker
from django.test import TestCase
from kafka import KafkaConsumer, TopicPartition

from consent_manager import settings
from hgw_common.messaging.sender import SendingError, create_sender


class TestKafkasender(TestCase):
    """
    Class the tests kafka sender
    """

    CONTAINER_NAME = "test_kafka"

    @classmethod
    def _stop_and_remove(cls):
        docker_client = docker.from_env()
        try:
            print("Getting container")
            container = docker_client.containers.get(cls.CONTAINER_NAME)
        except docker.errors.NotFound:
            pass
        else:
            print("Stopping container")
            container.stop()
            print("Removing container")
            container.remove()

    @classmethod
    def setUpClass(cls):
        cls._stop_and_remove()

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
    def tearDownClass(cls):
        cls._stop_and_remove()

    def test_correct_send(self):
        """
        Tests that, if the json encoding fails the send method raises an exception
        """
        sender = create_sender(settings.KAFKA_NOTIFICATION_TOPIC)
        message = {'message': 'text'}
        sender.send(message)

        consumer = KafkaConsumer(bootstrap_servers='kafka:9092')
        partition = TopicPartition('consent_manager_notification', 0)
        consumer.assign([partition])
        consumer.seek_to_beginning(partition)

        consumed_message = consumer.poll(timeout_ms=2000)[partition][0]
        self.assertEqual(json.loads(consumed_message.value.decode('utf-8')), message)

    def test_fail_kafka_producer_connection(self):
        """
        Tests that, if the kafka broker is not accessible, the send method raises an exception
        """
        docker_client = docker.from_env()
        container = docker_client.containers.get(self.CONTAINER_NAME)

        container.stop()
        sender = create_sender(settings.KAFKA_NOTIFICATION_TOPIC)
        self.assertFalse(sender.send({'message': 'fake_message'}))
        container.start()
