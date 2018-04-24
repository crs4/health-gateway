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
import django
import os
from Cryptodome.PublicKey import RSA

os.environ['DJANGO_SETTINGS_MODULE'] = 'source_endpoint.settings'
django.setup()

import source_endpoint.settings as settings
from source_endpoint.models import Connector
from kafka import KafkaProducer
from hgw_common.cipher import Cipher


class UnsupportedResource(Exception):
    def cipher(self, data):
        pass


class BasePublisher(object):
    def __init__(self,
                 bootstrap_servers=settings.KAFKA_BROKER,
                 security_protocol='SSL',
                 ssl_check_hostname=True,
                 ssl_cafile=settings.KAFKA_CA_CERT,
                 ssl_certfile=settings.KAFKA_CLIENT_CERT,
                 ssl_keyfile=settings.KAFKA_CLIENT_KEY):

        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                                      security_protocol=security_protocol,
                                      ssl_check_hostname=ssl_check_hostname,
                                      ssl_cafile=ssl_cafile,
                                      ssl_certfile=ssl_certfile,
                                      ssl_keyfile=ssl_keyfile)

        self.ciphers = {}

    def publish(self, data):
        raise NotImplementedError()


class NoConnectorAvailable(Exception):
    pass


class FHIRBasePublisher(BasePublisher):
    def publish(self, data, cipher=None):
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
                    value = value.encode()
                print('sending data to ', settings.SOURCE_ID)
                print(len(value))
                self.producer.send(settings.SOURCE_ID, key=connector.channel_id.encode(), value=value)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Tool for publishing data. Supported formats by now: fhir-json")
    parser.add_argument('input', help='Data to input: can be a single file or a directory')
    parser.add_argument('-c', dest='cipher', action='store_true', help='Enable encrypting')

    args = parser.parse_args()
    publisher = FHIRBasePublisher()

    if os.path.isdir(args.input):
        for f in os.listdir(args.input):
            file_path = os.path.join(args.input, f)
            if os.path.isfile(file_path):
                publisher.publish(json.load(open(file_path)), args.cipher)
    else:
        publisher.publish(json.load(open(args.input)), args.cipher)

    publisher.producer.close()
    print('DONE')
