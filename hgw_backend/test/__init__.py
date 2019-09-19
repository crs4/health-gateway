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
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.test import TestCase, client
from mock import MagicMock, Mock, NonCallableMock, patch

from hgw_backend.models import RESTClient

SOURCE_ENDPOINT_CLIENT_NAME = 'SOURCE MOCK'
HGW_FRONTEND_CLIENT_NAME = 'HGW FRONTEND'

class GenericTestCase(TestCase):
    """
    Generic test case class
    """

    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        for logger_name in ('channel_operation_consumer', 'hgw_backend'):
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.CRITICAL)
        return super(GenericTestCase, cls).setUpClass()

    def setUp(self):
        self.maxDiff = None
        self.client = client.Client()

    @staticmethod    
    def _get_client_data(client_name=SOURCE_ENDPOINT_CLIENT_NAME):
        app = RESTClient.objects.get(name=client_name)
        return app.client_id, app.client_secret


    def _call_token_creation(self, data):
        return self.client.post('/oauth2/token/', data=data)

    def _get_oauth_token(self, client_name=SOURCE_ENDPOINT_CLIENT_NAME):
        c_id, c_secret = self._get_client_data(client_name)
        params = {
            'grant_type': 'client_credentials',
            'client_id': c_id,
            'client_secret': c_secret
        }
        res = self._call_token_creation(params)
        return res.json()

    def _get_oauth_header(self, client_name=SOURCE_ENDPOINT_CLIENT_NAME):
        res = self._get_oauth_token(client_name)
        return {'Authorization': 'Bearer {}'.format(res['access_token'])}
    
    def _get_db_error_mock(self):
        mock = NonCallableMock()
        mock.DoesNotExist = ObjectDoesNotExist
        mock.objects = NonCallableMock()
        mock.objects.all = Mock(side_effect=DatabaseError)
        mock.objects.filter = Mock(side_effect=DatabaseError)
        mock.objects.get = Mock(side_effect=DatabaseError)
        mock.objects.create = Mock(side_effect=DatabaseError)
        mock.objects.get_or_create = Mock(side_effect=DatabaseError)
        return mock
