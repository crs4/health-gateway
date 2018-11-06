import requests
from oauthlib.oauth2 import InvalidClientError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.models import OAuth2SessionProxy
from hgw_common.utils import TokenHasResourceDetailedScope
from hgw_frontend import ERRORS_MESSAGE
from hgw_frontend.settings import HGW_BACKEND_CLIENT_ID, HGW_BACKEND_URI, HGW_BACKEND_CLIENT_SECRET


class Sources(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['sources']

    def list(self, request):
        try:
            oauth_backend_session = OAuth2SessionProxy('{}/oauth2/token/'.format(HGW_BACKEND_URI),
                                                       HGW_BACKEND_CLIENT_ID,
                                                       HGW_BACKEND_CLIENT_SECRET)
        except InvalidClientError:
            return Response({'errors': [ERRORS_MESSAGE['INVALID_BACKEND_CLIENT']]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except requests.exceptions.ConnectionError:
            return Response({'errors': [ERRORS_MESSAGE['BACKEND_CONNECTION_ERROR']]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            res = oauth_backend_session.get('{}/v1/sources/'.format(HGW_BACKEND_URI))

        return Response(res.json(), content_type='application/json')

    def retrieve(self, request, source_id):
        try:
            oauth_backend_session = OAuth2SessionProxy('{}/oauth2/token/'.format(HGW_BACKEND_URI),
                                                       HGW_BACKEND_CLIENT_ID,
                                                       HGW_BACKEND_CLIENT_SECRET)
        except InvalidClientError:
            return Response({'errors': [ERRORS_MESSAGE['INVALID_BACKEND_CLIENT']]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except requests.exceptions.ConnectionError:
            return Response({'errors': [ERRORS_MESSAGE['BACKEND_CONNECTION_ERROR']]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            res = oauth_backend_session.get('{}/v1/sources/{}/'.format(HGW_BACKEND_URI, source_id))

        return Response(res.json(), content_type='application/json')


class Profiles(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['sources']

    def list(self, request):
        try:
            oauth_backend_session = OAuth2SessionProxy('{}/oauth2/token/'.format(HGW_BACKEND_URI),
                                                       HGW_BACKEND_CLIENT_ID,
                                                       HGW_BACKEND_CLIENT_SECRET)
        except InvalidClientError:
            return Response({'errors': [ERRORS_MESSAGE['INVALID_BACKEND_CLIENT']]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except requests.exceptions.ConnectionError:
            return Response({'errors': [ERRORS_MESSAGE['BACKEND_CONNECTION_ERROR']]},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            res = oauth_backend_session.get('{}/v1/profiles/'.format(HGW_BACKEND_URI))

        return Response(res.json(), content_type='application/json')