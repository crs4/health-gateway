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


import uuid

from destination_mockup.management.commands.kafka_consumer import Command as DestinationMockupConsumerCommand
import requests
import json
import os
from django.conf import settings


class Command(DestinationMockupConsumerCommand):
    PRI_RSA_KEY_PATH = os.path.join(settings.BASE_DIR, 'certs/kafka/payload_encryption/private_key.pem')

    def add_arguments(self, parser):
        parser.add_argument('--fhir_address', type=str, default='https://i2b2-fhir:8181')
        parser.add_argument('--user', type=str, default='i2b2')
        parser.add_argument('--pwd', type=str, default='demouser')

    def _handle_payload(self, data, *args, **options):
        fhir_address = options['fhir_address']
        json_data = json.loads(data)
        print(json_data)
        unique_filename = str(uuid.uuid4())
        try:
            os.mkdir('/tmp/msgs/')
        except OSError:
            pass
        with open('/tmp/msgs/{}'.format(unique_filename), 'w') as f:
            f.write(data)


        # r = requests.post(
        #     '{}/fhir-i2b2/1.0.2/fhir/Observation'.format(fhir_address),
        #     json=json_data,
        #     verify=False,
        #     headers={
        #         'Accept': 'application/json',
        #         'Content-Type': 'application/json',
        #         'Authentication': '{}:{}'.format(options['user'], options['pwd'])}
        # )
        # if not r.ok:
        #     print ('Error with message: {}\n status code {}, reason {}').format(data, r.status_code, r.content)
