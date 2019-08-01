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

from Cryptodome.PublicKey import RSA
from django.test import TestCase, client
from mock import patch

from hgw_common.cipher import Cipher
from hgw_common.utils import ERRORS
from hgw_frontend.models import RESTClient

from .utils import get_db_error_mock

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

DEST_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\n' \
                  'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp4TF/ETwYKG+eAYZz3wo\n' \
                  '8IYqrPIlQyz1/xljqDD162ZAYJLCYeCfs9yczcazC8keWzGd5/tn4TF6II0oINKh\n' \
                  'kCYLqTIVkVGC7/tgH5UEe/XG1trRZfMqwl1hEvZV+/zanV0cl7IjTR9ajb1TwwQY\n' \
                  'MOjcaaBZj+xfD884pwogWkcSGTEODGfoVACHjEXHs+oVriHqs4iggiiMYbO7TBjg\n' \
                  'Be9p7ZDHSVBbXtQ3XuGKnxs9MTLIh5L9jxSRb9CgAtv8ubhzs2vpnHrRVkRoddrk\n' \
                  '8YHKRryYcVDHVLAGc4srceXU7zrwAMbjS7msh/LK88ZDUWfIZKZvbV0L+/topvzd\n' \
                  'XQIDAQAB\n' \
                  '-----END PUBLIC KEY-----'

DEST_1_NAME = 'Destination 1'
DEST_1_ID = 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj'
DEST_2_NAME = 'Destination 2'
DEST_2_ID = '6RtHuetJ44HKndsDHI5K9JUJxtg0vLJ3'
DISPATCHER_NAME = 'Health Gateway Dispatcher'
POWERLESS_NAME = 'Powerless Client'


class TestChannelsAPI(TestCase):
    """
    Unit test for /v1/channels REST API
    """
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(TestChannelsAPI, cls).setUpClass()
        logger = logging.getLogger('hgw_frontend')
        logger.setLevel(logging.ERROR)

    def setUp(self):
        self.client = client.Client()
        payload = '[{"clinical_domain": "Laboratory"}]'
        self.profile = {
            'code': 'PROF_001',
            'version': 'v0',
            'payload': payload
        }
        self.flow_request = {
            'flow_id': 'f_44444',
            'profile': self.profile,
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }

        self.encrypter = Cipher(public_key=RSA.importKey(DEST_PUBLIC_KEY))

        with open(os.path.abspath(os.path.join(BASE_DIR, '../hgw_frontend/fixtures/test_data.json'))) as fixtures_file:
            self.fixtures = json.load(fixtures_file)

        self.profiles = {obj['pk']: obj['fields'] for obj in self.fixtures
                         if obj['model'] == 'hgw_common.profile'}
        self.sources = {obj['pk']: {
            'source_id': obj['fields']['source_id'],
            'name': obj['fields']['name'],
            'profile':  self.profiles[obj['fields']['profile']]
        } for obj in self.fixtures if obj['model'] == 'hgw_frontend.source'}
        self.destinations = {obj['pk']: obj['fields'] for obj in self.fixtures
                             if obj['model'] == 'hgw_frontend.destination'}
        self.flow_requests = {obj['pk']: obj['fields'] for obj in self.fixtures
                              if obj['model'] == 'hgw_frontend.flowrequest'}
        self.channels = {obj['pk']: {
            'channel_id': obj['fields']['channel_id'],
            'source': self.sources[obj['fields']['source']],
            'profile': self.profiles[self.flow_requests[obj['fields']['flow_request']]['profile']],
            'destination_id':
            self.destinations[self.flow_requests[obj['fields']['flow_request']]['destination']]['destination_id'],
                'status': obj['fields']['status']
        } for obj in self.fixtures if obj['model'] == 'hgw_frontend.channel'}

        self.active_flow_request_channels = {obj['pk']: {
            'channel_id': obj['fields']['channel_id'],
            'source': self.sources[obj['fields']['source']],
            'profile': self.profiles[self.flow_requests[obj['fields']['flow_request']]['profile']],
            'destination_id':
            self.destinations[self.flow_requests[obj['fields']['flow_request']]['destination']]['destination_id'],
                'status': obj['fields']['status']
        } for obj in self.fixtures if obj['model'] == 'hgw_frontend.channel' and obj['fields']['flow_request'] == 2}

    @staticmethod
    def _get_client_data(client_name=DEST_1_NAME):
        app = RESTClient.objects.get(name=client_name)
        return app.client_id, app.client_secret

    def _get_oauth_header(self, client_name=DEST_1_NAME):
        c_id, c_secret = self._get_client_data(client_name)
        params = {
            'grant_type': 'client_credentials',
            'client_id': c_id,
            'client_secret': c_secret
        }
        res = self.client.post('/oauth2/token/', data=params)
        access_token = res.json()['access_token']
        return {"Authorization": "Bearer {}".format(access_token)}

    def test_get(self):
        """
        Tests getting channels
        """
        headers = self._get_oauth_header()
        res = self.client.get('/v1/channels/', **headers)
        self.assertEqual(res.status_code, 200)
        expected = [ch_fi for ch_pk, ch_fi in self.channels.items()
                    if ch_fi['destination_id'] == DEST_1_ID]
        self.assertEqual(res.json(), expected)
        self.assertEqual(res['X-Total-Count'], str(len(expected)))

    def test_get_db_error(self):
        """
        Tests getting channels error response in case of db error
        """
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.channels.Channel', mock):
            headers = self._get_oauth_header()
            res = self.client.get('/v1/channels/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_filter_by_status(self):
        """
        Tests getting channels related to a specific flow_request
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/channels/?status=AC', **headers)
        self.assertEqual(res.status_code, 200)
        expected = [ch_fi for ch_pk, ch_fi in self.channels.items()
                    if ch_fi['destination_id'] == DEST_2_ID and ch_fi['status'] == 'AC']
        self.assertEqual(res.json(), expected)
        self.assertEqual(res['X-Total-Count'], str(len(expected)))

    def test_get_filter_by_status_wrong_status(self):
        """
        Tests getting channels related to a specific flow_request
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/channels/?status=WRONG_STATUS', **headers)
        self.assertEqual(res.status_code, 400)

    def test_get_by_superuser(self):
        """
        Tests getting all channels from a superuser
        """
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/channels/', **headers)
        self.assertEqual(res.status_code, 200)
        expected = [ch_fi for ch_pk, ch_fi in self.channels.items()]
        self.assertEqual(res.json(), expected)
        self.assertEqual(res['X-Total-Count'], str(len(expected)))

    def test_get_db_error_by_superuser(self):
        """
        Tests getting channels error response in case of db error
        """
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.channels.Channel', mock):
            headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
            res = self.client.get('/v1/channels/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_unauthorized(self):
        """
        Tests get channels unauthorized
        """
        res = self.client.get('/v1/channels/')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': ['not_authenticated']})

    def test_get_forbidden(self):
        """
        Tests get channels forbidden
        """
        headers = self._get_oauth_header(client_name=POWERLESS_NAME)
        res = self.client.get('/v1/channels/', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': ['forbidden']})

    def test_retrieve_channel(self):
        """
        Tests getting channels
        """
        target_channel = self.channels[1]
        headers = self._get_oauth_header()
        res = self.client.get('/v1/channels/nh4P0hYo2SEIlE3alO6w3geTDzLTOl7b/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), target_channel)
    
    def test_retrieve_channel_db_error(self):
        """
        Tests getting channels db error
        """
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.channels.Channel', mock):
            headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
            res = self.client.get('/v1/channels/nh4P0hYo2SEIlE3alO6w3geTDzLTOl7b/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_retrieve_unauthorized(self):
        """
        Tests get channel unauthorized
        """
        res = self.client.get('/v1/channels/nh4P0hYo2SEIlE3alO6w3geTDzLTOl7b/')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': ['not_authenticated']})

    def test_retrieve_forbidden(self):
        """
        Tests get channels forbidden
        """
        headers = self._get_oauth_header(client_name=POWERLESS_NAME)
        res = self.client.get('/v1/channels/nh4P0hYo2SEIlE3alO6w3geTDzLTOl7b/', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': ['forbidden']})

    def test_retrieve_by_superuser(self):
        """
        Tests get channels forbidden
        """
        target_channel = self.channels[1]
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/channels/nh4P0hYo2SEIlE3alO6w3geTDzLTOl7b/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), target_channel)

    def test_retrieve_not_found(self):
        """
        Tests get channel not found. It tests not found for superclient, for nonexistent channel and for a channel
        that belongs to another destination
        """
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/channels/nonexistent_channel/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/channels/nonexistent_channel/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/channels/nh4P0hYo2SEIlE3alO6w3geTDzLTOl7b/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

    def test_get_by_flow_request(self):
        """
        Tests getting channels related to a specific flow_request
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/flow_requests/p_22222/channels/', **headers)
        self.assertEqual(res.status_code, 200)
        expected = [ch_fi for ch_pk, ch_fi in self.active_flow_request_channels.items()
                    if ch_fi['destination_id'] == DEST_2_ID]
        self.assertEqual(res.json(), expected)
        self.assertEqual(res['X-Total-Count'], str(len(expected)))

    def test_get_by_flow_request_filter_by_status(self):
        """
        Tests getting channels related to a specific flow_request
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/flow_requests/p_22222/channels/?status=AC', **headers)
        self.assertEqual(res.status_code, 200)
        expected = [ch_fi for ch_pk, ch_fi in self.active_flow_request_channels.items()
                    if ch_fi['destination_id'] == DEST_2_ID and ch_fi['status'] == 'AC']
        self.assertEqual(res.json(), expected)
        self.assertEqual(res['X-Total-Count'], str(len(expected)))

    def test_get_by_flow_request_filter_by_status_wrong_status(self):
        """
        Tests getting channels related to a specific flow_request
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/flow_requests/p_22222/channels/?status=WRONG_STATUS', **headers)
        self.assertEqual(res.status_code, 400)

    def test_get_by_flow_request_flow_request_not_found(self):
        """
        Tests getting channels related to a specific flow_request which is not found
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/flow_requests/nonexistentfr/channels/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

    def test_get_by_flow_request_channels_not_found(self):
        """
        Tests getting channels related to a specific flow_request when the flow_request has no channels
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/flow_requests/p_33333/channels/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

    def test_get_by_flow_request_not_owner(self):
        """
        Tests getting channels related to a specific flow_request when the flow_request does not
        belong to the same Destination
        """
        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/flow_requests/p_22222/channels/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

    def test_get_by_flow_request_by_superuser(self):
        """
        Tests getting channels related to a specific flow_request
        """
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/flow_requests/p_22222/channels/', **headers)
        self.assertEqual(res.status_code, 200)
        expected = [ch_fi for ch_pk, ch_fi in self.active_flow_request_channels.items()
                    if ch_fi['destination_id'] == DEST_2_ID]
        self.assertEqual(res.json(), expected)
        self.assertEqual(res['X-Total-Count'], str(len(expected)))

    def test_get_by_flow_request_unauthorized(self):
        """
        Tests get channels unauthorized
        """
        res = self.client.get('/v1/flow_requests/33333/channels/')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': ['not_authenticated']})

    def test_get_by_flow_request_forbidden(self):
        """
        Tests get channels forbidden
        """
        headers = self._get_oauth_header(client_name=POWERLESS_NAME)
        res = self.client.get('/v1/flow_requests/33333/channels/', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': ['forbidden']})

    def test_search_by_consent(self):
        """
        Tests searching channel by consent_id.
        """
        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/channels/search/?consent_id=consent', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), self.channels[1])
        self.assertEqual(res['X-Total-Count'], '1')

    def test_search_by_consent_db_error(self):
        """
        Tests searching channel by consent_id db error.
        """
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.channels.ConsentConfirmation', mock):
            headers = self._get_oauth_header(client_name=DEST_1_NAME)
            res = self.client.get('/v1/channels/search/?consent_id=consent', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

        with patch('hgw_frontend.views.channels.FlowRequest', mock):
            headers = self._get_oauth_header(client_name=DEST_1_NAME)
            res = self.client.get('/v1/channels/search/?consent_id=consent', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_search_unauthorized(self):
        """
        Tests searching channels, not authorized (i.e., without specifying the client)
        """
        res = self.client.get('/v1/channels/search/?consent_id=consent')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': ['not_authenticated']})

    def test_search_forbidden(self):
        """
        Tests searching channels, forbidden (i.e., by a client with no permission)
        """
        headers = self._get_oauth_header(client_name=POWERLESS_NAME)
        res = self.client.get('/v1/channels/search/?consent_id=consent', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': ['forbidden']})

    def test_search_not_found(self):
        """
        Tests searching channels, not found
        """
        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/channels/search/?consent_id=unknown', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

    def test_search_by_super_client(self):
        """
        Tests searching channels by a client with all privileges
        """
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/channels/search/?consent_id=consent', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), self.channels[1])
        self.assertEqual(res['X-Total-Count'], '1')

    def test_search_by_not_owner(self):
        """
        Tests searching channels by a client which is not the owner of the channel
        """
        headers = self._get_oauth_header(client_name=DEST_2_NAME)
        res = self.client.get('/v1/channels/search/?consent_id=consent', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})

    def test_search_wrong_parameter(self):
        """
        Tests searching channels with the wrong parameter
        """
        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/channels/search/?wrong_param=unknown', **headers)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': ['missing_parameter']})
