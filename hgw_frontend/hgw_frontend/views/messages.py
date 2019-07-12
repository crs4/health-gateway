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
import base64
import json
import sys

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from kafka import KafkaConsumer, TopicPartition
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.messaging.deserializer import RawDeserializer
from hgw_common.messaging.receiver import create_receiver
from hgw_common.utils import create_broker_parameters_from_settings
from hgw_common.utils.authorization import TokenHasResourceDetailedScope
from hgw_frontend.models import Destination
from hgw_frontend.settings import (KAFKA_BROKER, KAFKA_CA_CERT,
                                   KAFKA_CLIENT_CERT, KAFKA_CLIENT_KEY,
                                   KAFKA_SSL)

DEFAULT_LIMIT = 5
MAX_LIMIT = 10
RECEIVER_NAME = 'hgw_frontend_messages_api'


def check_destination(f):
    def wrapper(self, request, *args, **kwargs):
        if request.auth.application.destination.rest_or_kafka == Destination.KAFKA:
            return Response("", status.HTTP_403_FORBIDDEN)
        return f(self, request, *args, **kwargs)

    return wrapper


class Messages(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['messages']

    def _get_kafka_consumer(self, request):
        topic = request.auth.application.destination.destination_id
        if KAFKA_SSL:
            consumer_params = {
                'bootstrap_servers': KAFKA_BROKER,
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': KAFKA_CA_CERT,
                'ssl_certfile': KAFKA_CLIENT_CERT,
                'ssl_keyfile': KAFKA_CLIENT_KEY
            }
        else:
            consumer_params = {
                'bootstrap_servers': KAFKA_BROKER
            }
        kc = KafkaConsumer(**consumer_params)
        tp = TopicPartition(topic, 0)
        kc.assign([tp])
        return kc, tp

    def _construct_correct_response(self, msg):
        response = {
            'message_id': msg['id'],
            'data': base64.b64encode(msg['data'])
        }
        response.update(dict((k, v.decode('utf-8')) for (k, v) in msg['headers']))
        return response

    @check_destination
    def retrieve(self, request, message_id):
        message_id = int(message_id)

        topic = request.auth.application.destination.destination_id
        receiver = create_receiver(topic, RECEIVER_NAME, create_broker_parameters_from_settings(), 
                                   blocking=False, deserializer=RawDeserializer)
        first_id = receiver.get_first_id(topic)
        last_id = receiver.get_last_id(topic)
        if first_id <= message_id <= last_id:
            msg = receiver.get_by_id(message_id, topic)
            return Response(self._construct_correct_response(msg), content_type='application/json')
        else:
            response = {
                'first_id': first_id,
                'last_id': last_id
            }
            return Response(response,
                            status.HTTP_404_NOT_FOUND,
                            content_type='application/json')

    @check_destination
    def list(self, request):
        topic = request.auth.application.destination.destination_id
        receiver = create_receiver(topic, RECEIVER_NAME, create_broker_parameters_from_settings(), 
                                   blocking=False, deserializer=RawDeserializer)

        first_id = receiver.get_first_id(topic)
        last_id = receiver.get_last_id(topic)

        start = int(request.GET.get('start', first_id))
        limit = int(request.GET.get('limit', DEFAULT_LIMIT))

        if limit > MAX_LIMIT:
            limit = MAX_LIMIT

        if start < first_id:
            # If the start offset is less than the first offset available, we answer with not found
            return Response({'first_id': first_id,
                             'last_id': last_id},
                            status.HTTP_404_NOT_FOUND,
                            content_type='application/json')

        messages = [self._construct_correct_response(msg) for msg in receiver.get_range(start, start + limit - 1, topic)]
        headers = {
            'X-Skipped': start - first_id,
            'X-Total-Count': last_id - first_id + 1
        }
        return Response(messages, content_type='application/json', headers=headers)

    @check_destination
    def info(self, request):
        topic = request.auth.application.destination.destination_id
        receiver = create_receiver(topic, RECEIVER_NAME, create_broker_parameters_from_settings(), 
                                   blocking=False, deserializer=RawDeserializer)

        first_id = receiver.get_first_id(topic)
        last_id = receiver.get_last_id(topic)

        count = last_id + 1 - first_id
        return Response({
            'start_id': first_id,
            'last_id': last_id ,
            'count': count
        })
