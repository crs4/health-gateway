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
from datetime import timedelta

from Cryptodome.PublicKey import RSA
from dateutil.parser import parse
from django.test import TestCase, client
from mock import patch

from hgw_common.cipher import Cipher
from hgw_common.models import Profile
from hgw_common.utils import ERRORS
from hgw_common.utils.mocks import (MockMessage, get_free_port,
                                    start_mock_server)
from hgw_frontend import ERRORS_MESSAGE
from hgw_frontend.models import (Channel, ConfirmationCode,
                                 ConsentConfirmation, Destination, FlowRequest,
                                 RESTClient, Source)
from hgw_frontend.settings import CONSENT_MANAGER_CONFIRMATION_PAGE

from . import (CORRECT_CONFIRM_ID, CORRECT_CONFIRM_ID2, DEST_1_ID, DEST_1_NAME,
               DEST_PUBLIC_KEY, DISPATCHER_NAME, PERSON_ID, POWERLESS_NAME,
               SOURCE_1_ID, SOURCE_1_NAME, WRONG_CONFIRM_ID, ABORTED_CONFIRM_ID)
from .utils import MockBackendRequestHandler, MockConsentManagerRequestHandler, get_db_error_mock

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CONSENT_MANAGER_PORT = get_free_port()
CONSENT_MANAGER_URI = 'http://localhost:{}'.format(CONSENT_MANAGER_PORT)

HGW_BACKEND_PORT = get_free_port()
HGW_BACKEND_URI = 'http://localhost:{}'.format(HGW_BACKEND_PORT)

logger = logging.getLogger('hgw_frontend')
logger.setLevel(logging.DEBUG)


class TestFlowRequestAPI(TestCase):
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(TestFlowRequestAPI, cls).setUpClass()
        start_mock_server('certs', MockConsentManagerRequestHandler, CONSENT_MANAGER_PORT)
        start_mock_server('certs', MockBackendRequestHandler, HGW_BACKEND_PORT)

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
            'expire_validity': '2018-10-23T10:00:00+02:00',
            'sources': [{
                'source_id': SOURCE_1_ID
            }]
        }
        self.flow_request_without_sources = self.flow_request.copy()
        del self.flow_request_without_sources['sources']

        self.encrypter = Cipher(public_key=RSA.importKey(DEST_PUBLIC_KEY))

        with open(os.path.abspath(os.path.join(BASE_DIR, '../hgw_frontend/fixtures/test_data.json'))) as fixtures_file:
            self.fixtures = json.load(fixtures_file)

        self.destinations = {obj['pk']: obj['fields'] for obj in self.fixtures
                             if obj['model'] == 'hgw_frontend.destination'}
        self.profiles = {obj['pk']: obj['fields'] for obj in self.fixtures
                         if obj['model'] == 'hgw_common.profile'}
        self.flow_requests = {obj['pk']: obj['fields'] for obj in self.fixtures
                              if obj['model'] == 'hgw_frontend.flowrequest'}
        self.sources = {obj['pk']: {
            'source_id': obj['fields']['source_id'],
            'name': obj['fields']['name'],
            'profile':  self.profiles[obj['fields']['profile']]
        } for obj in self.fixtures if obj['model'] == 'hgw_frontend.source'}

    def set_mock_kafka_consumer(self, mock_kc_klass):
        mock_kc_klass.FIRST = 3
        mock_kc_klass.END = 33
        message = self.encrypter.encrypt(1000000 * 'a')
        mock_kc_klass.MESSAGES = {i: MockMessage(key=b'33333', offset=i,
                                                 topic=DEST_1_ID.encode('utf-8'),
                                                 value=message) for i in range(mock_kc_klass.FIRST, mock_kc_klass.END)}

    @staticmethod
    def _get_client_data(client_name=DEST_1_NAME):
        app = RESTClient.objects.get(name=client_name)
        return app.client_id, app.client_secret

    def _add_flow_request(self, client_name=DEST_1_NAME, flow_request=None):
        if flow_request is None:
            flow_request = self.flow_request

        headers = self._get_oauth_header(client_name)
        return self.client.post('/v1/flow_requests/', data=json.dumps(flow_request),
                                content_type='application/json', **headers)

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

    def test_oauth_flow_request_not_authorized(self):
        res = self.client.get('/v1/flow_requests/search/', content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': ['not_authenticated']})

        for m in ('post', 'get'):
            met = getattr(self.client, m)
            res = met('/v1/flow_requests/', content_type='application/json')
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json(), {'errors': ['not_authenticated']})

        for m in ('put', 'get', 'delete'):
            met = getattr(self.client, m)
            res = met('/v1/flow_requests/1/')
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json(), {'errors': ['not_authenticated']})

    def test_get_all_flow_requests_for_a_destination(self):
        """
        Tests get all flow requests for a destination. It returns only the ones belonging to the destination
        """
        # The flow requests are already present in test data
        headers = self._get_oauth_header()
        res = self.client.get('/v1/flow_requests/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['X-Total-Count'], '1')

    def test_get_one_flow_request_for_a_destination(self):
        """
        Tests retrieval of one flow request. The flow request belongs to the destination
        """
        headers = self._get_oauth_header()
        res = self.client.get('/v1/flow_requests/p_11111/', **headers)
        self.assertEqual(res.status_code, 200)
        profile = {
            'code': 'PROF_001',
            'version': 'v0',
            'payload': '[{"clinical_domain": "Laboratory"}]'
        }
        expected = {
            'flow_id': 'f_11111',
            'process_id': 'p_11111',
            'status': 'PE',
            'profile': profile,
            'sources': [{
                'source_id': SOURCE_1_ID,
                'name': SOURCE_1_NAME,
                'profile': profile
            }],
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }
        self.assertDictEqual(res.json(), expected)

    def test_get_all_flow_requests_as_super_client(self):
        """
        Tests get all flow requests from a client with super role. It returns all the flow requests
        """
        # The flow requests are already present in test data
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/flow_requests/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['X-Total-Count'], '4')

    def test_get_one_flow_requests_as_super_client(self):
        """
        Tests get all flow requests from from a client with super role. It returns all the flow requests
        """
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/flow_requests/p_11111/', **headers)
        self.assertEqual(res.status_code, 200)
        profile = {
            'code': 'PROF_001',
            'version': 'v0',
            'payload': '[{"clinical_domain": "Laboratory"}]'
        }
        expected = {
            'flow_id': 'f_11111',
            'process_id': 'p_11111',
            'status': 'PE',
            'profile': profile,
            'sources': [{
                'source_id': SOURCE_1_ID,
                'name': SOURCE_1_NAME,
                'profile': profile
            }],
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }
        self.assertDictEqual(res.json(), expected)

    def test_not_owned_flow_request(self):
        """
        Tests that when getting a flow request from the destination that doesn't own it, it returns an error
        """
        # the flow request belongs to DEST_2
        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/flow_requests/33333/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertDictEqual(res.json(), {'errors': ['not_found']})

    def test_get_all_flow_requests_db_error(self):
        """
        Tests error 500 in case of an error with the db
        """
        # The flow requests are already present in test data
        headers = self._get_oauth_header()
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.flow_requests.FlowRequest', mock):
            res = self.client.get('/v1/flow_requests/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_all_flow_requests_db_error_superclient(self):
        """
        Tests error 500 in case of an error with the db
        """
        # The flow requests are already present in test data
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.flow_requests.FlowRequest', mock):
            res = self.client.get('/v1/flow_requests/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_one_flow_request_db_error(self):
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.flow_requests.FlowRequest', mock):
            headers = self._get_oauth_header()
            res = self.client.get('/v1/flow_requests/p_11111/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_one_flow_request_as_superuser_db_error(self):
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.flow_requests.FlowRequest', mock):
            headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
            res = self.client.get('/v1/flow_requests/p_11111/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_add_flow_request_with_no_sources(self):
        """
        Tests adding a flow request without specifying the sources.
        It tests that the request is added but its status is set to PENDING. It also tests
        that the Sources are all the Sources in the db.
        NB: Note that it is testing also the case when the source returned from the backend
        is not present in the frontend db.
        """
        res = self._add_flow_request(flow_request=self.flow_request_without_sources)
        self.assertEqual(res.status_code, 201)
        flow_request = res.json()
        destination = Destination.objects.get(name='Destination 1')
        self.assertEqual(flow_request['flow_id'], self.flow_request['flow_id'])
        self.assertEqual(flow_request['status'], 'PE')
        self.assertDictEqual(flow_request['profile'], self.flow_request['profile'])
        self.assertEqual(FlowRequest.objects.all().count(), 5)
        self.assertEqual(ConfirmationCode.objects.all().count(), 1)
        self.assertEqual(FlowRequest.objects.get(flow_id=flow_request['flow_id']).destination, destination)
        flow_request_sources = FlowRequest.objects.get(flow_id=flow_request['flow_id']).sources.all()
        all_sources = Source.objects.all()
        self.assertEqual(list(flow_request_sources), list(all_sources))

    def test_add_flow_request_db_error(self):
        """
        Test the response in case of database error
        """
        mock = get_db_error_mock()
        with patch('hgw_frontend.views.flow_requests.Source', mock):
            for flow_request in (self.flow_request, self.flow_request_without_sources):
                res = self._add_flow_request(flow_request=flow_request)
                self.assertEqual(res.status_code, 500)
                self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

        with patch('hgw_frontend.views.flow_requests.FlowRequest', mock) and \
            patch('hgw_frontend.serializers.FlowRequest', mock):
            mock.PENDING = 'PE'
            for flow_request in (self.flow_request, self.flow_request_without_sources):
                res = self._add_flow_request(flow_request=flow_request)
                self.assertEqual(res.status_code, 500)
                self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})
        
        with patch('hgw_frontend.serializers.Profile', mock):
            for flow_request in (self.flow_request, self.flow_request_without_sources):
                res = self._add_flow_request(flow_request=flow_request)
                self.assertEqual(res.status_code, 500)
                self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_add_flow_request_with_sources(self):
        """
        Tests adding a flow request without specifying the sources. 
        It tests that the request is added but its status is set to PENDING. It also tests
        that the Sources are all the Sources in the db
        """
        res = self._add_flow_request(flow_request=self.flow_request)
        self.assertEqual(res.status_code, 201)
        flow_request = res.json()
        destination = Destination.objects.get(name='Destination 1')
        self.assertEqual(flow_request['flow_id'], self.flow_request['flow_id'])
        self.assertEqual(flow_request['status'], 'PE')
        self.assertDictEqual(flow_request['profile'], self.flow_request['profile'])
        self.assertEqual(FlowRequest.objects.all().count(), 5)
        self.assertEqual(ConfirmationCode.objects.all().count(), 1)
        self.assertEqual(FlowRequest.objects.get(flow_id=flow_request['flow_id']).destination, destination)
        self.assertEqual(FlowRequest.objects.get(flow_id=flow_request['flow_id']).sources.count(), 1)
        source = FlowRequest.objects.get(flow_id=flow_request['flow_id']).sources.first()
        self.assertDictEqual(
            {'source_id': source.source_id, 'name': source.name},
            {'source_id': SOURCE_1_ID, 'name': SOURCE_1_NAME}
        )

    def test_add_flow_requests_with_null_profile(self):
        """
        Tests adding a flow request with null profile. It tests that the request is added but its status is set to PENDING
        """
        flow_request = {
            'flow_id': 'f_44444',
            'profile': None,
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }
        res = self._add_flow_request(flow_request=flow_request)
        self.assertEqual(res.status_code, 201)

        flow_request = res.json()
        destination = Destination.objects.get(name='Destination 1')
        self.assertEqual(flow_request['flow_id'], self.flow_request['flow_id'])
        self.assertEqual(flow_request['status'], 'PE')
        self.assertEqual(flow_request['profile'], None)
        self.assertEqual(FlowRequest.objects.count(), 5)
        self.assertEqual(ConfirmationCode.objects.all().count(), 1)
        self.assertEqual(FlowRequest.objects.get(flow_id=flow_request['flow_id']).destination, destination)

    def test_add_flow_requests_without_profile(self):
        """
        Tests adding a flow request without profile. It tests that the request is added but its status is set to PENDING
        """
        flow_request = {
            'flow_id': 'f_44444',
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }
        res = self._add_flow_request(flow_request=flow_request)
        self.assertEqual(res.status_code, 201)

        flow_request = res.json()
        destination = Destination.objects.get(name='Destination 1')
        self.assertEqual(flow_request['flow_id'], self.flow_request['flow_id'])
        self.assertEqual(flow_request['status'], 'PE')
        self.assertEqual(flow_request['profile'], None)
        self.assertEqual(FlowRequest.objects.all().count(), 5)
        self.assertEqual(ConfirmationCode.objects.all().count(), 1)
        self.assertEqual(FlowRequest.objects.get(flow_id=flow_request['flow_id']).destination, destination)

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_flow_requests_unauthorized(self):
        """
        Tests failure when adding flow request with a client not authenticated (i.e., the request doesn't include
        the oauth2 header)
        """
        res = self.client.post('/v1/flow_requests/', data=json.dumps(self.flow_request),
                               content_type='application/json')

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': ['not_authenticated']})

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_flow_requests_forbidden(self):
        """
        Tests failure when adding flow request with a client which is not authorized (i.e., id doesn't have the correct
        oauth2 scope)
        """
        # The dispatcher in test data doesn't have the flow_request:write authorization
        res = self._add_flow_request(client_name=POWERLESS_NAME)
        self.assertEqual(res.status_code, 403)

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_duplicated_profile_requests(self):
        """
        Tests failure when adding a flow request and the profile sent has the same code but different payload than a
        profile already inserted
        :return:
        """
        # We change the profile of the original flow request. Notice that in test data there is already a flow request
        profile = {
            'code': 'PROF_002',
            'version': 'v0',
            'payload': '[{"clinical_domain": "Laboratory"}]'
        }
        flow_request = {
            'flow_id': 'f_11111',
            'profile': profile,
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }

        res = self._add_flow_request(flow_request=flow_request)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), ERRORS_MESSAGE['INVALID_DATA'])

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_flow_requests_no_validity_range_provided(self):
        """
        Tests that if the start and end validity are not specified, the flow request is still added regualarly.
        """
        flow_request = self.flow_request.copy()
        del flow_request['start_validity']
        del flow_request['expire_validity']

        res = self._add_flow_request(flow_request=flow_request)

        self.assertEqual(res.status_code, 201)
        start_validity = parse(res.json()['start_validity'], ignoretz=True)
        expire_validity = parse(res.json()['expire_validity'], ignoretz=True)

        self.assertEqual(expire_validity, start_validity + timedelta(days=180))

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_flow_request_only_one_validity_date_provided(self):
        """
        Tests that if only one of the validity data is specified the creation of the flow request fails
        """
        for param in ('start_validity', 'expire_validity'):
            flow_request = self.flow_request.copy()
            del flow_request['start_validity']
            res = self._add_flow_request(flow_request=flow_request)

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_flow_requests_wrong_content_type(self):
        """
        Tests error when adding a flow request with the wrong content type (i.e., != from application/json)
        """
        headers = self._get_oauth_header()
        res = self.client.post('/v1/flow_requests/', data=self.flow_request, **headers)
        self.assertEqual(res.status_code, 415)

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_add_flow_requests_forcing_status(self):
        """
        Tests that if the requester, adding a flow request, tries to force the status to ACTIVE,
        the status is still set to PENDING
        """
        flow_request = self.flow_request.copy()
        flow_request.update({
            'process_id': '22222',
            'status': FlowRequest.ACTIVE
        })

        res = self._add_flow_request(flow_request=flow_request)
        self.assertEqual(res.status_code, 201)
        res_flow_request = res.json()
        self.assertEqual(res_flow_request['flow_id'], flow_request['flow_id'])
        self.assertNotEqual(res_flow_request['process_id'], flow_request['process_id'])
        self.assertEqual(res_flow_request['status'], 'PE')
        self.assertDictEqual(res_flow_request['profile'], flow_request['profile'])
        self.assertEqual(FlowRequest.objects.all().count(), 5)

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_confirm_duplicated_consent(self):
        """
        Test that, if the consent manager returns a 400 status (meaning that the consent is already present),
        the Flow Request is not confirmed
        """
        # We create the flow request
        res = self._add_flow_request(flow_request=self.flow_request)
        confirm_id = res.json()['confirm_id']
        process_id = res.json()['process_id']
        callback_url = 'http://127.0.0.1/'

        # Then we login as mouse since the mock is configured to return 400 with "mouse" login
        self.client.login(username='mouse', password='duck')
        # Then we confirm the request.
        res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=add'.format(
            confirm_id, callback_url))
        self.assertRedirects(res, "{}?process_id={}&success=false&error={}".format(callback_url, process_id,
                                                                                   ERRORS_MESSAGE['ALL_CONSENTS_ALREADY_CREATED']),
                             fetch_redirect_response=False)

    def test_confirm_redirect(self):
        """
        Tests that the confirm url redirect to the identity provider to authenticate
        """
        res = self.client.get('/v1/flow_requests/confirm/')
        self.assertRedirects(res, '/saml2/login/?next=/v1/flow_requests/confirm/', fetch_redirect_response=False)

    def test_confirm_wrong_method(self):
        """
        Tests wrong method that accessing to /v1/flow_requests/confirm/ using the wrong HTTP method is not supported
        """
        self.client.login(username='duck', password='duck')
        for method in ('post', 'put', 'head', 'options', 'delete', 'trace'):
            met = getattr(self.client, method)
            res = met('/v1/flow_requests/confirm/')
            self.assertEqual(res.status_code, 405)

    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_confirm_invalid_action(self):
        """
        Tests that, when confirming a flow request, when in the url the action parameter is not "add" or "delete",
        it returns an appropriate error
        """
        headers = self._get_oauth_header()
        # using delete but it doesn't matter if it's delete or add
        res = self.client.delete('/v1/flow_requests/p_11111/', **headers)
        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=NOT_VALID'.format(
            confirm_id, callback_url))

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['UNKNOWN_ACTION'])

    def test_confirm_missing_parameters(self):
        """
        Test failure when confirming a flow requests and not sending the correct parameters
        """
        headers = self._get_oauth_header()

        # using delete but it doesn't matter if it's delete or add
        res = self.client.delete('/v1/flow_requests/p_11111/', **headers)

        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/flow_requests/confirm/')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

        res = self.client.get(
            '/v1/flow_requests/confirm/?confirm_id={}&callback_url={}'.format(confirm_id, callback_url))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

        res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&action=delete'.format(confirm_id))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

        res = self.client.get('/v1/flow_requests/confirm/?callback_url={}&action=delete'.format(confirm_id))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

    def test_confirm_invalid_confirmation_code(self):
        """
        Test error when sending an invalid confirmation code to confirm url
        """
        headers = self._get_oauth_header()

        # using delete but it doesn't matter if it's delete or add
        self.client.delete('/v1/flow_requests/p_11111/', **headers)
        callback_url = 'http://127.0.0.1/'
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/flow_requests/confirm/?confirm_id=invalid&callback_url={}&action=delete'.format(
            callback_url,
        ))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['INVALID_CONFIRMATION_CODE'])

    def test_confirm_add_wrong_flow_request_state(self):
        """
        Test errors when confirming a flow request creation which is not in PENDING status
        """
        # create fake flow request with active status
        profile = Profile.objects.get(pk=1)
        destination = Destination.objects.get(pk=1)
        data = {
            'flow_id': '112233',
            'process_id': '332211',
            'status': FlowRequest.ACTIVE,
            'profile': profile,
            'destination': destination,
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }
        flow_request = FlowRequest.objects.create(**data)
        flow_request.save()
        cc = ConfirmationCode.objects.create(flow_request=flow_request)
        cc.save()

        callback_url = 'http://127.0.0.1/'
        self.client.login(username='duck', password='duck')
        for status in [s[0] for s in FlowRequest.STATUS_CHOICES if s[0] != FlowRequest.PENDING]:
            flow_request.status = status
            flow_request.save()
            res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=add'.format(
                cc.code,
                callback_url
            ))
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['INVALID_FR_STATUS'])

    def test_confirm_delete_wrong_flow_request_state(self):
        """
        Test errors when confirming a flow request deletion which is not in ACTIVE status

        """
        # create fake flow request with active status
        profile = Profile.objects.get(pk=1)
        destination = Destination.objects.get(pk=1)

        data = {
            'flow_id': '112233',
            'process_id': '332211',
            'status': FlowRequest.ACTIVE,
            'profile': profile,
            'destination': destination,
            'start_validity': '2017-10-23T10:00:00+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }
        flow_request = FlowRequest.objects.create(**data)
        flow_request.save()
        cc = ConfirmationCode.objects.create(flow_request=flow_request)
        cc.save()

        callback_url = 'http://127.0.0.1/'
        self.client.login(username='duck', password='duck')
        for status in [s[0] for s in FlowRequest.STATUS_CHOICES if s[0] != FlowRequest.DELETE_REQUESTED]:
            flow_request.status = status
            flow_request.save()
            res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=delete'.format(
                cc.code,
                callback_url
            ))
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['INVALID_FR_STATUS'])

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_confirm_missing_person_id(self):
        """
        Tests that if the person logged does not have a correct ID (i.e., fiscalNumber), the confirmation fails
        :return:
        """
        self.client.login(username='admin', password='admin')
        res = self.client.get('/v1/flow_requests/confirm/?consent_confirm_id={}'.format(CORRECT_CONFIRM_ID))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PERSON_ID'])

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_CLIENT_ID', 'wrong_client_id')
    def test_confirm_fail_consent_oauth_token(self):
        """
        Tests that, if an error occurs when getting the token from consent (i.e., wrong oauth2 client parameters) the client is 
        redirected to callback_url with an appropriate error message
        """
        # First perform an add request that creates the flow request with status 'PENDING'
        res = self._add_flow_request()
        confirm_id = res.json()['confirm_id']
        process_id = res.json()['process_id']
        callback_url = 'http://127.0.0.1/'

        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=add'.format(
            confirm_id, callback_url))
        self.assertRedirects(res, "{}?process_id={}&success=false&error={}".format(callback_url, process_id, ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']),
                             fetch_redirect_response=False)

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', 'https://localhost')
    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_confirm_cannot_contact_consent_when_getting_oauth2_token(self):
        """
        Tests that, if a connection error occurs getting the oauth token from the backend, 
        the request to confirm fails and the client is redirected to the callback url with an error parameter
        """
        # First perform an add request that creates the flow request with status 'PENDING'
        res = self._add_flow_request()
        confirm_id = res.json()['confirm_id']
        process_id = res.json()['process_id']
        callback_url = 'http://127.0.0.1/'

        # Then confirm the request. This will cause a redirect to consent manager
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=add'.format(
            confirm_id, callback_url))
        self.assertRedirects(res, "{}?process_id={}&success=false&error={}".format(callback_url, process_id, ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']),
                             fetch_redirect_response=False)

    # @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', 'https://localhost')
    # @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    # def test_confirm_cannot_contact_consent_when_creating_consents(self):
    #     """
    #     Tests that, if a connection error occurs creating the consents into the backend
    #     the request to confirm fails and the client is redirected to the callback url with an error parameter
    #     """
    #     # First perform an add request that creates the flow request with status 'PENDING'
    #     res = self._add_flow_request()
    #     confirm_id = res.json()['confirm_id']
    #     process_id = res.json()['process_id']
    #     callback_url = 'http://127.0.0.1/'
    #     # Inserts a fake access token to skip the request of a new token and the firts request will be GET /v1/sources
    #     AccessToken.objects.create(token_url='https://localhost/oauth2/token/',
    #                                access_token='C3wxJNSLfeLIwHGwnWiIbZPHLTT9a8',
    #                                token_type='Bearer',
    #                                expires_in=36000,
    #                                expires_at=datetime.now() + timedelta(36000),
    #                                scope=['read', 'write'])

    #     self.client.login(username='duck', password='duck')
    #     res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=add'.format(
    #         confirm_id, callback_url))
    #     self.assertRedirects(res, "{}?process_id={}&success=false&error={}".format(callback_url, process_id, ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']),
    #                          fetch_redirect_response=False)

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    @patch('hgw_frontend.views.flow_requests.HGW_BACKEND_URI', HGW_BACKEND_URI)
    def test_confirm_add_flow_request_redirect_to_consent_manager(self):
        """
        Tests that confirmation of flow request, when the user is logged in, redirect to consent manager
        """
        # TODO: We should check that the post call to consent_manager is performed with the correct params
        # First perform an add request that creates the flow request with status 'PENDING'
        res = self._add_flow_request()
        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'
        previous_consent_confirmation_count = ConsentConfirmation.objects.count()

        # Then confirm the request. This will cause a redirect to consent manager
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=add'.format(
            confirm_id, callback_url))

        self.assertEqual(res.status_code, 302)
        self.assertEqual(ConsentConfirmation.objects.count(), previous_consent_confirmation_count + 1)
        flow_request = ConfirmationCode.objects.get(code=confirm_id).flow_request
        self.assertEqual(flow_request.person_id, PERSON_ID)

        channels = Channel.objects.filter(flow_request=flow_request)
        for channel in channels:
            self.assertIn(channel.source.source_id, [s['source_id'] for pk, s in self.sources.items()])
            self.assertIn(channel.status, Channel.CONSENT_REQUESTED)

        consent_confirm_id = ConsentConfirmation.objects.last().confirmation_id
        consent_callback_url = 'https://testserver/v1/flow_requests/consents_confirmed/'
        self.assertRedirects(res, '{}?confirm_id={}&callback_url={}'.
                             format(CONSENT_MANAGER_CONFIRMATION_PAGE, consent_confirm_id,
                                    consent_callback_url),
                             fetch_redirect_response=False)

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_confirm_add_flow_request_confirmed_consent(self):
        """
        Tests the correct confirmation process. It checks that the FlowRequest and the Channels are set to 
        WAITING_SOURCE_NOTIFICATION and that the Kafka message is sent
        """
        self.client.login(username='duck', password='duck')
        # Gets the confirmation code installed with the test data
        c = ConsentConfirmation.objects.get(confirmation_id=CORRECT_CONFIRM_ID)
        res = self.client.get(
            '/v1/flow_requests/consents_confirmed/?success=true&consent_confirm_id={}'.format(CORRECT_CONFIRM_ID))

        redirect_url = '{}?process_id={}&status=ok&success=true'.format(c.destination_endpoint_callback_url,
                                                              c.flow_request.process_id)
        self.assertRedirects(res, redirect_url, fetch_redirect_response=False)
        flow_request = c.flow_request
        self.assertEqual(flow_request.status, FlowRequest.ACTIVE)
        channel = ConsentConfirmation.objects.get(confirmation_id=CORRECT_CONFIRM_ID).channel
        # It remain CR until the consent notification consumer gets the change
        self.assertEqual(channel.status, Channel.CONSENT_REQUESTED)

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_confirm_add_flow_request_wrong_consent_status(self):
        """
        Tests the behavior when a user try to call the /flow_requests/confirm view with a consent_confirm_id of a
        consent not confirmed. It uses flow_request with 'no_consent' and consent with id 'not_confirmed' (status PE)
        (check test data)
        :return:
        """
        self.client.login(username='duck', password='duck')
        res = self.client.get(
            '/v1/flow_requests/consents_confirmed/?success=true&consent_confirm_id={}'.format(WRONG_CONFIRM_ID))
        self.assertEqual(res.status_code, 302)
        flow_request = FlowRequest.objects.get(flow_id='f_11111')
        self.assertEqual(flow_request.status, FlowRequest.PENDING)
        for channel in Channel.objects.filter(flow_request=flow_request):
            channel.status = Channel.CONSENT_REQUESTED

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_multiple_consent_confirms_request(self):

        self.client.login(username='duck', password='duck')
        confirms_id = (CORRECT_CONFIRM_ID, CORRECT_CONFIRM_ID2)
        # First we force the channel status to CONSENT_REQUESTED
        for confirm_id in confirms_id:
            c = ConsentConfirmation.objects.get(confirmation_id=confirm_id)
            c.channel.status = Channel.CONSENT_REQUESTED
            c.channel.save()

        res = self.client.get(
            '/v1/flow_requests/consents_confirmed/?success=true&consent_confirm_id={}&consent_confirm_id={}'.format(
                *confirms_id))
        self.assertEqual(res.status_code, 302)

        for confirm_id in confirms_id:
            c = ConsentConfirmation.objects.get(confirmation_id=confirm_id)
            self.assertEqual(c.flow_request.status, FlowRequest.ACTIVE)
            self.assertEqual(c.channel.status, Channel.CONSENT_REQUESTED)

        redirect_url = '{}?process_id={}&status=ok&success=true'.format(c.destination_endpoint_callback_url,
                                                              c.flow_request.process_id)
        self.assertRedirects(res, redirect_url, fetch_redirect_response=False)

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_confirm_add_flow_request_invalid_consent(self):
        """
        Tests the behavior when a user tries to call the /flow_requests/confirm view with a consent_confirm_id of an
        unknwon consent.
        :return:
        """
        self.client.login(username='duck', password='duck')
        res = self.client.get(
            '/v1/flow_requests/consents_confirmed/?success=true&consent_confirm_id=aaaaa')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content.decode('utf-8'), ERRORS_MESSAGE['INVALID_DATA'])

    @patch('hgw_frontend.views.flow_requests.CONSENT_MANAGER_URI', CONSENT_MANAGER_URI)
    def test_aborted_consent_confirms_request(self):

        self.client.login(username='duck', password='duck')

        c = ConsentConfirmation.objects.get(confirmation_id=ABORTED_CONFIRM_ID)
        c.channel.status = Channel.CONSENT_REQUESTED
        c.channel.save()

        res = self.client.get(
            '/v1/flow_requests/consents_confirmed/?success=false&status=aborted&consent_confirm_id={}'.format(
                ABORTED_CONFIRM_ID))
        self.assertEqual(res.status_code, 302)

        c = ConsentConfirmation.objects.get(confirmation_id=ABORTED_CONFIRM_ID)
        self.assertEqual(c.flow_request.status, FlowRequest.DELETE_REQUESTED)
        self.assertEqual(c.channel.status, Channel.CONSENT_ABORTED)

        redirect_url = '{}?process_id={}&status=aborted&success=false'.format(c.destination_endpoint_callback_url,
                                                                        c.flow_request.process_id)
        self.assertRedirects(res, redirect_url, fetch_redirect_response=False)

    def test_delete_flow_requests(self):
        headers = self._get_oauth_header()

        res = self.client.delete('/v1/flow_requests/p_11111/', **headers)
        self.assertEqual(res.status_code, 202)
        self.assertTrue('confirm_id' in res.json())
        self.assertEqual(FlowRequest.objects.all().count(), 4)
        self.assertEqual(FlowRequest.objects.get(process_id='p_11111').status, FlowRequest.DELETE_REQUESTED)

    # def test_confirm_delete_flow_requests(self):
    #     headers = self._get_oauth_header()

    #     res = self.client.delete('/v1/flow_requests/p_11111/', **headers)

    #     # Then confirm the request
    #     confirm_id = res.json()['confirm_id']
    #     callback_url = 'http://127.0.0.1/'

    #     self.client.login(username='duck', password='duck')
    #     res = self.client.get('/v1/flow_requests/confirm/?confirm_id={}&callback_url={}&action=delete'.format(
    #         confirm_id,
    #         callback_url
    #     ))
    #     self.assertRedirects(res, callback_url, fetch_redirect_response=False)
    #     self.assertRaises(FlowRequest.DoesNotExist, FlowRequest.objects.get, process_id='p_11111')

    def test_search_flow_request_by_channel_id_with_super_client(self):
        """
        Tests functionality of getting the flow request by channel id, using a REST client with super client
        """
        # Gets the confirmation code installed with the test data
        c = ConsentConfirmation.objects.get(confirmation_id=CORRECT_CONFIRM_ID)

        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/flow_requests/search/?channel_id={}'.format(c.channel.channel_id), **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['process_id'], 'p_11111')
        self.assertEqual(res['X-Total-Count'], '1')

    def test_search_flow_request_by_channel_id_with_standard_client(self):
        """
        Tests that getting the flow request by channel id, using non admin REST client is forbidden
        """
        # Gets the confirmation code installed with the test data
        c = ConsentConfirmation.objects.get(confirmation_id=CORRECT_CONFIRM_ID)
        headers = self._get_oauth_header(client_name=DEST_1_NAME)
        res = self.client.get('/v1/flow_requests/search/?channel_id={}'.format(c.channel.channel_id), **headers)
        self.assertEqual(res.status_code, 403)

    def test_search_flow_request_by_channel_id_db_error(self):
        c = ConsentConfirmation.objects.get(confirmation_id=CORRECT_CONFIRM_ID)

        mock = get_db_error_mock()
        with patch('hgw_frontend.views.flow_requests.Channel', mock):
            headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
            res = self.client.get('/v1/flow_requests/search/?channel_id={}'.format(c.channel.channel_id), **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_flow_request_by_channel_id_wrong_channel_id(self):
        """
        Test that if the channel id is not found, it returns a 404 error
        """
        headers = self._get_oauth_header(client_name=DISPATCHER_NAME)
        res = self.client.get('/v1/flow_requests/search/?channel_id=unknown', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': ['not_found']})
