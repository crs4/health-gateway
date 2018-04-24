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

import requests
from Cryptodome.PublicKey import RSA
from django.core.management.base import BaseCommand
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from hgw_common.cipher import Cipher, MAGIC_BYTES
from source_endpoint.models import Connector
from source_endpoint.settings import HGW_BACKEND_URI, HGW_BACKEND_CLIENT_ID, HGW_BACKEND_CLIENT_SECRET


class UnsupportedResource(Exception):
    def cipher(self, data):
        pass


class NoConnectorAvailable(Exception):
    pass


class Command(BaseCommand):
    help = 'Publish data to the hgw_backend'

    def __init__(self, *args, **kwargs):
        self.ciphers = {}
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('input', help='Data to input: can be a single file or a directory')
        parser.add_argument('-c', dest='cipher', action='store_true', help='Enable encrypting')

    def _load_data(self, data):
        if os.path.isdir(data):
            for f in os.listdir(data):
                file_path = os.path.join(data, f)
                if os.path.isfile(file_path):
                    return json.load(open(file_path))
        else:
            return json.load(open(data))

    def _fetch_token(self, oauth_session):
        oauth_session.fetch_token(token_url='{}/oauth2/token/'.format(HGW_BACKEND_URI),
                                  client_id=HGW_BACKEND_CLIENT_ID,
                                  client_secret=HGW_BACKEND_CLIENT_SECRET)

    def _get_oauth2_session(self):
        client = BackendApplicationClient(HGW_BACKEND_CLIENT_ID)
        oauth_session = OAuth2Session(client=client)
        self._fetch_token(oauth_session)
        return oauth_session

    def handle(self, *args, **options):
        data = self._load_data(options['input'])
        cipher = options['cipher']

        resource_type = data['resourceType']
        if resource_type != 'Observation':
            raise UnsupportedResource('{} is not supported'.format(resource_type))

        person_id = data['subject']['reference'].split('/')[-1]
        connectors = Connector.objects.filter(person_identifier=person_id)
        print("Connector.objects.all().count()", Connector.objects.all().count())
        if connectors.count() < 1:
            raise NoConnectorAvailable('No connector for person_id = {}'.format(person_id))

        for connector in connectors:
            if person_id == connector.person_identifier:
                value = json.dumps(data)
                if cipher:
                    if connector.channel_id not in self.ciphers:
                        self.ciphers[connector.channel_id] = Cipher(
                            public_key=RSA.importKey(connector.dest_public_key)
                        )
                    value = self.ciphers[connector.channel_id].encrypt(value)
                else:
                    value = '{}{}'.format(MAGIC_BYTES.decode('utf-8'), value)
                session = self._get_oauth2_session()
                channel_id = {
                    'channel_id': connector.channel_id
                }
                message = {
                    'payload': value
                }
                headers = {
                    'Authorization': 'Bearer {}'.format(session.token['access_token']),
                }

                res = requests.post("{}/v1/messages/".format(HGW_BACKEND_URI),
                                    data=channel_id, files=message, headers=headers)
                if res.status_code == 200:
                    print('sent correctly')
                else:
                    print("Error occurred")