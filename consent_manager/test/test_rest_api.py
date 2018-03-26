import json
import os

from django.test import TestCase, client

from consent_manager import ERRORS_MESSAGE
from consent_manager.models import Consent, ConfirmationCode, RESTClient
from hgw_common.utils import get_free_port

PORT = get_free_port()

BASE_DIR = os.path.dirname(__file__)
PERSON1_ID = 'SLSMLR56M13C354H'
PERSON2_ID = 'GVNFSL43S21H457H'


class TestAPI(TestCase):
    fixtures = ['test_data.json']

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
            'start_validity': '2017-10-23T10:00:00.000Z',
            'expire_validity': '2018-10-23T10:00:00.000Z'
        }

        self.json_consent_data = json.dumps(self.consent_data)

    def _get_client_data(self, client_index=0):
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
                    'expire_validity': '2018-10-23T10:00:00Z',
                    'start_validity': '2017-10-23T10:00:00Z',
                    'source': {
                        'id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                        'name': 'SOURCE_1'
                    }}

        headers = self._get_oauth_header(client_index=2)
        res = self.client.get('/v1/consents/', **headers)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(res.json()), 1)
        self.assertListEqual(res.json(), [expected])

        res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
        self.assertEquals(res.status_code, 200)
        self.assertDictEqual(res.json(), expected)

    def test_get_consents_by_super_client(self):
        """
        Tests get functionality when the restclient is a super client
        """
        expected = {
            'status': 'PE',
            'start_validity': '2017-10-23T10:00:00Z',
            'expire_validity': '2018-10-23T10:00:00Z',
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
            'source': {
                'id': 'iWWjKVje7Ss3M45oTNUpRV59ovVpl3xT',
                'name': 'SOURCE_1'
            }
        }

        headers = self._get_oauth_header(client_index=1)
        res = self.client.get('/v1/consents/', **headers)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(res.json()), 1)
        self.assertListEqual(res.json(), [expected])

        res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
        self.assertEquals(res.status_code, 200)
        self.assertDictEqual(res.json(), expected)

    def test_get_consent_not_found(self):
        """
        Tests not found consent
        :return:
        """
        headers = self._get_oauth_header()
        res = self.client.get('/v1/consents/unknown/', **headers)
        self.assertEquals(res.status_code, 404)
        self.assertEquals(res.json(), {'detail': 'Not found.'})

    def get_consent_forbidden(self):
        headers = self._get_oauth_header(client_index=3)
        res = self.client.get('/v1/consents/', **headers)
        self.assertEquals(res.status_code, 403)

        res = self.client.get('/v1/consents/q18r2rpd1wUqQjAZPhh24zcN9KCePRyr/', **headers)
        self.assertEquals(res.status_code, 403)

    def _add_consent(self, data=None, client_index=0):
        headers = self._get_oauth_header(client_index)
        data = data or self.json_consent_data
        return self.client.post('/v1/consents/', data=data,
                                content_type='application/json', **headers)

    def test_add_consent(self):
        """
        Test correct add consent
        """
        res = self._add_consent()
        self.assertEquals(res.status_code, 201)
        self.assertEquals(set(res.json().keys()), {'consent_id', 'confirm_id'})

    def test_add_consent_forbidden(self):
        """
        Test add consent is forbidden when it is missing the correct scopes
        """
        res = self._add_consent(client_index=2)
        self.assertEquals(res.status_code, 403)

    def test_add_consent_too_long_fields(self):
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
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.json(), expected)

    def test_add_consent_duplicated_endpoint(self):
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
            'source': {'non_field_errors': ['An instance with the same name and different id already exists']},
            'destination': {'non_field_errors': ['An instance with the same name and different id already exists']}
        }

        self.assertEquals(res.status_code, 400)
        self.assertDictEqual(res.json(), expected)

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
            'source': {'non_field_errors': ['An instance with the same id and different name already exists']},
            'destination': {'non_field_errors': ['An instance with the same id and different name already exists']}
        }

        self.assertEquals(res.status_code, 400)
        self.assertDictEqual(res.json(), expected)

    def test_add_consent_missing_fields(self):
        """
        Test error when adding consent and some fields are missing
        """
        headers = self._get_oauth_header()

        # Missing data
        res = self.client.post('/v1/consents/', data='{}', content_type='application/json', **headers)
        self.assertEquals(res.status_code, 400)
        expected = {'source': ['This field is required.'],
                    'profile': ['This field is required.'],
                    'person_id': ['This field is required.'],
                    'destination': ['This field is required.'],
                    'start_validity': ['This field is required.'],
                    'expire_validity': ['This field is required.']
                    }
        self.assertDictEqual(res.json(), expected)

    def test_add_consent_empty_fields(self):
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

        self.assertEquals(res.status_code, 400)
        self.assertDictEqual(res.json(), expected)

    def test_add_consent_none_fields(self):
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
                    'person_id': ['This field may not be null.'],
                    'start_validity': ['This field may not be null.'],
                    'expire_validity': ['This field may not be null.']
                    }

        self.assertEquals(res.status_code, 400)
        self.assertDictEqual(res.json(), expected)

    def test_add_duplicated_consent_when_not_active(self):
        """
        Tests that when adding a consent and there are already other consent
        the Consent is actually added and the old one in PENDING status is set to NOT_VALID status
        """
        # First we add one REVOKED and one NOT_VALID consents
        for status in (Consent.REVOKED, Consent.NOT_VALID):
            res = self._add_consent(self.json_consent_data)
            c = Consent.objects.get(consent_id=res.json()['consent_id'])
            c.status = status
            c.save()
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
        res = self._add_consent(self.json_consent_data)
        # Manually changing it to ACTIVE
        c = Consent.objects.get(consent_id=res.json()['consent_id'])
        c.status = Consent.ACTIVE
        c.save()
        res = self._add_consent(self.json_consent_data)
        expected = {'non_field_errors': ['Consent already present']}
        self.assertEquals(res.status_code, 400)
        self.assertDictEqual(res.json(), expected)

    def test_revoke_consent(self):
        """
        Tests consents revocation
        """
        res = self._add_consent()
        # Manually changing it to ACTIVE
        c = Consent.objects.get(consent_id=res.json()['consent_id'])
        c.status = Consent.ACTIVE
        c.save()

        self.client.login(username='duck', password='duck')
        data = {
            'revoke_list': [c.id]
        }
        res = self.client.post('/consents/revoke/', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(c.source.name, res.content.decode('utf-8'))
        self.assertIn(c.destination.name, res.content.decode('utf-8'))

    def test_revoke_consent_wrong_status(self):
        """
        Tests consents revocation fail if the consent was in PENDING status
        """
        for status in (Consent.PENDING, Consent.REVOKED, Consent.NOT_VALID):
            res = self._add_consent(self.json_consent_data)
            consent_id = res.json()['consent_id']
            c = Consent.objects.get(consent_id=consent_id)
            c.status = status
            c.save()

            self.client.login(username='duck', password='duck')
            data = {
                'revoke_list': [c.id]
            }
            res = self.client.post('/consents/revoke/', data=data)
            self.assertEqual(res.status_code, 200)
            c = Consent.objects.get(consent_id=consent_id)
            self.assertEqual(c.status, status)
            c.delete()

    def test_revoke_consent_wrong_user(self):
        """
        Tests consents revocation when the logged user is not the owner of the consent
        """
        res = self._add_consent(self.json_consent_data)
        # Manually changing it to ACTIVE
        c = Consent.objects.get(consent_id=res.json()['consent_id'])
        c.status = Consent.ACTIVE
        c.save()

        self.client.login(username='paperone', password='paperone')
        data = {
            'revoke_list': [c.id]
        }
        res = self.client.post('/consents/revoke/', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(c.source.name, res.content.decode('utf-8'))
        self.assertNotIn(c.destination.name, res.content.decode('utf-8'))

    def test_confirm_redirect_to_identity_provider(self):
        """
        Tests that confirm url is protected by login and redirects to the identity provider
        """
        res = self.client.get('/v1/consents/confirm/')
        self.assertRedirects(res, '/saml2/login/?next=/v1/consents/confirm/', fetch_redirect_response=False)

    def test_confirm_wrong_method(self):
        """
        That access with forbidden HTTP method to confirm url
        """
        for m in ('put', 'head', 'options', 'delete', 'trace'):
            met = getattr(self.client, m)
            res = met('/v1/consents/confirm/')
            self.assertEquals(res.status_code, 405)

    def test_confirm_missing_parameters(self):
        """
        Tests missing parameters when confirming consent
        """
        res = self._add_consent()
        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/confirm/')
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

        res = self.client.get('/v1/consents/confirm/?confirm_id={}'.format(confirm_id))
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

        res = self.client.get('/v1/consents/confirm/?callback_url={}'.format(callback_url))
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.content.decode('utf-8'), ERRORS_MESSAGE['MISSING_PARAM'])

    def test_confirm_invalid_confirmation_code(self):
        """
        Tests error when sending an invalid confirmation code
        """
        headers = self._get_oauth_header()

        # using delete but it doesn't matter if it's delete or add
        self.client.delete('/v1/flow_requests/54321/', **headers)
        callback_url = 'http://127.0.0.1/'
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/confirm/?confirm_id={}&callback_url={}'.format('invalid', callback_url))
        self.assertEquals(res.status_code, 400)
        self.assertEquals(res.content.decode('utf-8'), ERRORS_MESSAGE['INVALID_CONFIRMATION_CODE'])

    def test_confirm_wrong_consent_state(self):
        """
        Tests error when confirming a consent in the wrong state
        """
        consent = Consent.objects.get(pk=1)
        consent.status = Consent.ACTIVE
        consent.save()

        cc = ConfirmationCode.objects.create(consent=consent)
        cc.save()

        callback_url = 'http://127.0.0.1/'
        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/confirm/?confirm_id={}&callback_url={}'.format(cc.code, callback_url))

        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(res.context['errors']), 1)

    def test_confirm_valid(self):
        """
        Tests the valid confirmation. First, the user calls the confirmation page and gets an html page
        with the form that shows all the consents. Then it posts the form and the consent is set to active.
        """
        res = self._add_consent()

        confirm_id = res.json()['confirm_id']
        callback_url = 'http://127.0.0.1/'

        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/confirm/?confirm_id={}&callback_url={}'.format(confirm_id, callback_url))
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'text/html; charset=utf-8')
        cc = ConfirmationCode.objects.get(code=confirm_id)
        consent = cc.consent
        self.assertEquals(consent.status, Consent.PENDING)
        self.assertIsNone(consent.confirmed)
        post_data = {
            'csrf_token': res.context['csrf_token'],
            'confirm_id': res.context['consents'][0]['confirm_id'],
            'callback_url': res.context['callback_url']
        }
        res = self.client.post('/v1/consents/confirm/?confirm_id={}&callback_url={}'.format(confirm_id, callback_url),
                               post_data)
        self.assertRedirects(res, '{}?success=true&consent_confirm_id={}'.format(callback_url, confirm_id),
                             fetch_redirect_response=False)
        consent.refresh_from_db()
        self.assertEquals(consent.status, Consent.ACTIVE)
        self.assertIsNotNone(consent.confirmed)

    def test_two_consents_confirm_valid(self):
        """
        Tests the valid confirmation for two consents.
        """
        consent_data = [
            self.consent_data,
            {
                'source': {
                    'id': '1',
                    'name': 'SECOND SOURCE'
                },
                'destination': {
                    'id': 'vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj',
                    'name': 'DEST_MOCKUP'
                },
                'profile': self.profile,
                'person_id': PERSON1_ID,
                'start_validity': '2017-10-23T10:00:00.000Z',
                'expire_validity': '2018-04-23T10:00:00.000Z'
            }
        ]
        confirm_ids = []

        for data in consent_data:
            res = self._add_consent(json.dumps(data))
            confirm_ids.append(res.json()['confirm_id'])

        callback_url = 'http://127.0.0.1/'

        self.client.login(username='duck', password='duck')
        res = self.client.get('/v1/consents/confirm/?{}&callback_url={}'.format(
            '&'.join(['confirm_id={}'.format(confirm_id) for confirm_id in confirm_ids]),
            callback_url))

        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'text/html; charset=utf-8')

        context = res.context
        self.assertEquals(len(context['consents']), 2)
        self.assertEquals(len(context['errors']), 0)

        context = res.context
        for confirm_id in confirm_ids:
            cc = ConfirmationCode.objects.get(code=confirm_id)
            consent = cc.consent
            self.assertEquals(consent.status, Consent.PENDING)
            post_data = {
                'csrf_token': context['csrf_token'],
                'confirm_id': confirm_id,
                'callback_url': context['callback_url']
            }
            res = self.client.post('/v1/consents/confirm/',
                                   post_data)
            self.assertRedirects(res, '{}?success=true&consent_confirm_id={}'.format(callback_url, confirm_id),
                                 fetch_redirect_response=False)
            consent.refresh_from_db()
            self.assertEquals(consent.status, Consent.ACTIVE)
