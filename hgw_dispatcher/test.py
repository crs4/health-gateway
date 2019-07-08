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
from unittest.mock import MagicMock, Mock, call, patch

import requests
from oauthlib.oauth2 import TokenExpiredError

from dispatcher import (CONSENT_MANAGER_OAUTH_CLIENT_ID,
                        CONSENT_MANAGER_OAUTH_CLIENT_SECRET,
                        HGW_FRONTEND_OAUTH_CLIENT_ID,
                        HGW_FRONTEND_OAUTH_CLIENT_SECRET, Dispatcher,
                        OAuth2Session)
from test_data import (ACTIVE_CHANNEL_ID, ACTIVE_CONSENT_ID,
                       CONSENT_WITH_NO_PROCESS_ID, DESTINATION,
                       PENDING_CONSENT_ID, PROCESS_ID, SOURCES,
                       UNKNOWN_OAUTH_CLIENT)
from test_utils import (MockBackendRequestHandler,
                        MockConsentManagerRequestHandler,
                        MockFrontendRequestHandler,
                        MockKafkaConsumer,
                        get_free_port,
                        start_mock_server)

logger = logging.getLogger('dispatcher')
# for h in logger.handlers:
#     h.setLevel(logging.CRITICAL)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
HGW_BACKEND_PORT = get_free_port()
HGW_BACKEND_URI = 'http://localhost:{}'.format(HGW_BACKEND_PORT)
HGW_FRONTEND_PORT = get_free_port()
HGW_FRONTEND_URI = 'http://localhost:{}'.format(HGW_FRONTEND_PORT)
CONSENT_MANAGER_PORT = get_free_port()
CONSENT_MANAGER_URI = 'http://localhost:{}'.format(CONSENT_MANAGER_PORT)


class MockMessage(object):
    def __init__(self, topic, value, offset, key=None, headers=None):
        self.key = key
        self.topic = topic
        self.value = value
        self.offset = offset
        self.headers = headers if headers is not None else []


class TestDispatcher(TestCase):
    @classmethod
    def setUpClass(cls):
        start_mock_server(MockBackendRequestHandler, HGW_BACKEND_PORT)
        start_mock_server(MockFrontendRequestHandler, HGW_FRONTEND_PORT)
        start_mock_server(MockConsentManagerRequestHandler, CONSENT_MANAGER_PORT)

    def set_mock_kafka_consumer(self, mock_kc_klass, messages, topic, key):
        mock_kc_klass.FIRST = 0
        mock_kc_klass.END = 2
        key = key.encode('utf-8')
        mock_kc_klass.MESSAGES = {i: MockMessage(offset=i, topic=topic, value=m, key=key) for i, m in enumerate(messages)}

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('dispatcher.CONSENT_MANAGER_OAUTH_CLIENT_ID', UNKNOWN_OAUTH_CLIENT)
    def test_fail_wrong_consent_oauth_client(self):
        """
        Tests that the dispatcher exits when it cannot get an oauth token from the consent manager because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None, True)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', 'http://127.0.0.2')
    def test_fail_consent_oauth_connection(self):
        """
        Tests that the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None, True)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('dispatcher.HGW_FRONTEND_OAUTH_CLIENT_ID', UNKNOWN_OAUTH_CLIENT)
    def test_fail_wrong_hgw_frontend_oauth_client(self):
        """
        Tests that the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None, True)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', 'http://127.0.0.2')
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_fail_hgw_frontend_oauth_connection(self):
        """
        Tests that the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None, True)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('dispatcher.HGW_BACKEND_OAUTH_CLIENT_ID', UNKNOWN_OAUTH_CLIENT)
    def test_fail_hgw_backend_oauth2_client(self):
        """
        Tests that the dispatcher exits when it cannot get an oauth token from the hgw_backend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None, True)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.HGW_BACKEND_URI', 'http://127.0.0.2')
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_fail_hgw_backend_oauth_connection(self):
        """
        Tests that the dispatcher exits when it cannot get an oauth token from the hgw_frontend because of
        wrong client id
        """
        with self.assertRaises(SystemExit) as se:
            Dispatcher('kafka:9093', None, None, None, True)
        self.assertEqual(se.exception.code, 1)

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consent_oauth_token_renewal_on_token_expired(self):
        """
        Tests that, when the consent manager token expires, the dispatcher requires another one
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = [
                b'first_message',
                b'second_message'
            ]
            token_res = {
                'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                'token_type': 'Bearer',
                'expires_in': 36000,
                'expires_at': 1516236829.8031383,
                'scope': ['read', 'write']
            }
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)

            self.counter = 0

            def get_url(*args):
                res = MagicMock()
                if args[1].startswith(CONSENT_MANAGER_URI) and self.counter == 0:
                    self.counter += 1
                    raise TokenExpiredError()
                else:
                    res.status_code = 200
                return res

            d = Dispatcher('kafka:9093', None, None, None, True)
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

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consent_oauth_token_renewal_on_not_authorized_status(self):
        """
        Tests that, when the consent manager token expires, the dispatcher requires another one
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = [
                b'first_message',
                b'second_message'
            ]
            token_res = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                        'token_type': 'Bearer', 'expires_in': 36000,
                        'expires_at': 1516236829.8031383, 'scope': ['read', 'write']}
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)

            self.counter = 0

            def get_url(*args):
                res = MagicMock()
                if args[1].startswith(CONSENT_MANAGER_URI) and self.counter == 0:
                    self.counter += 1
                    res.status_code = 401
                else:
                    res.status_code = 200
                return res

            d = Dispatcher('kafka:9093', None, None, None, True)
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

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_hgw_frontend_oauth_token_renewal_on_token_expired(self):
        """
        Tests that when the hgw frontend token expires, the dispatcher requires another one
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)
                
            token_res = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                        'token_type': 'Bearer', 'expires_in': 36000,
                        'expires_at': 1516236829.8031383, 'scope': ['read', 'write']}

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
                    # simulates the service with minimum data just to arrive to the point of
                    # getting the hgw_frontend token
                    if args[1].startswith(CONSENT_MANAGER_URI):
                        res.json.return_value = {
                            'destination': DESTINATION,
                            'status': 'AC'
                        }
                    else:
                        res.json.return_value = {
                            'channel_id': ACTIVE_CHANNEL_ID,
                            'process_id': PROCESS_ID
                        }
                return res

            d = Dispatcher('kafka:9093', None, None, None, True)
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

    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_hgw_frontend_oauth_token_renewal_on_not_authorized(self):
        """
        Tests that when the hgw frontend token expires, the dispatcher requires another one
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            messages = [
                b'first_message',
                b'second_message'
            ]
            token_res = {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
                        'token_type': 'Bearer', 'expires_in': 36000,
                        'expires_at': 1516236829.8031383, 'scope': ['read', 'write']}
            self.set_mock_kafka_consumer(MockKafkaConsumer, messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)

            self.counter = 0

            def get_url(*args):
                """
                Method that simulates the get. When the response is 401 it means that token expired and the
                dispatcher requires another token
                """
                res = MagicMock()
                if args[1].startswith(HGW_FRONTEND_URI) and self.counter == 0:
                    self.counter += 1
                    res.status_code = 401
                else:
                    res.status_code = 200
                    # simulates the response with minimum data just to arrive to the point of
                    # getting the hgw_frontend token
                    if args[1].startswith(CONSENT_MANAGER_URI):
                        res.json.return_value = {
                            'destination': DESTINATION,
                            'status': 'AC'
                        }
                    else:
                        res.json.return_value = {
                            'channel_id': ACTIVE_CHANNEL_ID,
                            'process_id': PROCESS_ID
                        }
                return res

            d = Dispatcher('kafka:9093', None, None, None, True)
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

    @patch('hgw_common.messaging.sender.KafkaProducer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_correct_message_dispatching(self, mocked_kafka_producer):
        """
        Tests that a message is sent correctly to a destination when the channel is active
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            in_messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, in_messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)

            d = Dispatcher('kafka:9093', None, None, None, True)
            d.run()

            for m in in_messages:
                headers = [
                    ('process_id', PROCESS_ID.encode('utf-8')),
                    ('channel_id', ACTIVE_CHANNEL_ID.encode('utf-8')),
                    ('source_id', SOURCES[0]['source_id'].encode('utf-8'))
                ]
                mocked_kafka_producer().send.assert_any_call(DESTINATION['id'], value=m, key=None, headers=headers)

    @patch('hgw_common.messaging.sender.KafkaProducer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_wrong_consent_status_message_dispatching(self, mocked_kafka_producer):
        """
        Tests that if the consent is in status PENDING the message is not dispatched
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            in_messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, in_messages, SOURCES[1]['source_id'], PENDING_CONSENT_ID)

            d = Dispatcher('kafka:9093', None, None, None, True)
            d.run()
            mocked_kafka_producer().send.assert_not_called()

    @patch('hgw_common.messaging.sender.KafkaProducer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_unreachable_consent_on_message_dispatching(self, mocked_kafka_producer):
        """
        Tests that if the consent manager is unreachable the message is not sent
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            in_messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, in_messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)

            d = Dispatcher('kafka:9093', None, None, None, True)
            mock_oauth2_session = MagicMock()
            mock_oauth2_session.get.side_effect = requests.exceptions.ConnectionError()

            with patch.object(d, 'consent_oauth_session', mock_oauth2_session):
                d.run()
                mocked_kafka_producer().send.assert_not_called()

    @patch('hgw_common.messaging.sender.KafkaProducer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_consent_not_found(self, mocked_kafka_producer):
        """
        Tests that if the consent doesn't exists the message is not dispatched
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            in_messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, in_messages, SOURCES[0]['source_id'], 'UNKNOWN_CHANNEL_ID')
            
            d = Dispatcher('kafka:9093', None, None, None, True)
            d.run()
            mocked_kafka_producer().send.assert_not_called()

    @patch('hgw_common.messaging.sender.KafkaProducer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_unreachable_hgw_frontend_on_message_dispatching(self, mocked_kafka_producer):
        """
        Tests that if the consent manager is unreachable the message is not sent
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            in_messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, in_messages, SOURCES[0]['source_id'], ACTIVE_CONSENT_ID)
            d = Dispatcher('kafka:9093', None, None, None, True)
            mock_oauth2_session = MagicMock()
            mock_oauth2_session.get.side_effect = requests.exceptions.ConnectionError()

            with patch.object(d, 'consent_oauth_session', mock_oauth2_session):
                d.run()
                mocked_kafka_producer().send.assert_not_called()

    @patch('hgw_common.messaging.sender.KafkaProducer')
    @patch('dispatcher.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('dispatcher.HGW_FRONTEND_URI', HGW_FRONTEND_URI)
    @patch('dispatcher.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_process_id_not_found(self, mocked_kafka_producer):
        """
        Tests that if the consent doesn't exists the message is not dispatched
        """
        with patch('hgw_common.messaging.receiver.KafkaConsumer', MockKafkaConsumer):
            in_messages = [
                b'first_message',
                b'second_message'
            ]
            self.set_mock_kafka_consumer(MockKafkaConsumer, in_messages, SOURCES[0]['source_id'], CONSENT_WITH_NO_PROCESS_ID)
        
            d = Dispatcher('kafka:9093', None, None, None, True)
            d.run()
            mocked_kafka_producer().send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
