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

from django.conf import settings
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer, TopicPartition

from hgw_backend.models import Source


class Command(BaseCommand):
    help = 'Launch a KafkaConsumer'

    def handle(self, *args, **options):
        kc = KafkaConsumer(bootstrap_servers=settings.KAFKA_BROKER,
                           security_protocol='SSL',
                           ssl_check_hostname=True,
                           ssl_cafile=settings.KAFKA_CA_CERT,
                           ssl_certfile=settings.KAFKA_CLIENT_CERT,
                           ssl_keyfile=settings.KAFKA_CLIENT_KEY)

        kc.assign([TopicPartition(settings.KAFKA_TOPIC, 0)])
        kc.seek_to_beginning(TopicPartition(settings.KAFKA_TOPIC, 0))
        for msg in kc:
            try:
                channel_data = json.loads(msg.value.decode('utf-8'))
                source = Source.objects.get(source_id=channel_data['source_id'])
                destination_kafka_key = channel_data['destination']['kafka_public_key']
                person_id = channel_data['person_id']
                channel_id = channel_data['channel_id']
                source_endpoint_profile = channel_data['profile']
                connector = {
                    'profile': source_endpoint_profile,
                    'person_identifier': person_id,
                    'dest_public_key': destination_kafka_key,
                    'channel_id': channel_id
                }

                res = source.create_connector(connector)
            except Exception as ex:
                logging.error('error processing msg %s', msg)
                logging.exception(ex)
