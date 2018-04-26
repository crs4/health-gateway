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
import logging
import os
import unittest
from unittest import TestCase

import requests
from mock import patch, MagicMock, call, Mock
from oauthlib.oauth2 import TokenExpiredError

from dispatcher import Dispatcher, OAuth2Session, CONSENT_MANAGER_OAUTH_CLIENT_ID, CONSENT_MANAGER_OAUTH_CLIENT_SECRET, \
    HGW_FRONTEND_OAUTH_CLIENT_SECRET, HGW_FRONTEND_OAUTH_CLIENT_ID
from test_data import SOURCES, UNKNOWN_OAUTH_CLIENT, ACTIVE_CHANNEL_ID, DESTINATION, PROCESS_ID, PENDING_CHANNEL_ID, \
    CHANNEL_WITH_NO_PROCESS_ID, PERSON_ID
from test_utils import get_free_port, start_mock_server, MockBackendRequestHandler, MockConsentManagerRequestHandler, \
    MockFrontendRequestHandler

logger = logging.getLogger('dispatcher')
for h in logger.handlers:
    h.setLevel(logging.CRITICAL)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
HGW_BACKEND_PORT = get_free_port()
HGW_BACKEND_URI = 'http://localhost:{}'.format(HGW_BACKEND_PORT)
HGW_FRONTEND_PORT = get_free_port()
HGW_FRONTEND_URI = 'http://localhost:{}'.format(HGW_FRONTEND_PORT)
CONSENT_MANAGER_PORT = get_free_port()
CONSENT_MANAGER_URI = 'http://localhost:{}'.format(CONSENT_MANAGER_PORT)


class MockMessage(object):
    def __init__(self, key, topic, value, offset):
        self.key = key
        self.topic = topic
        self.value = value
        self.offset = offset


class TestDispatcher(TestCase):
    @classmethod
    def setUpClass(cls):
        start_mock_server(MockBackendRequestHandler, HGW_BACKEND_PORT)
        start_mock_server(MockFrontendRequestHandler, HGW_FRONTEND_PORT)
        start_mock_server(MockConsentManagerRequestHandler, CONSENT_MANAGER_PORT)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('dispatcher.CONSENT_MANAGER_OAUTH_CLIENT_ID', UNKNOWN_OAUTH_CLIENT)
    def test_fail_with_no_topics(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that if there are no available topics the dispatcher exits
        """
        mocked_kafka_consumer().partitions_for_topic = MagicMock(return_value=None)
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None)
        self.assertEqual(se.exception.code, 2)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('dispatcher.CONSENT_MANAGER_OAUTH_CLIENT_ID', UNKNOWN_OAUTH_CLIENT)
    def test_fail_wrong_consent_oauth_client(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that, when the dispatcher exits when it cannot get an oauth token from the consent manager because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', 'http://127.0.0.2')
    def test_fail_consent_oauth_connection(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that, when the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('dispatcher.HGW_FRONTEND_OAUTH_CLIENT_ID', UNKNOWN_OAUTH_CLIENT)
    def test_fail_wrong_hgw_frontend_oauth_client(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that, when the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', 'http://127.0.0.2')
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_fail_hgw_frontend_oauth_connection(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that, when the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None)
        self.assertEqual(se.exception.code, 1)
    #
    # @patch('dispatcher.KafkaProducer')
    # @patch('dispatcher.KafkaConsumer')
    # @patch('dispatcher.HGW_BACKEND_URI', 'http://127.0.0.2')
    # @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    # @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    # def test_fail_hgw_backend_connection(self, mocked_kafka_consumer, mocked_kafka_producer):
    #     """
    #     Tests that, when the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
    #     wrong client id
    #     """
    #     with self.assertRaises(SystemExit) as se:
    #         Dispatcher('kafka:9093', None, None, None)
    #     self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consent_oauth_token_renewal(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that when the consent manager token expires, the dispatcher requires another one
        """
        messages = [
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        token_res = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                     'token_type': 'Bearer', 'expires_in': 36000,
                     'expires_at': 1516236829.8031383, 'scope': ['read', 'write']}
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))

        self.counter = 0

        def get_url(*args):
            """
            Method that simulates the get. When the response is 401 it means that token expired and the
            dispatcher requires another token
            """
            res = MagicMock()
            if args[1].startswith(CONSENT_MANAGER_URI) and self.counter == 0:
                self.counter += 1
                raise TokenExpiredError()
            else:
                res.status_code = 200
            return res

        d = Dispatcher('kafka:9093', None, None, None)
        with patch.object(OAuth2Session, 'fetch_token', return_value=token_res) as fetch_token, \
                patch.object(OAuth2Session, 'get', get_url):
            # NOTE: the first fetch_token calls (one to the consent manager and the second to the
            # hgw frontend) are not mocked since they occurs in Dispatcher.__init__ and when we call
            # the __init__ Oauth2Session is not mocked, so has_calls doesn't register them
            d.run()
            calls = [call(token_url="{}/oauth2/token/".format(CONSENT_MANAGER_URI),
                          client_id=CONSENT_MANAGER_OAUTH_CLIENT_ID,
                          client_secret=CONSENT_MANAGER_OAUTH_CLIENT_SECRET)]
            # check that the fetch_token is called the second time with consent manager parameter
            fetch_token.assert_has_calls(calls)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_hgw_frontend_oauth_token_renewal(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that when the hgw frontend token expires, the dispatcher requires another one
        """
        messages = [
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        token_res = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                     'token_type': 'Bearer', 'expires_in': 36000,
                     'expires_at': 1516236829.8031383, 'scope': ['read', 'write']}
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))

        self.counter = 0

        def get_url(*args):
            """
            Method that simulates the get. When the response is 401 it means that token expired and the
            dispatcher requires another token
            """
            res = MagicMock()
            if args[1].startswith(HGW_FRONTEND_URI) and self.counter == 0:
                self.counter += 1
                raise TokenExpiredError()
            else:
                res.status_code = 200
                if args[1].startswith(CONSENT_MANAGER_URI):
                    # simulates the consent manager with minimum data just to arrive to the point of
                    # getting the hgw_frontend token
                    res.json.return_value = {
                        'destination': DESTINATION,
                        'status': 'AC'
                    }
            return res

        d = Dispatcher('kafka:9093', None, None, None)
        with patch.object(OAuth2Session, 'fetch_token', return_value=token_res) as fetch_token, \
                patch.object(OAuth2Session, 'get', get_url):
            # NOTE: the first fetch_token calls (one to the consent manager and the second to the
            # hgw frontend) are not mocked since they occurs in Dispatcher.__init__ and when we call
            # the __init__ Oauth2Session is not mocked, so has_calls doesn't register them
            d.run()
            calls = [call(token_url="{}/oauth2/token/".format(HGW_FRONTEND_URI),
                          client_id=HGW_FRONTEND_OAUTH_CLIENT_ID,
                          client_secret=HGW_FRONTEND_OAUTH_CLIENT_SECRET)]
            # check that the fetch_token is called the second time with consent manager parameter
            fetch_token.assert_has_calls(calls)

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consume_not_subscribed(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that, when there's no partitions for a topic, the consumer is not subscribed to that topic
        :return:
        """
        mocked_kafka_consumer().partitions_for_topic = MagicMock(return_value=None)
        with self.assertRaises(SystemExit):
            Dispatcher('kafka:9093', None, None, None)
            sources_id = [s['source_id'] for s in SOURCES]

            mocked_kafka_consumer().partitions_for_topic.assert_has_calls([call(s) for s in sources_id])
            mocked_kafka_consumer().subscribe.assert_not_called()

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consume_topic_subscription(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that the consumer is subscribed to the topic
        :return:
        """
        d = Dispatcher('kafka:9093', None, None, None)
        d.run()
        sources_id = [s['source_id'] for s in SOURCES]

        mocked_kafka_consumer().partitions_for_topic.assert_has_calls([call(s) for s in sources_id])
        mocked_kafka_consumer().subscribe.assert_called()

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_correct_message_dispatching(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that a message is sent correctly to a destination when the channel is active
        """
        messages = [
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))
        d = Dispatcher('kafka:9093', None, None, None)
        d.run()
        for m in messages:
            mocked_kafka_producer().send.assert_any_call(DESTINATION['id'], m.value, key=PROCESS_ID.encode('utf-8'))

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_wrong_consent_status_message_dispatching(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that if the consent is in status PENDING the message is not dispatched
        """
        messages = [
            MockMessage(key=PENDING_CHANNEL_ID.encode('utf-8'), topic=SOURCES[1]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=PENDING_CHANNEL_ID.encode('utf-8'), topic=SOURCES[1]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))
        d = Dispatcher('kafka:9093', None, None, None)
        d.run()
        mocked_kafka_producer().send.assert_not_called()

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_unreachable_consent_on_message_dispatching(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that if the consent manager is unreachable the message is not sent
        """
        messages = [
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))
        d = Dispatcher('kafka:9093', None, None, None)
        mock_oauth2_session = MagicMock()
        mock_oauth2_session.get.side_effect = requests.exceptions.ConnectionError()

        with patch.object(d, 'consent_oauth_session', mock_oauth2_session):
            d.run()
            mocked_kafka_producer().send.assert_not_called()

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consent_not_found(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that if the consent doesn't exists the message is not dispatched
        """
        messages = [
            MockMessage(key='UNKNOWN_CHANNEL_ID'.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key='UNKNOWN_CHANNEL_ID'.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))
        d = Dispatcher('kafka:9093', None, None, None)
        d.run()
        mocked_kafka_producer().send.assert_not_called()

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_unreachable_hgw_frontend_on_message_dispatching(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that if the consent manager is unreachable the message is not sent
        """
        messages = [
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=ACTIVE_CHANNEL_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))
        d = Dispatcher('kafka:9093', None, None, None)
        mock_oauth2_session = MagicMock()
        mock_oauth2_session.get.side_effect = requests.exceptions.ConnectionError()

        with patch.object(d, 'consent_oauth_session', mock_oauth2_session):
            d.run()
            mocked_kafka_producer().send.assert_not_called()

    @patch('dispatcher.KafkaProducer')
    @patch('dispatcher.KafkaConsumer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_process_id_not_found(self, mocked_kafka_consumer, mocked_kafka_producer):
        """
        Tests that if the consent doesn't exists the message is not dispatched
        """
        messages = [
            MockMessage(key=CHANNEL_WITH_NO_PROCESS_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'first_message', offset=0),
            MockMessage(key=CHANNEL_WITH_NO_PROCESS_ID.encode('utf-8'), topic=SOURCES[0]['source_id'].encode('utf-8'),
                        value=b'second_message', offset=1),
        ]
        mocked_kafka_consumer().__iter__ = Mock(return_value=iter(messages))
        d = Dispatcher('kafka:9093', None, None, None)
        d.run()
        mocked_kafka_producer().send.assert_not_called()


if __name__ == '__main__':
    unittest.main()