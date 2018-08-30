import time
from datetime import datetime, timedelta

import os
from django.test import TestCase
from django.utils.crypto import get_random_string
from mock import patch, Mock, MagicMock, call
from oauthlib.oauth2 import TokenExpiredError, InvalidClientError

os.environ['DJANGO_SETTINGS_MODULE'] = 'hgw_common.test.settings'

from hgw_common.models import OAuth2SessionProxy, AccessToken


class MockOAuth2Session(MagicMock):
    RESPONSES = []
    RAISES = None
    def __init__(self, *args, **kwargs):
        super(MockOAuth2Session, self).__init__(*args, **kwargs)
        self.token = None
        self.fetch_token = Mock(side_effect=self._fetch_token)
        self.get = Mock(side_effect=self._get)
        self._get_counter = 0

    def _fetch_token(self, **kwargs):
        if self.RAISES is None:
            self.token = {
                'access_token': get_random_string(30),
                'token_type': 'Bearer',
                'expires_in': 36000,
                'expires_at': time.time() + 36000,
                'scope': ['read', 'write']
            }
            return self.token
        else:
            raise self.RAISES()

    def _get(self, url, *args, **kwargs):
        res = self.RESPONSES[self._get_counter % len(self.RESPONSES)]
        self._get_counter += 1

        if isinstance(res, Exception):
            raise res
        else:
            response = Mock()
            response.status_code = res
            return response


def _mock_token():
    return {'access_token': 'OUfprCnmdJbhYAIk8rGMex4UBLXyf3',
            'token_type': 'Bearer',
            'expires_in': 36000,
            'expires_at': time.time() + 36000,
            'scope': ['read', 'writes']}


class OAuthProxyTest(TestCase):

    def setUp(self):
        self.service_url = 'https://oauth2service'
        self.client_id = 'id'
        self.client_secret = 'secret'

    def test_create_proxy(self):
        """
        Tests that when the proxy is instantiated a token is created.
        """
        with patch('hgw_common.models.OAuth2Session', new_callable=MockOAuth2Session) as mock:
            m = mock(200)
            OAuth2SessionProxy(self.service_url, self.client_id, self.client_secret)
            # The datetime object has a precision to 10e-6 seconds while the timestamp 10e-7.
            # This precision is irrelevant in this case but we need to modify the original value
            m.token['expires_at'] = datetime.fromtimestamp(m.token['expires_at']).timestamp()
            mock.assert_called()
            self.assertEquals(AccessToken.objects.count(), 1)
            self.assertDictEqual(AccessToken.objects.first().to_python(), mock().token)

    def test_access_token_creation_fail(self):
        with patch('hgw_common.models.OAuth2Session', MockOAuth2Session):
            MockOAuth2Session.RAISES = InvalidClientError
            self.assertRaises(InvalidClientError, OAuth2SessionProxy, self.service_url,
                              self.client_id, self.client_secret)
            MockOAuth2Session.RAISES = None

    def test_access_token_reused(self):
        """
        Tests that, if the token has already been created and two subsequent calls returns 200, it is used the same token
        """

        with patch('hgw_common.models.OAuth2Session', MockOAuth2Session):
            MockOAuth2Session.RESPONSES = [200, 200]
            proxy = OAuth2SessionProxy(self.service_url, self.client_id, self.client_secret)
            m = proxy._session
            first_token = m.token['access_token']
            proxy.get("/fake_url/1/")
            second_token = m.token['access_token']
            proxy.get("/fake_url/2/")
            third_token = m.token['access_token']
            self.assertEqual(len(m.get.call_args_list), 2)  # Number of calls
            m.get.assert_has_calls([call('/fake_url/1/'), call('/fake_url/2/')])
            m.fetch_token.assert_called_once()
            self.assertEquals(AccessToken.objects.count(), 1)
            self.assertEquals(first_token, second_token, third_token)

    def test_access_token_refreshed_for_401_response(self):
        """
        Tests that, when the response is 401 (Unauthorized), another token is created and the call is perfomed again
        """
        with patch('hgw_common.models.OAuth2Session', MockOAuth2Session):
            MockOAuth2Session.RESPONSES = [401]
            proxy = OAuth2SessionProxy(self.service_url, self.client_id, self.client_secret)
            m = proxy._session
            first_token = m.token['access_token']
            proxy.get("/fake_url/1/")
            second_token = m.token['access_token']
            self.assertEqual(len(m.get.call_args_list), 2)  # Number of calls
            self.assertEqual(len(m.fetch_token.call_args_list), 2)  # Number of calls
            m.get.assert_has_calls([call('/fake_url/1/'), call('/fake_url/1/')])
            self.assertEquals(AccessToken.objects.count(), 1)
            self.assertNotEquals(first_token, second_token)

    def test_access_token_refreshed_for_token_expired(self):
        """
        Tests that, when the response is 401 (Unauthorized), another token is created and the call is perfomed again
        """
        with patch('hgw_common.models.OAuth2Session', MockOAuth2Session):
            MockOAuth2Session.RESPONSES = [TokenExpiredError(), 200]
            proxy = OAuth2SessionProxy(self.service_url, self.client_id, self.client_secret)
            m = proxy._session
            first_token = m.token['access_token']
            # m.token['expires_at'] = m.token['expires_at'] - 36001
            proxy.get("/fake_url/1/")
            second_token = m.token['access_token']
            self.assertEqual(len(m.get.call_args_list), 2)  # Number of calls
            self.assertEqual(len(m.fetch_token.call_args_list), 2)  # Number of calls
            m.get.assert_has_calls([call('/fake_url/1/'), call('/fake_url/1/')])
            self.assertEquals(AccessToken.objects.count(), 1)
            self.assertNotEquals(first_token, second_token)
