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
import sys

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from kafka import KafkaConsumer, TopicPartition
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.utils import TokenHasResourceDetailedScope
from hgw_frontend.models import Destination
from hgw_frontend.settings import KAFKA_BROKER, KAFKA_CA_CERT, KAFKA_CLIENT_CERT, KAFKA_CLIENT_KEY, KAFKA_SSL

DEFAULT_LIMIT = 5
MAX_LIMIT = 10


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

    @check_destination
    def retrieve(self, request, message_id):
        message_id = int(message_id)
        kc, tp = self._get_kafka_consumer(request)
        first_offset = kc.beginning_offsets([tp])[tp]
        last_offset = kc.end_offsets([tp])[tp] - 1
        if first_offset <= message_id <= last_offset:
            kc.seek(tp, message_id)
            msg = next(kc)
            response = {
                'message_id': msg.offset,
                'process_id': msg.key,
                'data': base64.b64encode(msg.value)
            }
        else:
            return Response({'first_id': first_offset,
                             'last_id': last_offset},
                            status.HTTP_404_NOT_FOUND,
                            content_type='application/json')
        return Response(response, content_type='application/json')

    @check_destination
    def list(self, request):
        kc, tp = self._get_kafka_consumer(request)
        kc.assign([tp])
        first_offset = kc.beginning_offsets([tp])[tp]
        end_offset = kc.end_offsets([tp])[tp]
        start = int(request.GET.get('start', first_offset))
        limit = int(request.GET.get('limit', DEFAULT_LIMIT))
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT
        total_count = end_offset - first_offset
        if start < first_offset:
            # If we the first is greater than the skip we answer with not found
            return Response({'first_id': first_offset,
                             'last_id': end_offset - 1},
                            status.HTTP_404_NOT_FOUND,
                            content_type='application/json')
        if start + limit > end_offset:
            limit = end_offset - start
        kc.seek(tp, start)
        response = []
        for i in range(limit):
            msg = next(kc)
            response.append({
                'message_id': msg.offset,
                'process_id': msg.key,
                'data': base64.b64encode(msg.value)
            })
        headers = {
            'X-Skipped': start - first_offset,
            'X-Total-Count': total_count
        }
        return Response(response, content_type='application/json', headers=headers)

    @swagger_auto_schema(
        operation_description='Returns information regarding the messages available for a destination. The destination '
                              'is implicitly taken from the OAuth2 token',
        security=[{'messages': ['messages:read']}],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'start_id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                       description='The id of the first message available'),
                            'last_id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                      description='The id of tha last message available'),
                            'count': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                    description='The number of messages available')}
            ),
            401: openapi.Response('Unauthorized - The client has not provide a valid token or the token has expired'),
            403: openapi.Response('Forbidden - The client token has not the right scope for the operation'),
        })
    @check_destination
    def info(self, request):
        kc, tp = self._get_kafka_consumer(request)
        first_offset = kc.beginning_offsets([tp])[tp]
        last_offset = kc.end_offsets([tp])[tp]
        count = last_offset - first_offset
        return Response({
            'start_id': first_offset,
            'last_id': last_offset - 1,
            'count': count
        })
