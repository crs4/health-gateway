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

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from hgw_common.cipher import is_encrypted
from hgw_common.messaging.sender import create_sender
from hgw_common.messaging.serializer import RawSerializer
from hgw_common.models import Profile
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import create_broker_parameters_from_settings, get_logger
from hgw_common.utils.authorization import TokenHasResourceDetailedScope

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

        topic = self._get_kafka_topic(request)
        sender = create_sender(create_broker_parameters_from_settings(), serializer=RawSerializer)

        success = sender.send(topic, payload, key=channel_id.decode('utf-8'))
        if success is False:
            logger.error('Cannot connect to kafka')
            return Response({'error': 'cannot_send_message'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({}, 200)
