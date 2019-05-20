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
from datetime import datetime
from json import JSONDecodeError

from dateutil import parser
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from kafka import KafkaConsumer, TopicPartition

from hgw_common.utils import get_logger
from hgw_frontend.models import Source
from hgw_frontend.serializers import SourceSerializer

logger = get_logger('backend_notification_consumer')


class Command(BaseCommand):
    help = 'Launch Backend Notification Consumer'

    def handle(self, *args, **options):
        consumer_params = {
            'bootstrap_servers': settings.KAFKA_BROKER
        }
        if settings.KAFKA_SSL:
            consumer_params.update({
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': settings.KAFKA_CA_CERT,
                'ssl_certfile': settings.KAFKA_CLIENT_CERT,
                'ssl_keyfile': settings.KAFKA_CLIENT_KEY
            })

        consumer = KafkaConsumer(**consumer_params)
        consumer.assign([TopicPartition(settings.KAFKA_SOURCE_NOTIFICATION_TOPIC, 0)])
        # consumer.assign([TopicPartition(settings.KAFKA_CONNECTOR_NOTIFICATION_TOPIC, 0)])
        # consumer.seek_to_beginning(TopicPartition(settings.KAFKA_TOPIC, 0))
        
        logger.info("Start consuming messages from Backend")
        for msg in consumer:
            logger.info("Found message")
            try:
                source_data = json.loads(msg.value.decode('utf-8'))
            except JSONDecodeError:
                logger.error("Cannot add Source. JSON Error")
            else:
                try:
                    data = {key: source_data[key] for key in ['source_id', 'name', 'profile']}
                except KeyError:
                    logger.error("Cannot find some source information in the message")
                else:
                    try:
                        source = Source.objects.get(source_id=data['source_id'])
                    except Source.DoesNotExist:
                        logger.info("Inserting new source with id %s", data['source_id'])
                        source_serializer = SourceSerializer(data=data)
                    else:
                        logger.info("Updating new source with id %s", data['source_id'])
                        source_serializer = SourceSerializer(source, data=data)                        
                    if source_serializer.is_valid():
                        source_serializer.save()
