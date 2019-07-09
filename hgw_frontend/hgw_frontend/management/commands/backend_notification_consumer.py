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

from django.conf import settings

from hgw_common.utils import get_logger
from hgw_common.utils.management import ConsumerCommand

from hgw_frontend.models import Channel, ConsentConfirmation, Source
from hgw_frontend.serializers import SourceSerializer
from hgw_frontend.settings import (KAFKA_CONNECTOR_NOTIFICATION_TOPIC,
                                   KAFKA_SOURCE_NOTIFICATION_TOPIC)

logger = get_logger('backend_notification_consumer')


class Command(ConsumerCommand):
    help = 'Launch Backend Notification Consumer'

    def __init__(self, *args, **kwargs):
        self.client_id = 'backend_notification_consumer'
        self.group_id = 'backend_notification_consumer'
        self.topics = [KAFKA_SOURCE_NOTIFICATION_TOPIC,
                       KAFKA_CONNECTOR_NOTIFICATION_TOPIC]
        super(Command, self).__init__(*args, **kwargs)

    def handle_message(self, message):
        logger.info('Found message for topic %s', message['queue'])
        if not message['success']:
            logger.error("Errore reading the message")
        else:
            if message['queue'] == settings.KAFKA_SOURCE_NOTIFICATION_TOPIC:
                return self._handle_source(message['data'])
            else:
                return self._handle_connector(message['data'])

    def _handle_source(self, source_data):
        try:
            data = {key: source_data[key] for key in ['source_id', 'name', 'profile']}
        except (KeyError, TypeError):
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
                return True
        return False

    def _handle_connector(self, connector_data):
        try:
            consent_id = connector_data['channel_id']
        except (KeyError, TypeError):
            logger.error('Cannot find some consent information in the message')
        else:
            try:
                consent_confirmation = ConsentConfirmation.objects.get(consent_id=consent_id)
            except ConsentConfirmation.DoesNotExist:
                logger.error('The consent was not found')
            else:
                channel = consent_confirmation.channel
                if channel.status != Channel.WAITING_SOURCE_NOTIFICATION:
                    logger.critical('Received channel confirmation from source for a channel'
                                    'not in WAITING_SOURCE_NOTIFICATION status. Channel id is %s', channel.channel_id)
                else:
                    logger.info('Changing Channel status to ACTIVE for channel with id %s', channel.channel_id)
                    channel.status = Channel.ACTIVE
                    channel.save()
                    return True
        return False
