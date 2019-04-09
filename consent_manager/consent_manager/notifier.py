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

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from consent_manager import settings


class UnknownNotifier(Exception):
    """
    Exception to be raised when it was impossible to get the instantiate the correct notifier
    """


class NotificationError(Exception):
    """
    Exception to be raised when a notification error happens
    """


class GenericNotifier():
    """
    Generic notifier abstract class. Subclass should implement the
    real notification process
    """

    def notify(self, message):
        """
        Abstract notify method. Subclasses should implement this
        """
        raise NotImplementedError


class KafkaNotifier(GenericNotifier):
    """
    A notifier that publish updates in a kafka topic
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
        super().__init__()

    def notify(self, message):
        try:
            if self.producer is None:
                self.producer = KafkaProducer(**self.producer_params)
        except NoBrokersAvailable:
            raise NotificationError('Cannot connect to kafka broker')

        try:
            self.producer.send(self.topic, json.dumps(message).encode('utf-8'))
        except (TypeError, UnicodeError):
            raise NotificationError('Something bad happened notifying the message')


def get_notifier():
    """
    Methods that returns the correct notifier based on the settings file
    """
    if settings.NOTIFICATION_TYPE == 'kafka':
        return KafkaNotifier(settings.KAFKA_BROKER,
                             settings.KAFKA_TOPIC,
                             settings.KAFKA_SSL,
                             settings.KAFKA_CA_CERT,
                             settings.KAFKA_CLIENT_CERT,
                             settings.KAFKA_CLIENT_KEY)

    raise UnknownNotifier("Cannot instantiate a notifier")
