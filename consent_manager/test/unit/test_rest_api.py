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
import os
from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.test import TestCase, client
from martor.utils import markdownify
from mock import Mock, NonCallableMock, patch

from consent_manager import settings
from consent_manager.models import ConfirmationCode, Consent, RESTClient
from consent_manager.serializers import ConsentSerializer
from hgw_common.utils import ERRORS
from hgw_common.utils.mocks import get_free_port

PORT = get_free_port()

BASE_DIR = os.path.dirname(__file__)
PERSON1_ID = 'AAABBB12C34D567E'
PERSON2_ID = 'FFFGGG12H34I567G'


def _get_serialized_data(consent_serializer):
    serialized_data = {}
    for k, v in consent_serializer.data.items():
        if type(v) is OrderedDict:
            serialized_data[k] = dict(v)
        else:
            serialized_data[k] = v
    return serialized_data


class TestAPI(TestCase):
    fixtures = ['test_data.json']
    maxDiff = None

    def setUp(self):
        self.client = client.Client()
        payload = '[{"clinical_domain": "Laboratory", ' \
                  '"filters": [{"excludes": "HDL", "includes": "immunochemistry"}]}, ' \
                  '{"clinical_domain": "Radiology", ' \
                  '"filters": [{"excludes": "Radiology", "includes": "Tomography"}]}, ' \
                  '{"clinical_domain": "Emergency", ' \
                  '"filters": [{"excludes": "", "includes": ""}]}, ' \
                  '{"clinical_domain": "Prescription", ' \
                  '"filters": [{"excludes": "", "includes": ""}]}]'

        self.profile = {
            'code': 'PROF002',
            'version': 'hgw.document.profile.v0',
            'payload': payload
        }

        self.consent_data = {
            'source': {
                'id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                'name': 'SOURCE_1'
            },
            'destination': {
                'id': 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj',
                'name': 'DEST_MOCKUP'
            },
            'profile': self.profile,
            'person_id': PERSON1_ID,
            'legal_notice_version': 4,
            'start_validity': '2017-10-23T10:00:54.123000+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00'
        }

        self.json_consent_data = json.dumps(self.consent_data)

        self.legal_notice = "# Legal Notice\r\n\r\nNew legal notice\r\n\r\nthe lawyer"

    @staticmethod
    def _get_client_data(client_index=0):
        app = RESTClient.objects.all()[client_index]
        return app.client_id, app.client_secret

    def _get_oauth_token(self, client_index=0):
        c_id, c_secret = self._get_client_data(client_index)
        params = {
            'grant_type': 'client_credentials',
            'client_id': c_id,
            'client_secret': c_secret
        }
        res = self.client.post('/oauth2/token/', data=params)
        return res.json()

    def _get_oauth_header(self, client_index=0):
        res = self._get_oauth_token(client_index)
        access_token = res['access_token']
        return {'Authorization': 'Bearer {}'.format(access_token)}

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

    def test_oauth_scopes(self):
        """
        Tests that the oauth token scopes are taken from the RESTClient field or from default in case it is blank
        """
        # Defaults
        res = self._get_oauth_token(0)
        self.assertListEqual(res['scope'].split(' '), ['consent:read', 'consent:write'])

        # Specified
        res = self._get_oauth_token(1)
        self.assertListEqual(res['scope'].split(' '), ['consent:read'])

        # Specified
        res = self._get_oauth_token(2)
        self.assertListEqual(res['scope'].split(' '), ['consent:read'])

    def test_get_consents(self):
        """
        Tests get functionality with not all details
        """
        expected = {'consent_id': 'q18r2rpd1wUqQjAZPhh24zcN9KCePRyr',
                    'status': 'PE',
                    'start_validity': '2017-10-23T10:00:54.123000+02:00',
                    'expire_validity': '2018-10-23T10:00:00+02:00',
                    'legal_notice_version': 4,
                    'source': {
                        'id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                        'name': 'SOURCE_1'
                    }}

        headers = self._get_oauth_header(client_index=2)
        res = self.client.get('/v1/consents/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        results = res.json()
        for r in results:
            self.assertEqual(dict(r), expected)

        res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(dict(res.json()), expected)

    def test_get_consents_db_error(self):
        """
        Tests get functionality with not all details
        """
        mock = self._get_db_error_mock()
        with patch('consent_manager.views.Consent', mock):
            headers = self._get_oauth_header(client_index=2)
            res = self.client.get('/v1/consents/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

            res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_consents_by_super_client(self):
        """
        Tests get functionality when the restclient is a super client
        """
        expected = {
            'status': 'PE',
            'start_validity': '2017-10-23T10:00:54.123000+02:00',
            'expire_validity': '2018-10-23T10:00:00+02:00',
            'profile': {
                'code': 'PROF002',
                'version': 'hgw.document.profile.v0',
                'payload': '[{"clinical_domain": "Laboratory", "filters": [{"excludes": "HDL", "includes": "immunochemistry"}]}, {"clinical_domain": "Radiology", "filters": [{"excludes": "Radiology", "includes": "Tomography"}]}, {"clinical_domain": "Emergency", "filters": [{"excludes": "", "includes": ""}]}, {"clinical_domain": "Prescription", "filters": [{"excludes": "", "includes": ""}]}]'
            },
            'destination': {
                'id': 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj',
                'name': 'DEST_MOCKUP'
            },
            'consent_id': 'q18r2rpd1wUqQjAZPhh24zcN9KCePRyr',
            'person_id': PERSON1_ID,
            'legal_notice_version': 4,
            'source': {
                'id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                'name': 'SOURCE_1'
            }
        }

        headers = self._get_oauth_header(client_index=1)
        res = self.client.get('/v1/consents/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        results = res.json()
        for r in results:
            self.assertEqual(dict(r), expected)

        res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), expected)

    def test_get_consent_by_superclient_db_error(self):
        """
        Tests get functionality with not all details
        """
        mock = self._get_db_error_mock()
        with patch('consent_manager.views.Consent', mock):
            headers = self._get_oauth_header(client_index=1)
            res = self.client.get('/v1/consents/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

            res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_get_consent_not_found(self):
        """
        Tests not found consent
        :return:
        """
        headers = self._get_oauth_header()
        res = self.client.get('/v1/consents/unknown/', **headers)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_FOUND]})

    def test_get_consent_forbidden(self):
        """
        Test failure when getting consents from a client with no consent:read scope
        """
        headers = self._get_oauth_header(client_index=3)
        res = self.client.get('/v1/consents/', **headers)
        self.assertEqual(res.status_code, 403)

        res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
        self.assertEqual(res.status_code, 403)

    def _add_consent(self, data=None, client_index=0, status=Consent.PENDING):
        headers = self._get_oauth_header(client_index)
        data = data or self.json_consent_data
        res = self.client.post('/v1/consents/', data=data,
                               content_type='application/json', **headers)
        if 'consent_id' in res.json():
            c = Consent.objects.get(consent_id=res.json()['consent_id'])
            c.status = status
            c.save()
        return res

    def test_add(self):
        """
        Test correct add consent
        """
        res = self._add_consent()
        consent_id = res.json()['consent_id']

        expected = self.consent_data.copy()
        expected.update({
            'status': 'PE',
            'consent_id': consent_id,
            'person_id': PERSON1_ID,
        })

        c = Consent.objects.get(consent_id=consent_id)
        serializer = ConsentSerializer(c)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(set(res.json().keys()), {'consent_id', 'confirm_id'})
        self.assertEqual(serializer.data['legal_notice_version'], expected['legal_notice_version'])
        self.assertEqual(dict(serializer.data), expected)

    def test_add_db_error(self):
        """
        Test add in case of db error
        """
        mock = self._get_db_error_mock()
        with patch('consent_manager.serializers.Consent', mock):
            res = self._add_consent()
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_add_other_timezone(self):
        """
        Tests that when the date is sent using timezone different from settings.TIME_ZONE,
        when it is returned is still represented with settings.TIME_ZONE timezone.
        """
        for tz in (('08', 'Z'), ('09', '+01:00')):
            consent_data = self.consent_data.copy()
            consent_data['start_validity'] = '2017-10-23T{}:00:54.123000{}'.format(tz[0], tz[1])
            consent_data['expire_validity'] = '2018-10-23T{}:00:00{}'.format(tz[0], tz[1])
            res = self._add_consent(data=json.dumps(consent_data))
            consent_id = res.json()['consent_id']
            expected = self.consent_data.copy()
            expected.update({
                'status': 'PE',
                'consent_id': consent_id,
                'person_id': PERSON1_ID,

            })
            c = Consent.objects.get(consent_id=consent_id)
            serializer = ConsentSerializer(c)
            self.assertEqual(res.status_code, 201)
            self.assertEqual(set(res.json().keys()), {'consent_id', 'confirm_id'})

            self.assertEqual(dict(serializer.data), expected)

    def test_add_forbidden(self):
        """
        Test add consent is forbidden when it is missing the correct scopes
        """
        res = self._add_consent(client_index=2)
        self.assertEqual(res.status_code, 403)

    def test_add_too_long_fields(self):
        """
        Test error when adding consent with too long source id and name
        """
        headers = self._get_oauth_header()
        self.consent_data['source'] = {
            'id': 33 * 'a',
            'name': 101 * 'b'
        }
        self.consent_data['destination'] = {
            'id': 33 * 'a',
            'name': 101 * 'b'
        }
        self.json_consent_data = json.dumps(self.consent_data)
        res = self.client.post('/v1/consents/', data=self.json_consent_data, content_type='application/json', **headers)
        expected = {'source': {'id': ['Ensure this field has no more than 32 characters.'],
                               'name': ['Ensure this field has no more than 100 characters.']},
                    'destination': {'id': ['Ensure this field has no more than 32 characters.'],
                                    'name': ['Ensure this field has no more than 100 characters.']}}
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), expected)

    def test_add_duplicated_endpoint(self):
        """
        Test that adding source or destination with the same name or id of an existing one, returns an error
        """
        headers = self._get_oauth_header()
        orig_source_id = self.consent_data['source']['id']
        orig_source_name = self.consent_data['source']['name']
        orig_dest_id = self.consent_data['destination']['id']
        orig_dest_name = self.consent_data['destination']['name']

        # Changing id, keeping the name
        self.consent_data['source'] = {
            'id': 'different_id',
            'name': orig_source_name
        }
        self.consent_data['destination'] = {
            'id': 'different_id',
            'name': orig_dest_name
        }
        self.json_consent_data = json.dumps(self.consent_data)
        res = self.client.post('/v1/consents/', data=self.json_consent_data, content_type='application/json', **headers)
        expected = {
            'source': {'generic_errors': ['An instance with the same name and different id already exists']},
            'destination': {'generic_errors': ['An instance with the same name and different id already exists']}
        }

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), expected)

        # Changing name, keeping the id
        self.consent_data['source'] = {
            'id': orig_source_id,
            'name': 'different_name'
        }
        self.consent_data['destination'] = {
            'id': orig_dest_id,
            'name': 'different_name'
        }
        self.json_consent_data = json.dumps(self.consent_data)
        res = self.client.post('/v1/consents/', data=self.json_consent_data, content_type='application/json', **headers)
        expected = {
            'source': {'generic_errors': ['An instance with the same id and different name already exists']},
            'destination': {'generic_errors': ['An instance with the same id and different name already exists']}
        }

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), expected)

    def test_add_missing_fields(self):
        """
        Test error when adding consent and some fields are missing
        """
        headers = self._get_oauth_header()

        # Missing data
        res = self.client.post('/v1/consents/', data='{}', content_type='application/json', **headers)
        self.assertEqual(res.status_code, 400)
        expected = {
            'source': ['This field is required.'],
            'profile': ['This field is required.'],
            'person_id': ['This field is required.'],
            'destination': ['This field is required.']
        }
        self.assertEqual(res.json(), expected)

    def test_add_empty_fields(self):
        """
        Test error when some the fields are empty {i.e., dict wothout keys}
        """
        headers = self._get_oauth_header()

        # Wrong data
        self.consent_data['profile'] = {}
        self.consent_data['source'] = {}
        self.consent_data['destination'] = {}

        self.json_consent_data = json.dumps(self.consent_data)
        res = self.client.post('/v1/consents/', data=self.json_consent_data, content_type='application/json', **headers)
        expected = {
            'profile': {'code': ['This field is required.'],
                        'payload': ['This field is required.'],
                        'version': ['This field is required.']},
            'source': {'id': ['This field is required.'],
                       'name': ['This field is required.']},
            'destination': {'id': ['This field is required.'],
                            'name': ['This field is required.']},
        }

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), expected)

    def test_add_none_fields(self):
        """
        Test error when some the fields are empty {i.e., dict wothout keys}
        """
        headers = self._get_oauth_header()

        # Wrong data
        self.consent_data = {
            'profile': None,
            'source': None,
            'destination': None,
            'person_id': None,
            'start_validity': None,
            'expire_validity': None
        }

        self.json_consent_data = json.dumps(self.consent_data)
        res = self.client.post('/v1/consents/', data=self.json_consent_data, content_type='application/json', **headers)
        expected = {'profile': ['This field may not be null.'],
                    'source': ['This field may not be null.'],
                    'destination': ['This field may not be null.'],
                    'person_id': ['This field may not be null.']
                    }

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), expected)

    def test_add_duplicated_consent_when_not_active(self):
        """
        Tests that when adding a consent and there are already other consent
        the Consent is actually added and the old one in PENDING status is set to NOT_VALID status
        """
        # First we add one REVOKED and one NOT_VALID consents
        for status in (Consent.REVOKED, Consent.NOT_VALID):
            self._add_consent(self.json_consent_data, status=status)

        # then we add a PENDING consent
        res = self._add_consent(self.json_consent_data)
        old_pending_consent_id = res.json()['consent_id']

        # finally we add the new consent and check it's added correctly
        res = self._add_consent()
        c = Consent.objects.get(consent_id=old_pending_consent_id)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(c.status, Consent.NOT_VALID)

    def test_add_duplicated_consent_when_active(self):
        """
        Tests error when adding a consent and there is already one ACTIVE status
        """
        self._add_consent(self.json_consent_data, status=Consent.ACTIVE)
        res = self._add_consent(self.json_consent_data)
        expected = {'generic_errors': [ERRORS.DUPLICATED]}
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), expected)

    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_modify(self, mocked_kafka_producer):
        """
        Test consent modification (i.e., update). It can update only the start date and end data
        """
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        updated_data = {
            'start_validity': '2017-09-23T10:00:54.123000+02:00',
            'expire_validity': '2018-09-23T10:00:00+02:00'
        }

        self.client.login(username='duck', password='duck')
        res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {})
        consent = Consent.objects.get(consent_id=consent_id)
        consent_serializer = ConsentSerializer(consent)
        self.assertEqual(consent_serializer.data['start_validity'], updated_data['start_validity'])
        self.assertEqual(consent_serializer.data['expire_validity'], updated_data['expire_validity'])
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][0][0], settings.KAFKA_NOTIFICATION_TOPIC)
        serialized_data = _get_serialized_data(consent_serializer)
        self.assertEqual(json.loads(mocked_kafka_producer().send.call_args_list[0][1]['value'].decode('utf-8')),
                             serialized_data)

    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_modify_db_error(self, mocked_kafka_producer):
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        updated_data = {
            'start_validity': '2017-09-23T10:00:54.123000+02:00',
            'expire_validity': '2018-09-23T10:00:00+02:00'
        }

        mock = self._get_db_error_mock()
        with patch('consent_manager.views.Consent', mock):
            self.client.login(username='duck', password='duck')
            res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                                  content_type='application/json')
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_modify_wrong_status(self):
        """
        Test consent modification failure when the client specifies a consent in the wrong status
        """
        consents = []
        statuses = [Consent.PENDING, Consent.REVOKED, Consent.NOT_VALID]
        for i, s in enumerate(statuses):
            data = self.consent_data.copy()
            data['source'] = {
                'id': 'source_{}_id'.format(i),
                'name': 'source_{}_name'.format(i)
            }
            res = self._add_consent(data=json.dumps(data), status=s)
            consents.append(res.json()['consent_id'])

        updated_data = {
            'start_validity': '2017-11-23T10:00:54.123+02:00',
            'expire_validity': '2018-11-23T10:00:00.000+02:00'
        }
        self.client.login(username='duck', password='duck')
        for i, c in enumerate(consents):
            res = self.client.put('/v1/consents/{}/'.format(c), data=json.dumps(updated_data),
                                  content_type='application/json')
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json(), {'errors': ['wrong_consent_status']})
            c = Consent.objects.get(consent_id=c)
            s = ConsentSerializer(c)
            self.assertEqual(s.data['start_validity'], self.consent_data['start_validity'])
            self.assertEqual(s.data['expire_validity'], self.consent_data['expire_validity'])

    def test_modify_unallowed_fields(self):
        """
        Test consent modification failure when the client specify attributes different from the allowed ones
        """
        res = self._add_consent(status=Consent.ACTIVE)

        consent_id = res.json()['consent_id']

        updated_data = {
            'person_id': 'DIFFERENT_PERSON',
            'expire_validity': '2018-11-23T10:00:00+02:00'
        }

        self.client.login(username='duck', password='duck')
        res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': {'generic_errors': ['attributes_not_editable']}})

    def test_modify_wrong_fields_format(self):
        """
        Test consent modification failure when the client specify attributes in a wronf form
        """
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        updated_data = {
            'start_validity': 'wrong_date_value',
            'expire_validity': '2018-11-23'
        }

        self.client.login(username='duck', password='duck')
        res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': {
            'start_validity': ['invalid_date_format'],
            'expire_validity': ['invalid_date_format']
        }})

    def test_modify_wrong_person(self):
        """
        Test consent modification failure when the client specify a client that doesn't belong to the logged in user
        """

        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        updated_data = {
            'start_validity': '2017-09-23T10:00:54.123000+02:00',
            'expire_validity': '2018-09-23T10:00:00+02:00'
        }

        self.client.login(username='paperone', password='paperone')
        res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': ['wrong_person']})
        c = Consent.objects.get(consent_id=consent_id)
        s = ConsentSerializer(c)
        self.assertEqual(s.data['start_validity'], self.consent_data['start_validity'])
        self.assertEqual(s.data['expire_validity'], self.consent_data['expire_validity'])

    def test_modify_unauthorized(self):
        """
        Test consent modification failure when the client is unauthorized (i.e., it is not logged in)
        """
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']
        updated_data = {
            'start_validity': '2017-11-23T10:00:54.123+02:00',
            'expire_validity': '2018-11-23T10:00:00.000+02:00'
        }
        res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                              content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_AUTHENTICATED]})

    def test_modify_forbidden(self):
        """
        Test consent modification failure when the client is forbidden (i.e., it is using oauth2)
        """
        res = self._add_consent(self.json_consent_data, status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        headers = self._get_oauth_header(0)
        updated_data = {
            'start_validity': '2017-11-23T10:00:54.123+02:00',
            'expire_validity': '2018-11-23T10:00:00.000+02:00'
        }
        res = self.client.put('/v1/consents/{}/'.format(consent_id), data=json.dumps(updated_data),
                              content_type='application/json', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': [ERRORS.FORBIDDEN]})

    def test_modify_not_found(self):
        """
        Test revoke operation for a single consent. Test revoke error when the consent is not found
        """

        self.client.login(username='duck', password='duck')
        res = self.client.put('/v1/consents/unkn/')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_FOUND]})

    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_revoke(self, mocked_kafka_producer):
        """
        Test revoke operation for a single consent. Test that the consent is not revoked in case
        the consent doesn't belong to the logged person
        """

        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        self.client.login(username='duck', password='duck')
        res = self.client.post('/v1/consents/{}/revoke/'.format(consent_id),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {})
        consent = Consent.objects.get(consent_id=consent_id)
        consent_serializer = ConsentSerializer(consent)

        self.assertEqual(consent.status, Consent.REVOKED)
        self.assertEqual(mocked_kafka_producer().send.call_args_list[0][0][0], settings.KAFKA_NOTIFICATION_TOPIC)
        serialized_data = _get_serialized_data(consent_serializer)
        self.assertEqual(json.loads(mocked_kafka_producer().send.call_args_list[0][1]['value'].decode('utf-8')),
                             serialized_data)

    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_revoke_db_error(self, mocked_kafka_producer):
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        mock = self._get_db_error_mock()
        with patch('consent_manager.views.Consent', mock):
            self.client.login(username='duck', password='duck')
            res = self.client.post('/v1/consents/{}/revoke/'.format(consent_id),
                                   content_type='application/json')
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_revoke_wrong_status(self):
        """
        Test revoke operation for a single consent. Test that the consent is not revoked in case
        the consent is not in ACTIVE status
        """
        consents = []
        statuses = [Consent.PENDING, Consent.REVOKED, Consent.NOT_VALID]
        for i, s in enumerate(statuses):
            data = self.consent_data.copy()
            data['source'] = {
                'id': 'source_{}_id'.format(i),
                'name': 'source_{}_name'.format(i)
            }
            res = self._add_consent(data=json.dumps(data), status=s)
            consents.append(res.json()['consent_id'])

        self.client.login(username='duck', password='duck')
        for i, c in enumerate(consents):
            res = self.client.post('/v1/consents/{}/revoke/'.format(c), content_type='application/json')
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json(), {'errors': ['wrong_consent_status']})
            c = Consent.objects.get(consent_id=c)
            self.assertEqual(c.status, statuses[i])

    def test_revoke_wrong_person(self):
        """
        Test revoke operation for a single consent. Test that the consent is not revoked in case
        the consent doesn't belong to the logged person
        """

        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        self.client.login(username='paperone', password='paperone')
        res = self.client.post('/v1/consents/{}/revoke/'.format(consent_id),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': ['wrong_person']})
        c = Consent.objects.get(consent_id=consent_id)
        self.assertEqual(c.status, Consent.ACTIVE)

    def test_revoke_unauthorized(self):
        """
        Tests revoke failure when the user is authenticated but not authorized
        """
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        res = self.client.post('/v1/consents/{}/revoke/'.format(consent_id), data=json.dumps([consent_id]),
                               content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_AUTHENTICATED]})

    def test_revoke_forbidden(self):
        """
        Tests that the revoke action cannot be performed by an OAuth2 authenticated client
        """
        res = self._add_consent(self.json_consent_data, status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        headers = self._get_oauth_header(0)
        res = self.client.post('/v1/consents/{}/revoke/'.format(consent_id), data=json.dumps([consent_id]),
                               content_type='application/json', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': [ERRORS.FORBIDDEN]})

    def test_revoke_not_found(self):
        """
        Test revoke operation for a single consent. Test revoke error when the consent is not found
        """

        self.client.login(username='duck', password='duck')
        res = self.client.post('/v1/consents/unkn/revoke/')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_FOUND]})

    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_revoke_list(self, mocked_kafka_producer):
        """
        Tests consents revocation
        """
        consents = []
        for i in range(4):
            data = self.consent_data.copy()
            data['source'] = {
                'id': 'source_{}_id'.format(i),
                'name': 'source_{}_name'.format(i)
            }
            res = self._add_consent(data=json.dumps(data), status=Consent.ACTIVE)
            consents.append(res.json()['consent_id'])

        self.client.login(username='duck', password='duck')
        revoke_consents = {
            'consents': consents
        }
        res = self.client.post('/v1/consents/revoke/', data=json.dumps(revoke_consents),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['revoked'], consents)
        self.assertEqual(len(res.json()['failed']), 0)
        kafka_mocked_data = [json.loads(x[1]['value'].decode('utf-8'))
                             for x in mocked_kafka_producer().send.call_args_list]
        for index, consent in enumerate(consents):
            consent = Consent.objects.get(consent_id=consent)
            consent_serializer = ConsentSerializer(consent)

            self.assertEqual(consent.status, Consent.REVOKED)
            self.assertEqual(mocked_kafka_producer().send.call_args_list[index][0][0],
                             settings.KAFKA_NOTIFICATION_TOPIC)
            serialized_data = _get_serialized_data(consent_serializer)
            self.assertIn(serialized_data, kafka_mocked_data)

    def test_revoke_list_missing_parameters(self):
        """
        Tests error when not sending consents
        """

        self.client.login(username='duck', password='duck')
        res = self.client.post('/v1/consents/revoke/')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': [ERRORS.MISSING_PARAMETERS]})

    def test_revoke_list_wrong_status(self):
        """
        Tests that if the consent was not in ACTIVE status it is not revoked. It does so by trying to revoke
        3 consent, one for every status (PENDING, REVOKED, NOT_VALID). It checks that the consents have not
        changed
        """
        consents = []
        statuses = [Consent.PENDING, Consent.REVOKED, Consent.NOT_VALID]
        for i, s in enumerate(statuses):
            data = self.consent_data.copy()
            data['source'] = {
                'id': 'source_{}_id'.format(i),
                'name': 'source_{}_name'.format(i)
            }
            res = self._add_consent(data=json.dumps(data), status=s)
            consents.append(res.json()['consent_id'])

        self.client.login(username='duck', password='duck')

        data = {
            'consents': consents
        }
        res = self.client.post('/v1/consents/revoke/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['revoked']), 0)
        self.assertEqual(len(res.json()['failed']), 3)
        self.assertListEqual(sorted(res.json()['failed']), sorted(consents))
        for i, c in enumerate(consents):
            c = Consent.objects.get(consent_id=c)
            self.assertEqual(c.status, statuses[i])

    def test_revoke_list_wrong_user(self):
        """
        Tests that when the logged user is not the owner of the consent to be revoked, the consent is not revoked
        """
        res = self._add_consent(self.json_consent_data, status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']
        self.client.login(username='paperone', password='paperone')
        data = {
            'consents': [consent_id]
        }
        res = self.client.post('/v1/consents/revoke/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['revoked']), 0)
        self.assertEqual(len(res.json()['failed']), 1)
        self.assertEqual(res.json()['failed'][0], consent_id)

    def test_revoke_list_unknown_consent(self):
        """
        Tests error when confirming an unknwown consent
        """
        consent_id = 'unknown'
        self.client.login(username='duck', password='duck')
        data = {
            'consents': [consent_id]
        }
        res = self.client.post('/v1/consents/revoke/', data=json.dumps(data),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['revoked']), 0)
        self.assertEqual(len(res.json()['failed']), 1)
        self.assertEqual(res.json()['failed'][0], consent_id)
        self.assertRaises(Consent.DoesNotExist, Consent.objects.get, consent_id=consent_id)

    def test_revoke_list_unauthorized(self):
        res = self._add_consent(status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']

        res = self.client.post('/v1/consents/revoke/', data=json.dumps([consent_id]),
                               content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_AUTHENTICATED]})

    def test_revoke_list_forbidden(self):
        """
        Tests that the revoke action cannot be performed by an OAuth2 authenticated client
        """
        res = self._add_consent(self.json_consent_data, status=Consent.ACTIVE)
        consent_id = res.json()['consent_id']
        headers = self._get_oauth_header(0)
        res = self.client.post('/v1/consents/revoke/', data=json.dumps([consent_id]),
                               content_type='application/json', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': [ERRORS.FORBIDDEN]})

    def test_find_unauthorized(self):
        res = self._add_consent()

        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        res = self.client.get('/v1/consents/find/?confirm_id={}&callback_url={}'.format(confirm_id, callback_url))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_AUTHENTICATED]})

    def test_find_unauthorized_db_error(self):
        res = self._add_consent()

        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        mock = self._get_db_error_mock()
        with patch('consent_manager.views.ConfirmationCode', mock):
            self.client.login(username='duck', password='duck')
            res = self.client.get('/v1/consents/find/?confirm_id={}&callback_url={}'.format(confirm_id, callback_url))
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {'errors': [ERRORS.DB_ERROR]})

    def test_find_with_oauth_token(self):
        res = self._add_consent()

        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        headers = self._get_oauth_header(0)
        res = self.client.get('/v1/consents/find/?confirm_id={}&callback_url={}'.format(confirm_id, callback_url),
                              **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': [ERRORS.FORBIDDEN]})

    def test_find_missing_parameters(self):
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/find/')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': [ERRORS.MISSING_PARAMETERS]})

    def test_find_not_found(self):
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/find/?confirm_id=unk')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {})

    def test_find(self):
        res = self._add_consent()
        confirm_id = res.json()['confirm_id']
        expected = self.consent_data.copy()
        expected.update({
            'status': 'PE',
            'confirm_id': confirm_id,
            'person_id': PERSON1_ID,
        })
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/find/?confirm_id={}'.format(confirm_id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()[0], expected)

    def _test_confirm(self, null_dates=False):
        """
        Support method that adds the consents and calls the confirmation REST endpoint.
        It returns the consents created and the response
        """
        consents = self._gen_test_consents(null_dates)

        # Then, confirm them
        self.client.login(username='duck', password='duck')
        data = {
            'consents': consents
        }
        res = self.client.post('/v1/consents/confirm/', data=json.dumps(data), content_type='application/json')
        return consents, res

    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_confirm_with_correct_notification(self, mocked_kafka_producer):
        """
        Tests correct consent confirmation
        """
        consents, res = self._test_confirm()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['confirmed']), 4)
        self.assertEqual(len(res.json()['failed']), 0)
        kafka_mocked_data = [json.loads(x[1]['value'].decode('utf-8'))
                             for x in mocked_kafka_producer().send.call_args_list]
        for index, (confirm_id, consent_data) in enumerate(consents.items()):
            consent_obj = ConfirmationCode.objects.get(code=confirm_id).consent
            self.assertEqual(consent_obj.status, Consent.ACTIVE)
            consent_serializer = ConsentSerializer(consent_obj)
            self.assertEqual(consent_serializer.data['start_validity'], consent_data['start_validity'])
            self.assertEqual(consent_serializer.data['expire_validity'], consent_data['expire_validity'])
            self.assertEqual(mocked_kafka_producer().send.call_args_list[index][0][0],
                             settings.KAFKA_NOTIFICATION_TOPIC)
            serialized_data = _get_serialized_data(consent_serializer)
            self.assertIn(serialized_data, kafka_mocked_data)


    @patch('hgw_common.messaging.sender.KafkaProducer')
    def test_confirm_with_correct_notification_and_null_validity_dates(self, mocked_kafka_producer):
        """
        Tests correct consent confirmation with start and expire validity set to null
        """
        consents, res = self._test_confirm(null_dates=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['confirmed']), 4)
        self.assertEqual(len(res.json()['failed']), 0)

        kafka_mocked_data = [json.loads(x[1]['value'].decode('utf-8'))
                             for x in mocked_kafka_producer().send.call_args_list]

        for index, (confirm_id, consent_data) in enumerate(consents.items()):
            consent_obj = ConfirmationCode.objects.get(code=confirm_id).consent
            self.assertEqual(consent_obj.status, Consent.ACTIVE)
            consent_serializer = ConsentSerializer(consent_obj)
            self.assertEqual(consent_serializer.data['start_validity'], None)
            self.assertEqual(consent_serializer.data['expire_validity'], None)

            self.assertEqual(mocked_kafka_producer().send.call_args_list[index][0][0],
                             settings.KAFKA_NOTIFICATION_TOPIC)
            serialized_data = _get_serialized_data(consent_serializer)
            self.assertIn(serialized_data, kafka_mocked_data)

    # def test_confirm_failed_notification(self):
    #     """
    #     Tests correct consent confirmation
    #     """
    #     consents, res = self._test_confirm()

    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(len(res.json()['confirmed']), 4)
    #     self.assertEqual(len(res.json()['failed']), 0)
    #     for index, (confirm_id, consent_data) in enumerate(consents.items()):
    #         consent_obj = ConfirmationCode.objects.get(code=confirm_id).consent
    #         self.assertEqual(consent_obj.status, Consent.ACTIVE)
    #         consent_serializer = ConsentSerializer(consent_obj)
    #         self.assertEqual(consent_serializer.data['start_validity'],
    #                          consent_data['start_validity'])
    #         self.assertEqual(consent_serializer.data['expire_validity'],
    #                          consent_data['expire_validity'])

    def test_confirm_unauthorized(self):
        """
        Tests failure in confirmation when the user is authenticated but not unauthorized
        """
        res = self._add_consent()
        consent = {res.json()['confirm_id']: {}}
        res = self.client.post('/v1/consents/confirm/', data=json.dumps({'consents': consent}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {'errors': [ERRORS.NOT_AUTHENTICATED]})

    def test_confirm_forbidden(self):
        """
        Tests failure in confirmation when the user is not authenticated
        """
        res = self._add_consent()

        consent = {res.json()['confirm_id']: {}}
        headers = self._get_oauth_header(0)
        res = self.client.post('/v1/consents/confirm/', data=json.dumps({'consents': consent}),
                               content_type='application/json', **headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json(), {'errors': [ERRORS.FORBIDDEN]})

    def test_confirm_missing_parameters(self):
        """
        Tests error when not sending consents
        """

        self.client.login(username='duck', password='duck')
        res = self.client.post('/v1/consents/confirm/')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {'errors': [ERRORS.MISSING_PARAMETERS]})

    def test_confirm_wrong_consent_status(self):
        """
        Tests that if the consent was not in PENDING status it is not activated. It does so by trying to revoke
        4 consent, one for every status (PENDING, ACTIVE, REVOKED, NOT_VALID). It checks that only the one that was in
        PENDING status is returned and is in ACTIVE status
        """
        consents = {}
        statuses = [Consent.PENDING, Consent.ACTIVE, Consent.REVOKED, Consent.NOT_VALID]
        confirm_ids = []
        for i, s in enumerate(statuses):
            data = self.consent_data.copy()
            data['source'] = {
                'id': 'source_{}_id'.format(i),
                'name': 'source_{}_name'.format(i)
            }
            res = self._add_consent(data=json.dumps(data), status=s)
            consents[res.json()['confirm_id']] = {
                'start_validity': '2018-03-0{}T10:05:05.123000+02:00'.format(i + 1),
                'expire_validity': '2019-03-0{}T10:05:05.123000+02:00'.format(i + 1),
            }
            confirm_ids.append(res.json()['confirm_id'])

        self.client.login(username='duck', password='duck')

        data = {
            'consents': consents
        }
        res = self.client.post('/v1/consents/confirm/', data=json.dumps(data), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['confirmed']), 1)
        self.assertEqual(len(res.json()['failed']), 3)
        self.assertListEqual(sorted(res.json()['failed']), sorted(confirm_ids[1:]))
        statuses[0] = Consent.ACTIVE
        for i, confirm_id in enumerate(confirm_ids):
            c = ConfirmationCode.objects.get(code=confirm_id).consent
            self.assertEqual(c.status, statuses[i])

    def test_confirm_wrong_user(self):
        """
        Tests error when confirming a consent of another user
        """
        res = self._add_consent()
        confirm_id = res.json()['confirm_id']
        consent = {confirm_id: {}}

        self.client.login(username='paperone', password='paperone')
        res = self.client.post('/v1/consents/confirm/', data=json.dumps({'consents': consent}),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['confirmed']), 0)
        self.assertEqual(len(res.json()['failed']), 1)
        self.assertEqual(res.json()['failed'][0], confirm_id)
        c = ConfirmationCode.objects.get(code=confirm_id).consent
        self.assertEqual(c.status, Consent.PENDING)

    def test_confirm_confirm_id_not_valid(self):
        """
        Tests error when confirming a consent of and the confirmation code has expired
        """
        res = self._add_consent()
        confirm_id = res.json()['confirm_id']
        consent = {confirm_id: {}}

        c = ConfirmationCode.objects.get(code=confirm_id)
        c.validity = datetime.now() - timedelta(hours=10)
        self.client.login(username='paperone', password='paperone')
        res = self.client.post('/v1/consents/confirm/', data=json.dumps({'consents': consent}),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['confirmed']), 0)
        self.assertEqual(len(res.json()['failed']), 1)
        self.assertEqual(res.json()['failed'][0], confirm_id)
        c = ConfirmationCode.objects.get(code=confirm_id).consent
        self.assertEqual(c.status, Consent.PENDING)

    def test_confirm_unknown_consent(self):
        """
        Tests error when confirming an unknwown consent
        """
        confirm_id = 'unknown'
        consent = {confirm_id: {}}
        self.client.login(username='duck', password='duck')
        res = self.client.post('/v1/consents/confirm/', data=json.dumps({'consents': consent}),
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['confirmed']), 0)
        self.assertEqual(len(res.json()['failed']), 1)
        self.assertEqual(res.json()['failed'][0], confirm_id)
        self.assertRaises(Consent.DoesNotExist, Consent.objects.get, consent_id=confirm_id)

    def test_page_confirm_redirect_to_identity_provider(self):
        """
        Tests that confirm url is protected by login and redirects to the identity provider
        """
        res = self.client.get('/confirm_consents/')
        self.assertRedirects(res, '/saml2/login/?next=/confirm_consents/', fetch_redirect_response=False)

    def test_confirm_wrong_method(self):
        """
        That access with forbidden HTTP method to confirm url
        """
        for m in ('put', 'head', 'options', 'delete', 'trace'):
            met = getattr(self.client, m)
            res = met('/confirm_consents/')
            self.assertEqual(res.status_code, 405)

    def _gen_test_consents(self, null_dates=False):
        consents = {}
        for i in range(4):
            data = self.consent_data.copy()
            data['source'] = {
                'id': 'source_{}_id'.format(i),
                'name': 'source_{}_name'.format(i)
            }
            res = self._add_consent(data=json.dumps(data))

            if null_dates is False:
                consents[res.json()['confirm_id']] = {
                    'start_validity': '2018-10-0{}T10:05:05.123000+02:00'.format(i + 1),
                    'expire_validity': '2019-10-0{}T10:05:05.123000+02:00'.format(i + 1)
                }
            else:
                consents[res.json()['confirm_id']] = {
                    'start_validity': None,
                    'expire_validity': None
                }

        return consents

    def test_given_some_pending_consents_when_requesting_their_abortion_then_mark_them_as_not_valid(self):
        """
        Tests consent abortion
        """
        consents = self._gen_test_consents()

        self.client.login(username='duck', password='duck')
        data = {
            'consents': consents
        }
        # Here we abort the just-created consents
        res = self.client.post('/v1/consents/abort/', data=json.dumps(data), content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['aborted']), 4)
        self.assertEqual(len(res.json()['failed']), 0)
        for index, (confirm_id, consent_data) in enumerate(consents.items()):
            consent_obj = ConfirmationCode.objects.get(code=confirm_id).consent
            self.assertEqual(consent_obj.status, Consent.NOT_VALID)

    def test_given_valid_legal_notice_when_requesting_markdown_then_return_it(self):
        self.client.login(username='duck', password='duck')
        # Here we abort the just-created consents
        res = self.client.get('/v1/legal-notices/4', HTTP_ACCEPT='text/markdown, application/json')
        self.assertEqual(res.status_code, 200)
        # the expected comes from the testing fixture
        self.assertEqual(res.data, self.legal_notice)

    def test_given_valid_legal_notice_when_requesting_html_then_return_it(self):
        self.client.login(username='duck', password='duck')
        # Here we abort the just-created consents
        res = self.client.get('/v1/legal-notices/4', HTTP_ACCEPT='text/html, application/json')
        self.assertEqual(res.status_code, 200)
        # the expected comes from the testing fixture
        self.assertEqual(res.data, markdownify(self.legal_notice))

    def test_given_valid_legal_notice_when_requesting_json_then_return_406(self):
        self.client.login(username='duck', password='duck')
        # Here we abort the just-created consents
        res = self.client.get('/v1/legal-notices/4', HTTP_ACCEPT='application/json')
        self.assertEqual(res.status_code, 406)

    def test_given_not_existing_legal_notice_when_requesting_markdown_then_return_404(self):
        self.client.login(username='duck', password='duck')
        # Here we abort the just-created consents
        res = self.client.get('/v1/legal-notices/5', HTTP_ACCEPT='text/markdown, application/json')
        self.assertEqual(res.status_code, 404)

    def test_given_unauthorized_when_requesting_legal_notice_then_return_401(self):
        # Here we abort the just-created consents
        res = self.client.get('/v1/legal-notices/4', HTTP_ACCEPT='text/markdown, application/json')
        self.assertEqual(res.status_code, 401)
