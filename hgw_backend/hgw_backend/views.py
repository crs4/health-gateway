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
from _ssl import SSLError
from traceback import format_exc

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import Http404, HttpResponse
from kafka import KafkaProducer
from kafka.errors import (KafkaError, KafkaTimeoutError, NoBrokersAvailable,
                          TopicAuthorizationFailedError)
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from hgw_backend.utils import get_kafka_producer
from hgw_common.cipher import is_encrypted
from hgw_common.models import Profile
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import TokenHasResourceDetailedScope, get_logger

from .models import Source
from .serializers import SourceSerializer

logger = get_logger('hgw_backend')


def home(request):
    return HttpResponse('<a href="/admin/">Click here to access admin page</a>')


class Sources(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['sources']

    def get_object(self, source_id):
        try:
            return Source.objects.get(source_id=source_id)
        except Source.DoesNotExist:
            raise Http404

    def list(self, request):
        sources = Source.objects.all()
        serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data, content_type='application/json')

    def retrieve(self, request, source_id):
        source = self.get_object(source_id)
        serializer = SourceSerializer(source)
        return Response(serializer.data, content_type='application/json')


class Profiles(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['sources']

    def get_object(self, source_id):
        try:
            return Profile.objects.get(source_id=source_id)
        except Source.DoesNotExist:
            raise Http404

    def list(self, request):
        profiles = Profile.objects.all()
        profiles_ser = ProfileSerializer(profiles, many=True)
        profiles_data = profiles_ser.data
        for i, p in enumerate(profiles):
            sources = Source.objects.filter(profile=p)
            source_serializer = SourceSerializer(sources, many=True)
            profiles_data[i]['sources'] = [{'source_id': s['source_id'], 'name': s['name']}
                                           for s in source_serializer.data]

        return Response(profiles_data, content_type='application/json')
    #
    # def retrieve(self, request, source_id):
    #     source = self.get_object(source_id)
    #     serializer = SourceSerializer(source)
    #     return Response(serializer.data, content_type='application/json')


class Messages(APIView):
    """
    Viewset for /messages/ REST API
    """
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['messages']
    parser_classes = (MultiPartParser,)

    @staticmethod
    def _get_kafka_topic(request):
        return request.auth.application.source.source_id

    def post(self, request):
        """
        Create a message
        """
        if 'channel_id' not in request.data or 'payload' not in request.data:
            logger.debug('Missing channel_id or payload in request')
            return Response({'error': 'missing_parameters'}, status.HTTP_400_BAD_REQUEST)

        payload = request.data.getlist('payload')
        if len(payload) > 1:
            payload = bytes(map(int, payload))
        else:
            if isinstance(payload[0], InMemoryUploadedFile):
                payload = payload[0].read()
            else:
                payload = payload[0].encode('utf-8')

        if not is_encrypted(payload):
            logger.info('Source %s sent an unencrypted message', self.request.auth.application.source.name)
            return Response({'error': 'not_encrypted_payload'}, status.HTTP_400_BAD_REQUEST)

        try:
            channel_id = request.data['channel_id'].encode('utf-8')
        except ValueError:
            return Response({'error': 'invalid_paramater: channel_id'})

        producer = get_kafka_producer()
        if producer is None:
            return Response({'error': 'cannot_send_message'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            topic = self._get_kafka_topic(request)
            try:
                future = producer.send(topic, key=channel_id, value=payload)
            except KafkaTimeoutError:
                logger.debug('Cannot get topic %s metadata. Probably the token does not exist', topic)
                # Topic doesn't exist
                return Response({'error': 'cannot_send_message'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Block for 'synchronous' sends
            try:
                future.get(timeout=2)
            except TopicAuthorizationFailedError:
                logger.debug('Missing write permission to write in topic %s', topic)
                return Response({'error': 'cannot_send_message'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            except KafkaError:
                logger.debug('An error occurred sending message to topic %s. Error details %s', topic, format_exc())
                # Decide what to do if produce request failed...
                return Response({'error': 'cannot_send_message'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.debug('Connector creation notified correctly')

        return Response({}, 200)
