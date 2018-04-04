import json
import os
import sys

from django.test import TestCase, client
from mock import patch

from hgw_backend.models import OAuth2Authentication
from hgw_common.utils import start_mock_server
from test.utils import MockKafkaConsumer, MockKafkaConsumerOAuth2Messages, MockSourceEnpointHandler

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CERT_SOURCE_PORT = 40000
OAUTH_SOURCE_PORT = 40001

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/management/')))

from commands.kafka_consumer import Command


class TestHGWBackendAPI(TestCase):
    fixtures = ['test_data.json']

    @classmethod
    def setUpClass(cls):
        super(TestHGWBackendAPI, cls).setUpClass()
        start_mock_server('certs', MockSourceEnpointHandler, OAUTH_SOURCE_PORT)
        start_mock_server('certs', MockSourceEnpointHandler, CERT_SOURCE_PORT)

    def setUp(self):
        self.messages_source_oauth = []
        self.client = client.Client()
        payload = [{'clinical_domain': 'Laboratory',
                    'filters': [{'includes': 'immunochemistry', 'excludes': 'HDL'}]},
                   {'clinical_domain': 'Radiology',
                    'filters': [{'includes': 'Tomography', 'excludes': 'Radiology'}]},
                   {'clinical_domain': 'Emergency',
                    'filters': [{'includes': '', 'excludes': ''}]},
                   {'clinical_domain': 'Prescription',
                    'filters': [{'includes': '', 'excludes': ''}]}]
        self.profile_data = {
            'code': 'PROF002',
            'version': 'hgw.document.profile.v0',
            'start_time_validity': '2017-06-23T10:13:39Z',
            'end_time_validity': '2018-06-23T23:59:59Z',
            'payload': json.dumps(payload)
        }
        with open(os.path.abspath(os.path.join(BASE_DIR, '../hgw_backend/fixtures/test_data.json'))) as fixtures_file:
            self.fixtures = json.load(fixtures_file)

    def test_get_sources(self):
        res = self.client.get('/v1/sources/')
        json_res = json.loads(res.content.decode())
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'application/json')
        self.assertEquals(len(json_res), 2)

    def test_add_connector(self):
        with open(os.path.join(os.path.dirname(__file__), './channels_data.json')) as cd:
            messages = json.load(cd)
        with patch('commands.kafka_consumer.KafkaConsumer', MockKafkaConsumer):
            MockKafkaConsumer.MESSAGES = messages
            self.assertIsNone(OAuth2Authentication.objects.get().token)
            res = Command().handle()
            self.assertIsNotNone(OAuth2Authentication.objects.get().token)


