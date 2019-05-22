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

from django.conf import settings
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer, TopicPartition

from hgw_common.utils import KafkaConsumerCommand, get_logger
from hgw_frontend.models import Source
from hgw_frontend.serializers import SourceSerializer

logger = get_logger('backend_notification_consumer')


class Command(KafkaConsumerCommand):
    help = 'Launch Backend Notification Consumer'

    def __init__(self, *args, **kwargs):
        self.client_id = 'backend_notification_consumer'
        self.group_id = 'backend_notification_consumer'
        self.topics = [settings.KAFKA_SOURCE_NOTIFICATION_TOPIC]
        super(Command, self).__init__(*args, **kwargs)

    def handle_message(self, message):
        logger.info('Found message')
        try:
            source_data = json.loads(message.value.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error('Cannot add Source. JSON Error')
        else:
            try:
                data = {key: source_data[key] for key in ['source_id', 'name', 'profile']}
            except KeyError:
                logger.error('Cannot find some source information in the message')
            else:
                try:
                    source = Source.objects.get(source_id=data['source_id'])
                except Source.DoesNotExist:
                    logger.info('Inserting new source with id %s', data['source_id'])
                    source_serializer = SourceSerializer(data=data)
                else:
                    logger.info('Updating new source with id %s', data['source_id'])
                    source_serializer = SourceSerializer(source, data=data)                        
                if source_serializer.is_valid():
                    source_serializer.save()
