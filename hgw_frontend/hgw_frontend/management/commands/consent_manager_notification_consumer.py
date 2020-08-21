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

from hgw_common.messaging.sender import create_sender
from hgw_common.models import FailedMessages
from hgw_common.utils import create_broker_parameters_from_settings
from hgw_common.utils.management import ConsumerCommand
from hgw_frontend.management.commands import db_safe
from hgw_frontend.models import Channel, ConsentConfirmation, Destination
from hgw_frontend.settings import (DATETIME_FORMAT,
                                   KAFKA_CHANNEL_NOTIFICATION_TOPIC,
                                   KAFKA_CONSENT_NOTIFICATION_TOPIC)

logger = logging.getLogger('hgw_frontend.consent_manager_notification_consumer')


class FAILED_REASON:
    FAILED_NOTIFICATION = 'FAILED_NOTIFICATION'
    INVALID_STRUCTURE = 'INVALID_STRUCTURE'
    JSON_DECODING = 'JSON_DECODING'
    UNKNOWN_CONSENT = 'UNKNOWN_CONSENT'
    MISMATCHING_PERSON = 'MISMATCHING_PERSON'
    MISMATCHING_SOURCE = 'MISMATCHING_SOURCE'
    INCONSISTENT_STATUS = 'INCONSISTENT_STATUS'


class ACTION:
    """
    The action performed to the channel
    """
    CREATED = 'CREATED'
    UPDATED = 'UPDATED'
    REVOKED = 'REVOKED'


FAILED_MESSAGE_TYPE = 'CONSENT'


class Command(ConsumerCommand):
    help = 'Launch Backend Notification Consumer'

    def __init__(self, *args, **kwargs):
        self.group_id = 'consent_manager_notification_consumer'
        self.topics = [KAFKA_CONSENT_NOTIFICATION_TOPIC]
        self.sender_topic = KAFKA_CHANNEL_NOTIFICATION_TOPIC
        self.sender = create_sender(create_broker_parameters_from_settings())
        super(Command, self).__init__(*args, **kwargs)

    def _validate_consent(self, consent, attempt=1):
        expected_keys = (
            'consent_id', 'person_id', 'status',
            'source', 'destination', 'profile',
            'start_validity', 'expire_validity'
        )

        try:
            for key in expected_keys:
                assert key in consent
        except AssertionError:
            logger.error('Consent structure missing some keys')
            return FAILED_REASON.INVALID_STRUCTURE

        try:
            logger.debug('Retrieving consent information')
            channel = ConsentConfirmation.objects.get(consent_id=consent['consent_id']).channel
        except ConsentConfirmation.DoesNotExist:
            logger.error('Cannot find the corresponding consent inside the db')
            return FAILED_REASON.UNKNOWN_CONSENT

        if channel.flow_request.person_id != consent['person_id']:
            logger.critical('The person id of the consent does not correspond to the Channel one')
            return FAILED_REASON.MISMATCHING_PERSON
        if channel.source.source_id != consent['source']['id']:
            logger.critical('The source id of the consent does not correspond to the Channel one')
            return FAILED_REASON.MISMATCHING_SOURCE

    def _notify(self, consent, action):
        destination = Destination.objects.get(destination_id=consent['destination']['id'])
        channel = {
            'channel_id': consent['consent_id'],
            'action': action,
            'source_id': consent['source']['id'],
            'destination': {
                'destination_id': destination.destination_id,
                'kafka_public_key': destination.kafka_public_key
            },
            'profile': consent['profile'],
            'person_id': consent['person_id'],
            'start_validity': consent['start_validity'],
            'expire_validity': consent['expire_validity']
        }
        notified = self.sender.send(self.sender_topic, channel)

        if not notified:
            failure_reason = FAILED_REASON.FAILED_NOTIFICATION
            return failure_reason
        else:
            logger.info('Channel operation notified')

    @db_safe(ConsentConfirmation)
    def handle_message(self, message):
        logger.info('Found message for queue %s', message['queue'])

        failure_reason = None
        retry = False
        if not message['success']:
            logger.error('Cannot handle message. JSON Error')
            failure_reason = FAILED_REASON.JSON_DECODING
        else:
            consent = message['data']

            failure_reason = self._validate_consent(consent)
            if failure_reason is None:
                consent_confirmation = ConsentConfirmation.objects.get(consent_id=consent['consent_id'])
                channel = consent_confirmation.channel
                if consent['status'] == 'AC' and channel.status == Channel.CONSENT_REQUESTED:  # Consent confirmed
                    logger.debug('Consent has been given in the Consent Manager')
                    channel.start_validity = consent['start_validity']
                    channel.expire_validity = consent['expire_validity']
                    channel.status = Channel.WAITING_SOURCE_NOTIFICATION
                    channel.save()

                    failure_reason = self._notify(consent, ACTION.CREATED)
                    if failure_reason is not None:
                        retry = True
                elif consent['status'] == 'AC' and channel.status in (Channel.ACTIVE, Channel.WAITING_SOURCE_NOTIFICATION):  # Consent changed
                    logger.debug('Consent has been changed in the Consent Manager. ')
                    new_start_validity = datetime.strptime(consent['start_validity'], DATETIME_FORMAT) \
                        if consent['start_validity'] is not None else None
                    new_expire_validity = datetime.strptime(consent['expire_validity'], DATETIME_FORMAT) \
                        if consent['expire_validity'] is not None else None
                    if channel.start_validity != new_start_validity or channel.expire_validity != new_expire_validity:
                        logger.debug('Changing the channel accordingly')
                        channel.start_validity = consent['start_validity']
                        channel.expire_validity = consent['expire_validity']
                        channel.save()
                        
                        failure_reason = self._notify(consent, ACTION.UPDATED)
                        if failure_reason is not None:
                            retry = True
                    else:
                        consent['expire_validity']
                        logger.debug('Data from consent equal to the ones already stored. Not changing')
                        failure_reason = FAILED_REASON.INCONSISTENT_STATUS
                        retry = False

                elif consent['status'] == 'RE' and channel.status in (Channel.ACTIVE, Channel.WAITING_SOURCE_NOTIFICATION):  # Consent revoked
                    logger.debug('Consent has been revoked in the Consent Manager. ')
                    channel.status = Channel.CONSENT_REVOKED
                    channel.save()

                    failure_reason = self._notify(consent, ACTION.REVOKED)
                    if failure_reason is not None:
                        retry = True
                else:
                    failure_reason = FAILED_REASON.INCONSISTENT_STATUS
                    retry = False

        if failure_reason is not None:
            FailedMessages.objects.create(
                message_type=FAILED_MESSAGE_TYPE, message=json.dumps(message),
                reason=failure_reason, retry=retry
            )
