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

from kafka import KafkaConsumer, TopicPartition
from kafka.errors import NoBrokersAvailable

from hgw_common.messaging import (BrokerConnectionError, DeserializationError,
                                  TopicNotAssigned)

from . import UnknownReceiver, NotInRangeError
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

        self.config.update({
            'auto_offset_reset': 'earliest',
            'auto_commit_interval_ms': 2000
        })
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

    def _construct_message(self, msg):
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

    def _go_to_id(self, message_id, topic, partition):
        tp = TopicPartition(topic, partition)
        first_offset = self.get_first_id(topic, partition)
        last_offset = self.get_last_id(topic, partition)
        if first_offset <= message_id <= last_offset:
            self.consumer.seek(tp, message_id)
        else:
            return NotInRangeError()

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

    def get_current_id(self, topic, partition=0):
        """
        Get the id of the last consumed message
        """
        tp = TopicPartition(topic, partition)
        return self.consumer.position(tp) - 1

    def get_first_id(self, topic, partition=0):
        """
        Get the id of the fist available object in a partition
        """
        tp = TopicPartition(topic, partition)
        return self.consumer.beginning_offsets([tp])[tp]

    def get_last_id(self, topic, partition=0):
        tp = TopicPartition(topic, partition)
        return self.consumer.end_offsets([tp])[tp]

    def get_by_id(self, message_id, topic, partition=0):
        self._go_to_id(message_id, topic, partition)
        msg = next(self.consumer)
        return self._construct_message(msg)

    def get_range(self, first_id, last_id, topic, partition=0):
        """
        Return messages from the :param:`first_id` to the :param:`last_id`. The :param:`last_id` is not included.
        """
        if last_id < first_id:
            raise Exception

        if last_id > self.get_last_id(topic, partition):
            last_id = self.get_last_id(topic, partition)
        if first_id < self.get_first_id(topic, partition):
            first_id = self.get_first_id(topic, partition)

        msgs = []
        for msg_id in range(first_id, last_id):
            msgs.append(self.get_by_id(msg_id, topic, partition))
        return msgs

    def __iter__(self):
        return self

    def __next__(self):
        msg = next(self.consumer)
        return self._construct_message(msg)

    def __del__(self):
        self.consumer.close()


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
