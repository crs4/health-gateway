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

from hgw_backend.models import FailedConnector, Source
from hgw_common.utils import KafkaConsumerCommand, get_logger

logger = get_logger('backend_kafka_consumer')


class Command(KafkaConsumerCommand):
    help = 'Launch a KafkaConsumer'
    def __init__(self, *args, **kwargs):
        self.client_id = 'create_connector_consumer'
        self.group_id = 'create_connector_consumer'
        self.topics = [settings.KAFKA_TOPIC]
        super(Command, self).__init__(*args, **kwargs)

    def handle_message(self, message):
        failure_reason = None
        retry = False
        try:
            # Loads the json message
            channel_data = json.loads(message.value.decode('utf-8'))
        except (TypeError, UnicodeError):
            failure_reason = FailedConnector.DECODING
            logger.error('Skipping message with id %s: something bad happened', message.offset)
        except JSONDecodeError:
            failure_reason = FailedConnector.JSON_DECODING
            logger.error('Skipping message with id %s: message was not json encoded', message.offset)
        else:
            try:
                # Then get the source data
                source = Source.objects.get(source_id=channel_data['source_id'])
            except Source.DoesNotExist:
                failure_reason = FailedConnector.SOURCE_NOT_FOUND
                logger.error('Skipping message with id %s: source with id %s was not found in the db', message.offset, channel_data['source_id'])
            else:
                try:
                    # Then get the key from the structure
                    destination_kafka_key = channel_data['destination']['kafka_public_key']
                    person_id = channel_data['person_id']
                    channel_id = channel_data['channel_id']
                    source_endpoint_profile = channel_data['profile']
                    start_channel_validity = channel_data['start_validity']
                    end_channel_validity = channel_data['expire_validity']
                except KeyError as k:
                    failure_reason = FailedConnector.WRONG_MESSAGE_STRUCTURE
                    logger.error('Skipping message with id %s: cannot find %s attribute in the message', message.offset, k.args[0])
                else:
                    if start_channel_validity is not None:
                        try:
                            start_channel_validity = parser.parse(channel_data['start_validity']).date().isoformat()
                        except ValueError:
                            failure_reason = FailedConnector.WRONG_DATE_FORMAT
                            logger.error('Skipping message with id %s: wrong start date format', message.offset)

                    if end_channel_validity is not None:
                        try:
                            end_channel_validity = parser.parse(channel_data['expire_validity']).date().isoformat()
                        except ValueError:
                            failure_reason = FailedConnector.WRONG_DATE_FORMAT
                            logger.error('Skipping message with id %s: wrong end date format', message.offset)

                    connector = {
                        'profile': source_endpoint_profile,
                        'person_identifier': person_id,
                        'dest_public_key': destination_kafka_key,
                        'channel_id': channel_id,
                        'start_validity': start_channel_validity,
                        'end_validity': end_channel_validity
                    }
                    logger.info("Consumed connector with data %s", connector)
                    res = source.create_connector(connector)
                    if res is None:
                        failure_reason = FailedConnector.SENDING_ERROR
                        retry = True
                        logger.error('Skipping message with id %s: error ontacting the Source Endpoint', message.offset)

        if failure_reason is not None:
            try:
                with transaction.atomic():
                    FailedConnector.objects.create(message=message.value, reason=failure_reason, retry=retry)
            except:
                logger.error('Failure saving message with id %s into database', message.offset)
