import requests
from django.http import Http404
from oauthlib.oauth2 import InvalidClientError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.models import OAuth2SessionProxy, Profile
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils.authorization import TokenHasResourceDetailedScope
from hgw_frontend import ERRORS_MESSAGE
from hgw_frontend.models import Source
from hgw_frontend.serializers import SourceSerializer
from hgw_frontend.settings import (HGW_BACKEND_CLIENT_ID,
                                   HGW_BACKEND_CLIENT_SECRET, HGW_BACKEND_URI)


class Sources(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['sources']

    def list(self, request):
        sources = Source.objects.all()
        serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data, content_type='application/json')

    def retrieve(self, request, source_id):
        try:
            source = Source.objects.get(source_id=source_id)
        except Source.DoesNotExist:
            raise Http404
        else:
            serializer = SourceSerializer(source)
        return Response(serializer.data, content_type='application/json')

class Profiles(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['sources']

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