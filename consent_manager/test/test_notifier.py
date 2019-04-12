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
Tests notifiers
"""

import json

from django.test import TestCase
from mock import patch

import consent_manager
from consent_manager import settings
from consent_manager.notifier import (KafkaNotifier, NotificationError,
                                      UnknownNotifier, get_notifier)


class TestNotifiers(TestCase):
    """
    Test notifiers class
    """

    @patch('consent_manager.settings.NOTIFICATION_TYPE', 'unknown')
    def test_raise_unknown_notifier(self):
        """
        Tests that, when the notifier is unknown the get_notifier function raises an error
        """
        self.assertRaises(UnknownNotifier, get_notifier)

    @patch('consent_manager.notifier.KafkaProducer')
    def test_get_kafka_notifier(self, mocked_kafka_producer):
        """
        Tests that, when the settings specifies a kafka notifier, the instantiated notifier is KafkaNotifier
        """
        notifier = get_notifier()
        self.assertIsInstance(notifier, KafkaNotifier)


class TestKafkaNotifier(TestCase):
    """
    Class the tests kafka notifier
    """

    def test_fail_kafka_producer_connection(self):
        """
        Tests that, if the kafka broker is not accessible, the notify method raises an exception
        """
        notifier = get_notifier()
        self.assertRaises(NotificationError, notifier.notify, {'message': 'fake_message'})

    @patch('consent_manager.notifier.KafkaProducer')
    def test_fail_json_encoding_error(self, mocked_kafka_producer):
        """
        Tests that, if the json encoding fails the notify method raises an exception
        """
        notifier = get_notifier()
        # NB: set are not json serializable so we can use it to cause a json encoding error
        self.assertRaises(NotificationError, notifier.notify, {"wrong_object"})

    @patch('consent_manager.notifier.KafkaProducer')
    def test_correct_send(self, mocked_kafka_producer):
        """
        Tests that, if the json encoding fails the notify method raises an exception
        """
        notifier = get_notifier()
        message = {'message': 'text'}
        notifier.notify(message)
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][0][0], settings.KAFKA_TOPIC)
        self.assertDictEqual(json.loads(mocked_kafka_producer().send.call_args_list[0][0][1].decode('utf-8')), message)

    # def test_real_send(self):
    #     """
    #     Tests that, if the json encoding fails the notify method raises an exception
    #     """
    #     print("Sending message to kafka")
    #     notifier = get_notifier()
    #     message = {'message': 'text'}
    #     notifier.notify(message)
