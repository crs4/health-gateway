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

import collections.abc
import logging
from ssl import SSLError
from typing import MutableSequence

from django.conf import settings
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from hgw_common.messaging import BrokerConnectionError, DeserializationError

from . import UnknownReceiver
from .deserializer import JSONDeserializer

logger = logging.getLogger('receiver')
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handlers = [logging.StreamHandler()]

for handler in handlers:
    handler.setLevel(logging.INFO)
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class GenericReceiver():
    """
    Generic sender abstract class. Subclass should implement the
    real notification process
    """

    def __iter__(self):
        raise NotImplementedError


class KafkaReceiver(GenericReceiver):
    """
    A very simple kafka receiver. It just creates a KafkaConsumer that consumes
    from the topic specified in input. To consume messages use the iterator
    """

    def __init__(self, topics, config, deserializer=JSONDeserializer):
        if isinstance(topics, collections.abc.MutableSequence):
            self.topics = topics
        else:
            self.topics = [topics]
        self.config = config
        try:
            self.consumer = KafkaConsumer(**self.config)
        except NoBrokersAvailable:
            logger.error("Cannot connect to kafka")
            raise BrokerConnectionError
        except SSLError:
            logger.error('SSLError connecting to kafka broker')
            raise BrokerConnectionError('SSLError connecting to kafka broker')


        self.consumer.subscribe(self.topics)
        logger.info("Subscribed to topic(s) %s", ", ".join(self.topics))
        self.wait_assignments()
        self.deserializer = deserializer()
        super(KafkaReceiver, self).__init__()

    def _force_assignment(self):
        # force the assignment update. See https://github.com/dpkp/kafka-python/issues/601
        self.consumer.poll()

    def wait_assignments(self):
        """
        Wait that the topic is assigned to the consumer
        """
        logger.info("Waiting for topic assignment")
        self._force_assignment()
        assignments = [tp.topic for tp in self.consumer.assignment()]
        while set(self.topics) < set(assignments):
            self._force_assignment()
            assignments = [tp.topic for tp in self.consumer.assignment()]
        logger.info("Topic(s) %s assigned", ', '.join(self.topics))

    def is_last(self):
        return self.consumer.position == self.consumer.highwater

    def __iter__(self):
        return self

    def __next__(self):
        msg = next(self.consumer)

        try:
            success = True
            data = self.deserializer.deserialize(msg.value)
        except DeserializationError:
            success = False
            try:
                data = msg.value.decode('utf-8')
            except UnicodeDecodeError:
                data = msg.value
        return {
            'success': success,
            'id': msg.offset,
            'queue': msg.topic,
            'key': msg.key.decode('utf-8') if msg.key is not None else None,
            'data': data
        }


def create_receiver(name, client_name, configuration_params, deserializer=JSONDeserializer):
    """
    Methods that returns the correct sender based on the settings file
    """
    if configuration_params['broker_type'] == 'kafka':
        kafka_config = {
            'bootstrap_servers': configuration_params['broker_url'],
            'group_id': client_name,
            'security_protocol': 'SSL' if configuration_params['ssl'] is True else 'PLAINTEXT',
            'ssl_check_hostname': True,
            'ssl_cafile': configuration_params['ca_cert'],
            'ssl_certfile': configuration_params['client_cert'],
            'ssl_keyfile': configuration_params['client_key'],
        }

        return KafkaReceiver(name, kafka_config, deserializer)

    raise UnknownReceiver("Cannot instantiate a sender")
