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


import base64
import json
import os
import time
import uuid

import requests
from Cryptodome.PublicKey import RSA
from django.core.management.base import BaseCommand

from destination_mockup import settings
from hgw_common.cipher import Cipher
from hgw_common.utils import get_logger

MAGIC_BYTES = '\xdf\xbb'


logger = get_logger('rest_consumer')


class Command(BaseCommand):
    PRI_RSA_KEY_PATH = os.path.join(settings.BASE_DIR, 'certs/kafka/payload_encryption/private_key.pem')

    help = 'Launch the kafka consumer '

    def __init__(self):
        with open(self.PRI_RSA_KEY_PATH, 'r') as f:
            self.rsa_pri_key = RSA.importKey(f.read())
            self.cipher = Cipher(private_key=self.rsa_pri_key)
        super(Command, self).__init__()

    def _handle_payload(self, data, *args, **options):
        docs = json.loads(data)
        logger.info('\nFound documents for {} person(s)'.format(len(docs)))

        unique_filename = str(uuid.uuid4())
        try:
            os.mkdir('/tmp/msgs/')
        except OSError:
            pass
        with open('/tmp/msgs/{}'.format(unique_filename), 'w') as f:
            f.write(data)

    def handle(self, *args, **options):
        params = {
            'grant_type': 'client_credentials',
            'client_id': settings.OAUTH_CLIENT_ID,
            'client_secret': settings.OAUTH_CLIENT_SECRET
        }
        res = requests.post('{}/oauth2/token/'.format(settings.HGW_FRONTEND_URI), data=params)
        access_token = res.json()['access_token']
        header = {"Authorization": "Bearer {}".format(access_token)}
        first_id = None
        while first_id is None:
            try:
                info = requests.get('{}/v1/messages/info/'.format(settings.HGW_FRONTEND_URI), headers=header)
                first_id = info.json()['start_id']
            except ValueError:
                pass
        current_id = first_id
        while True:
            msg = requests.get('{}/v1/messages/{}/'.format(settings.HGW_FRONTEND_URI, current_id), headers=header)
            if msg.status_code == 200:
                try:
                    res = msg.json()
                    logger.info("Received message with key {} and id {}".format(res['process_id'], res['message_id']))
                    message = base64.b64decode(res['data'])
                    current_id += 1
                    time.sleep(2)
                    if self.cipher.is_encrypted(message):
                        self._handle_payload(self.cipher.decrypt(message), *args, **options)
                    else:
                        self._handle_payload(message, *args, **options)
                except ValueError as e:
                    logger.info("Error")
            elif msg.status_code == 404:
                logger.info("No message. Retrying in 6 seconds")
                time.sleep(6)
            else:
                logger.info("Error: {}".format(msg.content))
