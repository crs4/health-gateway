import json
import os

from django.test import TestCase, client

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class TestAPI(TestCase):

    fixtures = ['test_data.json']

    def setUp(self):
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

    def test_get_sources(self):
        res = self.client.get('/v1/sources/')
        json_res = json.loads(res.content.decode())
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res['Content-Type'], 'application/json')
        self.assertEquals(len(json_res), 1)
