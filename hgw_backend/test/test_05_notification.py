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

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from mock.mock import patch

from hgw_backend.models import Source
from hgw_backend.serializers import SourceSerializer
from hgw_backend.settings import KAFKA_SOURCE_NOTIFICATION_TOPIC
from hgw_common.models import Profile

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class TestNotification(TestCase):
    
    @classmethod
    def setUpClass(cls):
        for logger_name in ('backend_kafka_consumer', 'hgw_backend'):
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.CRITICAL)
        return super(TestNotification, cls).setUpClass()

    def setUp(self):
        new_profile_data = {
            "code": "PROF_003",
            "version": "v0",
            "payload": "[{\"clinical_domain\": \"Anatomical pathology\"}]"
        }
        self.profile = Profile.objects.create(**new_profile_data)
        self.new_source_data = {
            "source_id": "fXSMECPXjKxRKFUaFLS6ioBjSX2Nmyyk",
            "name": "source_3",
            "url": "http://localhost:30000/v1/connectors/",
            "profile": self.profile,
            "content_type": ContentType.objects.get(app_label="hgw_backend", model="certificatesauthentication"),
            "object_id": 1
        }

    def test_notification_adding_source(self):
        """
        Test that, when a new Source is created, it is notified to kafka
        """
        with patch('hgw_common.notifier.KafkaProducer') as MockKafkaProducer:
            source = Source.objects.create(**self.new_source_data)
            MockKafkaProducer().send.assert_called_once()
            serializer = SourceSerializer(source)
            source_data = {k: serializer.data[k] for k in ('source_id', 'name', 'profile')}
            self.assertEqual(MockKafkaProducer().send.call_args_list[0][0][0], KAFKA_SOURCE_NOTIFICATION_TOPIC)
            self.assertEqual(json.loads(MockKafkaProducer().send.call_args_list[0][1]['value'].decode('utf-8')), source_data)
    