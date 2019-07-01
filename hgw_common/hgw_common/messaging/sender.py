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

import json
from json.decoder import JSONDecodeError
from traceback import format_exc

from django.conf import settings
from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError, NoBrokersAvailable, \
    TopicAuthorizationFailedError

from hgw_common.utils import get_logger

logger = get_logger(__file__)


class UnknownSender(Exception):
    """
    Exception to be raised when it was impossible to get the instantiate the correct sender
    """


class SendingError(Exception):
    """
    Exception to be raised when a notification error happens
    """


class GenericSender():
    """
    Generic sender abstract class. Subclass should implement the
    real notification process
    """

    def notify(self, message):
        """
        Abstract notify method. Subclasses should implement this
        """
        raise NotImplementedError


class KafkaSender(GenericSender):
    """
    A sender that publish updates in a kafka topic
    """

    def __init__(self, broker, topic, ssl, ca_cert, client_cert, client_key):
        self.topic = topic
        if ssl:
            self.producer_params = {
                'bootstrap_servers': broker,
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': ca_cert,
                'ssl_certfile': client_cert,
                'ssl_keyfile': client_key
            }
        else:
            self.producer_params = {
                'bootstrap_servers': broker
            }
        self.producer = None
        super(KafkaSender, self).__init__()

    def _create_producer(self):
        try:
            if self.producer is None:
                self.producer = KafkaProducer(**self.producer_params)
        except NoBrokersAvailable:
            raise SendingError('Cannot connect to kafka broker')

    def notify(self, message):
        try:
            self._create_producer()
        except SendingError:
            return False

        try:
            future = self.producer.send(self.topic, value=json.dumps(message).encode('utf-8'))
        except KafkaTimeoutError:
            logger.error('Cannot get topic %s metadata. Probably the token does not exist', self.topic)
            return False
        except (TypeError, JSONDecodeError):
            logger.error('Error in message structure')
            return False
        # Block for 'synchronous' sends
        try:
            future.get(timeout=2)
        except TopicAuthorizationFailedError:
            logger.debug('Missing write permission to write in topic %s', self.topic)
            return False
        except KafkaError:
            logger.debug('An error occurred sending message to topic %s. Error details %s', self.topic, format_exc())
            # Decide what to do if produce request failed...
            return False
        else:
            return True

    def notify_async(self, message):
        try:
            self._create_producer()
        except SendingError:
            return False

        try:
            self.producer.send(self.topic, json.dumps(message).encode('utf-8'))
        except (TypeError, UnicodeError):
            raise SendingError('Something bad happened notifying the message')



def get_sender(name):
    """
    Methods that returns the correct sender based on the settings file
    """
    if settings.NOTIFICATION_TYPE == 'kafka':
        return KafkaSender(settings.KAFKA_BROKER,
                             name,
                             settings.KAFKA_SSL,
                             settings.KAFKA_CA_CERT,
                             settings.KAFKA_CLIENT_CERT,
                             settings.KAFKA_CLIENT_KEY)

    raise UnknownSender("Cannot instantiate a sender")
