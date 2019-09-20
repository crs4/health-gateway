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

from dateutil import parser
from django.db import DatabaseError, transaction

from hgw_backend.models import FailedConnector, Source
from hgw_backend.settings import KAFKA_CHANNEL_NOTIFICATION_TOPIC
from hgw_common.utils.management import ConsumerCommand

logger = logging.getLogger('hgw_backend.channel_consumer')

class ACTION:
    """
    The possible actions performed by the HGW Frontend
    """
    CREATED = 'CREATED'
    UPDATED = 'UPDATED'
    REVOKED = 'REVOKED'

class Command(ConsumerCommand):
    help = 'Launch a KafkaConsumer'
    def __init__(self, *args, **kwargs):
        self.client_id = 'channel_consumer'
        self.group_id = 'channel_consumer'
        self.topics = [KAFKA_CHANNEL_NOTIFICATION_TOPIC]
        self.retriable_failure_reason = (FailedConnector.DATABASE_ERROR, FailedConnector.SENDING_ERROR)
        super(Command, self).__init__(*args, **kwargs)

    def _store_failure(self, message, failure_reason):
        try:
            with transaction.atomic():
                FailedConnector.objects.create(message=json.dumps(message['data']), 
                    reason=failure_reason, retry=failure_reason in self.retriable_failure_reason)
        except Exception as e:
            logger.error('Failure saving message into database', message['id'])
            logger.error(e)

    def _check_message_structure(self, channel_data):
        required_keys = {'destination', 'person_id', 'channel_id', 'profile', 'start_validity', 'expire_validity'}
        channel_keys = set(channel_data.keys())
        if not required_keys <= channel_keys:
            logger.error('Cannot find %s attribute in the message', ', '.join(required_keys - channel_keys))
            return False
        if 'kafka_public_key' not in channel_data['destination']:
            logger.error('Cannot find kafka_public_key attribute in the message')
            return False
        return True

    def _check_date(self, date):
        if date is not None:
            try:
                return parser.parse(date).date().isoformat()
            except ValueError:
                logger.error('Wrong date format for date: %s', date)
                return False
        return None

    def _check_source(self, channel_data):
        try:
            source = Source.objects.get(source_id=channel_data['source_id'])
        except DatabaseError:
            logger.error('Error reading data from db')
            return None, FailedConnector.DATABASE_ERROR
        except Source.DoesNotExist:
            logger.error('Source with id %s was not found in the db', channel_data['source_id'])
            return None, FailedConnector.SOURCE_NOT_FOUND
        return source, None

    def _check_action(self, channel_data):
        return channel_data['action'] in (ACTION.CREATED, ACTION.UPDATED, ACTION.REVOKED)
        
    def handle_message(self, message):
        logger.info('Received message with id %s to create a connector', message['id'])

        if not message['success']:
            logger.error('Message was not json encoded', message['id'])
            self._store_failure(message, FailedConnector.JSON_DECODING)
            return

        channel_data = message['data']
        if not self._check_action(channel_data):
            self._store_failure(message, FailedConnector.WRONG_ACTION)
            return

        if not self._check_message_structure(channel_data):
            self._store_failure(message, FailedConnector.WRONG_MESSAGE_STRUCTURE)
            return

        start_date = self._check_date(channel_data['start_validity'])
        expire_date = self._check_date(channel_data['expire_validity'])
        if start_date is False or expire_date is False:
            self._store_failure(message, FailedConnector.WRONG_DATE_FORMAT)
            return

        source, failure_reason = self._check_source(channel_data)
        if failure_reason is not None:
            self._store_failure(message, failure_reason)
            return
        
        if channel_data['action'] == ACTION.CREATED:
            connector = {
                'profile': channel_data['profile'],
                'person_identifier': channel_data['person_id'],
                'dest_public_key': channel_data['destination']['kafka_public_key'],
                'channel_id': channel_data['channel_id'],
                'start_validity': start_date,
                'expire_validity': expire_date
            }
            met = 'create_connector'
        elif channel_data['action'] == ACTION.UPDATED:
            connector = {
                'channel_id': channel_data['channel_id'],
                'profile': channel_data['profile'],
                'start_validity': start_date,
                'expire_validity': expire_date
            }
            met = 'update_connector'
        elif channel_data['action'] == ACTION.REVOKED:
            connector = {
                'channel_id': channel_data['channel_id'],
            }
            met = 'delete_connector'
        
        if getattr(source, met)(connector) is None:
            logger.error('Error contacting the Source Endpoint', message['id'])
            self._store_failure(message, FailedConnector.SENDING_ERROR)
