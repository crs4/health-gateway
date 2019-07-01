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

from hgw_common.messaging.notifier import get_sender
from hgw_common.utils import KafkaConsumerCommand, get_logger
from hgw_common.models import FailedMessages
from hgw_frontend.models import Channel, ConsentConfirmation, Destination, \
    FlowRequest
from hgw_frontend.settings import (KAFKA_CHANNEL_NOTIFICATION_TOPIC,
                                   KAFKA_CONSENT_NOTIFICATION_TOPIC)


logger = get_logger(__file__)

class FAILED_REASON():
    FAILED_NOTIFICATION = 'FAILED_NOTIFICATION'
    INVALID_STRUCTURE = 'INVALID_STRUCTURE'
    JSON_DECODING = 'JSON_DECODING'
    UNKNOWN_CONSENT = 'UNKNOWN_CONSENT'
    MISMATCHING_PERSON = 'MISMATCHING_PERSON'
    MISMATCHING_SOURCE = 'MISMATCHING_SOURCE'


FAILED_MESSAGE_TYPE = 'CONSENT'

class Command(KafkaConsumerCommand):
    help = 'Launch Backend Notification Consumer'


    def __init__(self, *args, **kwargs):
        self.client_id = self.group_id = 'consent_manager_notification_consumer'
        self.topics = [KAFKA_CONSENT_NOTIFICATION_TOPIC]
        self.notifier = get_sender(KAFKA_CHANNEL_NOTIFICATION_TOPIC)
        super(Command, self).__init__(*args, **kwargs)

    def _validate_consent(self, consent):
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

    def handle_message(self, message):
        logger.info('Found message for topic %s', message.topic)
        try:
            consent = json.loads(message.value.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error('Cannot handle message. JSON Error')
            FailedMessages.objects.create(
                message_type=FAILED_MESSAGE_TYPE, message=message,
                reason=FAILED_REASON.JSON_DECODING, retry=False
            )
        else:
            fail_reason = self._validate_consent(consent)
            if fail_reason:
                FailedMessages.objects.create(
                    message_type=FAILED_MESSAGE_TYPE, message=message,
                    reason=fail_reason, retry=False
                )
            else:
                consent_confirmation = ConsentConfirmation.objects.get(consent_id=consent['consent_id'])
                channel = consent_confirmation.channel
                if channel.status == Channel.CONSENT_REQUESTED and consent['status'] == 'AC':
                    logger.debug('Consent status is AC. Sending message to KAFKA')
                    channel.status = Channel.WAITING_SOURCE_NOTIFICATION
                    channel.save()

                    destination = Destination.objects.get(destination_id=consent['destination']['id'])
                    channel = {
                        'channel_id': consent['consent_id'],
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

                    notified = self.notifier.notify(channel)
                    if not notified:
                        FailedMessages.objects.create(
                            message_type=FAILED_MESSAGE_TYPE, message=message,
                            reason=FAILED_REASON.FAILED_NOTIFICATION, retry=True
                        )
                    else:
                        logger.info('Channel notified to backend')
