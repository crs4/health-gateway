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


import datetime
import json
import logging
from operator import xor

import coreapi
import requests
import six
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from kafka import KafkaProducer
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from rest_framework import status
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.viewsets import ViewSet

import hgw_frontend.serializers
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import TokenHasResourceDetailedScope
from hgw_frontend import CONFIRM_ACTIONS, ERRORS_MESSAGE
from hgw_frontend.models import FlowRequest, ConfirmationCode, ConsentConfirmation, Destination
from hgw_frontend.settings import CONSENT_MANAGER_CLIENT_ID, CONSENT_MANAGER_CLIENT_SECRET, CONSENT_MANAGER_URI, \
    KAFKA_TOPIC, KAFKA_BROKER, HGW_BACKEND_URI, KAFKA_CLIENT_KEY, KAFKA_CLIENT_CRT, KAFKA_CA_CERT

logger = logging.getLogger('hgw_frontend')
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(fmt)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class UnknownConsentConfirmation(Exception):
    pass


class FlowRequestView(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['flow_request']
    # for the search view we also want the token to have the query scope
    view_specific_scopes = {'search': {'read': ['query']}}

    @staticmethod
    def get_flow_request(request, process_id):
        try:
            if request.auth.application.is_super_client():
                return FlowRequest.objects.get(process_id=process_id)
            else:
                return FlowRequest.objects.get(destination=request.auth.application.destination, process_id=process_id)
        except FlowRequest.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_description='Return the list of flow requests',
        security=[{'flow_request': ['flow_request:read']}],
        responses={
            200: openapi.Response('Success - The list of flow requests', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'flow_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                  description='The id assigned to the flow request by the '
                                                              'destination'),
                        'process_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                     description='The id assigned to the flow request by the '
                                                                 'Health Gateway'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='The status of the flow request',
                                                 enum=[sc[0] for sc in FlowRequest.STATUS_CHOICES]),
                        'profile': openapi.Schema(type=openapi.TYPE_OBJECT,
                                                  properties={
                                                      'code': openapi.Schema(type=openapi.TYPE_STRING,
                                                                             description='A code identifying the profile'),
                                                      'version': openapi.Schema(type=openapi.TYPE_STRING,
                                                                                description='The version of the profile'),
                                                      'payload': openapi.Schema(type=openapi.TYPE_STRING,
                                                                                description='A json encoded string that'
                                                                                            'describe the profile')
                                                  }),
                        'start_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                         format=openapi.FORMAT_DATETIME,
                                                         description='The start date validity of the flow request'),
                        'expire_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                          format=openapi.FORMAT_DATETIME,
                                                          description='The end date validity of the flow request')
                    }
                )
            )),
            401: openapi.Response('Unauthorized - The client has not provide a valid token or the token has expired'),
            403: openapi.Response('Forbidden - The client token has not the right scope for the operation'),
        })
    def list(self, request):
        if request.auth.application.is_super_client():
            flow_requests = FlowRequest.objects.all()
        else:
            flow_requests = FlowRequest.objects.filter(destination=request.auth.application.destination)
        serializer = hgw_frontend.serializers.FlowRequestSerializer(flow_requests, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description='Create a new flow request which will be set in a pending status until the user '
                              'confirms it. To do that the user needs to go to the `/flow_request/confirm` url '
                              'using as query parameter the confirmation_id returned by this operation',
        security=[{'flow_request': ['flow_request:write']}],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'flow_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='The id assigned to the flow request by the destination'),
                'profile': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'code': openapi.Schema(type=openapi.TYPE_STRING,
                                               description='A code identifying the profile'),
                        'version': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='The version of the profile'),
                        'payload': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='A json encoded string that'
                                        'describe the profile')
                    }),
                'start_validity': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description='The start date validity of the flow request'),
                'expire_validity': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description='The end date validity of the flow request'),
            }),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'process_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                         description='the id that identifies the flow request in '
                                                                     'the health gateway. The client must maintain '
                                                                     'the mapping between the process_id and the '
                                                                     'flow_id to be used in subsequent process'),
                            'confirmation_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                              description='the id to send to the confirmation '
                                                                          'url to activate the flow request')}
            ),
            400: openapi.Response('Bad Request - Missing or wrong parameters'),
            401: openapi.Response('Unathorized - The client has not provide a valid token or the token has expired'),
            403: openapi.Response('Forbidden - The client token has not the right scope for the operation'),
        })
    def create(self, request):
        if 'flow_id' not in request.data or 'profile' not in request.data or \
                xor(('start_validity' not in request.data), ('expire_validity' not in request.data)):
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
        data = {
            'flow_id': request.data['flow_id'],
            'process_id': get_random_string(32),
            'status': FlowRequest.PENDING,
            'profile': request.data['profile'],
            'destination': request.auth.application.destination.pk
        }
        if 'start_validity' not in request.data and 'expire_validity' not in request.data:
            # Assign default values for the validity range: current datetime + 6 months
            start_datetime = datetime.datetime.now()
            expire_datetime = start_datetime + datetime.timedelta(6 * 30)
            data['start_validity'] = start_datetime.strftime(TIME_FORMAT)
            data['expire_validity'] = expire_datetime.strftime(TIME_FORMAT)
        else:
            data['start_validity'] = request.data['start_validity']
            data['expire_validity'] = request.data['expire_validity']

        fr_serializer = hgw_frontend.serializers.FlowRequestSerializer(data=data)

        if fr_serializer.is_valid():
            try:
                fr = fr_serializer.save()
            except IntegrityError as e:
                logger.debug(fr_serializer.data)
                return Response(ERRORS_MESSAGE['INVALID_DATA'], status=status.HTTP_400_BAD_REQUEST)
            cc = ConfirmationCode.objects.create(flow_request=fr)
            cc.save()
            res = {k: v for k, v in six.iteritems(fr_serializer.data)}
            res.update({'confirm_id': cc.code})

            return Response(res, status=status.HTTP_201_CREATED)
        else:
            logger.error("Error adding Flow Request. Details {}".format(fr_serializer.errors))
        return Response(ERRORS_MESSAGE['INVALID_DATA'], status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, process_id, format=None):
        fr = self.get_flow_request(request, process_id)
        fr.status = FlowRequest.DELETE_REQUESTED
        fr.save()

        cc = ConfirmationCode.objects.create(flow_request=fr)
        cc.save()
        res = {'confirm_id': cc.code}

        return Response(res, status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(
        operation_description='Returns the flow request specified by the process_id parameter',
        security=[{'flow_request': ['flow_request:read']}],
        manual_parameters=[
            openapi.Parameter('process_id', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              description='The process_id identifying the requested flow request'),
        ],
        responses={
            200: openapi.Response('The flow request identified by the process_id in input', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'flow_id': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='The id assigned to the flow request by the '
                                                          'destination'),
                    'process_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='The id assigned to the flow request by the '
                                                             'Health Gateway'),
                    'status': openapi.Schema(type=openapi.TYPE_STRING,
                                             description='The status of the flow request',
                                             enum=[sc[0] for sc in FlowRequest.STATUS_CHOICES]),
                    'profile': openapi.Schema(type=openapi.TYPE_OBJECT,
                                              properties={
                                                  'code': openapi.Schema(type=openapi.TYPE_STRING,
                                                                         description='A code identifying the profile'),
                                                  'version': openapi.Schema(type=openapi.TYPE_STRING,
                                                                            description='The version of the profile'),
                                                  'payload': openapi.Schema(type=openapi.TYPE_STRING,
                                                                            description='A json encoded string that'
                                                                                        'describe the profile')
                                              }),
                    'start_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                     format=openapi.FORMAT_DATETIME,
                                                     description='The start date validity of the flow request'),
                    'expire_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                      format=openapi.FORMAT_DATETIME,
                                                      description='The end date validity of the flow request')
                }
            )),
            401: openapi.Response('Unauthorized - The client has not provide a valid token or the token has expired'),
            403: openapi.Response('Forbidden - The client token has not the right scope for the operation'),
            404: openapi.Response('Not Found - The flow request has not been found')
        })
    def retrieve(self, request, process_id, format=None):
        fr = self.get_flow_request(request, process_id)
        serializer = hgw_frontend.serializers.FlowRequestSerializer(fr)
        res = {k: v for k, v in six.iteritems(serializer.data) if k != 'destination'}
        return Response(res)

    @swagger_auto_schema(
        operation_description='Seaech for flow request by channel_id',
        security=[{'flow_request': ['flow_request:read', 'flow_request:query']}],
        manual_parameters=[
            openapi.Parameter('channel_id', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('The flow request corresponding to the channel_id in input', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'flow_id': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='The id assigned to the flow request by the destination'),
                    'process_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='The id assigned to the flow request by the '
                                                             'Health Gateway'),
                    'status': openapi.Schema(type=openapi.TYPE_STRING,
                                             description='The status of the flow request',
                                             enum=[sc[0] for sc in FlowRequest.STATUS_CHOICES]),
                    'profile': openapi.Schema(type=openapi.TYPE_OBJECT,
                                              properties={
                                                  'code': openapi.Schema(type=openapi.TYPE_STRING,
                                                                         description='A code identifying the profile'),
                                                  'version': openapi.Schema(type=openapi.TYPE_STRING,
                                                                            description='The version of the profile'),
                                                  'payload': openapi.Schema(type=openapi.TYPE_STRING,
                                                                            description='A json encoded string that'
                                                                                        'describe the profile')
                                              }),
                    'start_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                     format=openapi.FORMAT_DATETIME,
                                                     description='The start date validity of the flow request'),
                    'expire_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                      format=openapi.FORMAT_DATETIME,
                                                      description='The end date validity of the flow request')
                }
            )),
            401: openapi.Response('Unauthorized - The client has not provide a valid token or the token has expired'),
            403: openapi.Response('Forbidden - The client token has not the right scope for the operation'),
            404: openapi.Response('Not Found - The flow request has not been found')
        })
    def search(self, request):
        if 'channel_id' in request.GET:
            try:
                consent_confirmation = ConsentConfirmation.objects.get(consent_id=request.GET['channel_id'])
                flow_request = consent_confirmation.flow_request
                serializer = hgw_frontend.serializers.FlowRequestSerializer(instance=flow_request)
            except ConsentConfirmation.DoesNotExist:
                return Response({}, status.HTTP_404_NOT_FOUND)
            return Response(serializer.data)
        else:
            return Response({}, status.HTTP_400_BAD_REQUEST)


def _get_consent_oauth_token():
    client = BackendApplicationClient(CONSENT_MANAGER_CLIENT_ID)
    oauth_session = OAuth2Session(client=client)
    token_url = '{}/oauth2/token/'.format(CONSENT_MANAGER_URI)
    access_token = oauth_session.fetch_token(token_url=token_url, client_id=CONSENT_MANAGER_CLIENT_ID,
                                             client_secret=CONSENT_MANAGER_CLIENT_SECRET)

    access_token = access_token["access_token"]
    access_token_header = {"Authorization": "Bearer {}".format(access_token)}
    return oauth_session, access_token_header


def _create_consent(flow_request, destination_endpoint_callback_url, user):
    profile_payload = [{'clinical_domain': 'Laboratory',
                        'filters': [{'includes': 'Immunochemistry', 'excludes': 'HDL'}]},
                       {'clinical_domain': 'Radiology',
                        'filters': [{'includes': 'Tomography', 'excludes': 'Radiology'}]},
                       {'clinical_domain': 'Emergency',
                        'filters': [{'includes': '', 'excludes': ''}]},
                       {'clinical_domain': 'Prescription',
                        'filters': [{'includes': '', 'excludes': ''}]}]
    profile_data = {
        'code': 'PROF002',
        'version': 'hgw.document.profile.v0',
        'payload': json.dumps(profile_payload)
    }

    destination = flow_request.destination

    res = requests.get('{}/v1/sources/'.format(HGW_BACKEND_URI))

    confirm_ids = []
    oauth_session, access_token_header = _get_consent_oauth_token()
    for source_data in res.json():
        channel_data = {
            'source': {
                'id': source_data['source_id'],
                'name': source_data['name']
            },
            'destination': {
                'id': destination.destination_id,
                'name': destination.name
            },
            'profile': profile_data,
            'person_id': user.fiscalNumber,
            'start_validity': flow_request.start_validity.strftime(TIME_FORMAT),
            'expire_validity': flow_request.expire_validity.strftime(TIME_FORMAT)
        }

        res = oauth_session.post('{}/v1/consents/'.format(CONSENT_MANAGER_URI),
                                 headers=access_token_header, json=channel_data)
        if res.status_code == 201:
            json_res = res.json()
            ConsentConfirmation.objects.create(flow_request=flow_request, consent_id=json_res['consent_id'],
                                               confirmation_id=json_res['confirm_id'],
                                               destination_endpoint_callback_url=destination_endpoint_callback_url)
            confirm_ids.append(json_res['confirm_id'])

    return confirm_ids


def _get_consent(confirm_id):
    """
    Query the consent manager for the consent with confirmation_id equale to confirm_id
    :param confirm_id: the confirmation_id of the consent to get
    :return:
    """
    try:
        consent_confirmation = ConsentConfirmation.objects.get(confirmation_id=confirm_id)
    except ConsentConfirmation.DoesNotExist:
        raise UnknownConsentConfirmation()
    consent_id = consent_confirmation.consent_id
    oauth_session, access_token_header = _get_consent_oauth_token()
    res = oauth_session.get('{}/v1/consents/{}/'.format(CONSENT_MANAGER_URI, consent_id))
    return consent_confirmation, res.json()


def _get_callback_url(request):
    """
    Return the URL to confirm a flow request
    :param request:
    :return:
    """
    return '{}://{}/v1/flow_requests/consents_confirmed/'.format(request.scheme, request.get_host())


def _ask_consent(request, flow_request, callback_url):
    if flow_request.status == FlowRequest.PENDING:
        consents = _create_consent(flow_request, callback_url, request.user)
        if not consents:
            return HttpResponse("All available consents already inserted")
        logger.debug("Created consent")
        consent_callback_url = _get_callback_url(request)
        return HttpResponseRedirect('{}/v1/consents/confirm/?{}&callback_url={}'.
                                    format(CONSENT_MANAGER_URI,
                                           '&'.join(['confirm_id={}'.format(consent) for consent in consents]),
                                           consent_callback_url))
    else:
        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_FR_STATUS'])


def _confirm(request, consent_confirm_id):
    try:
        logger.debug("Getting consent from Consent Manager")
        consent_confirmation, consent = _get_consent(consent_confirm_id)
        logger.debug("Found consent")
    except UnknownConsentConfirmation:
        return False

    if consent['status'] == 'AC':
        logger.debug("Consent status is AC. Sending message to KAFKA")
        kp = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                           security_protocol='SSL',
                           ssl_check_hostname=True,
                           ssl_cafile=KAFKA_CA_CERT,
                           ssl_certfile=KAFKA_CLIENT_CRT,
                           ssl_keyfile=KAFKA_CLIENT_KEY)
        destination = Destination.objects.get(destination_id=consent['destination']['id'])
        profile_ser = ProfileSerializer(consent_confirmation.flow_request.profile)
        channel = {
            'channel_id': consent_confirmation.consent_id,
            'source_id': consent['source']['id'],
            'destination': {
                'destination_id': destination.destination_id,
                'kafka_public_key': destination.kafka_public_key
            },
            'profile': profile_ser.data,
            'person_id': request.user.fiscalNumber
        }

        kp.send(KAFKA_TOPIC, json.dumps(channel).encode('utf-8'))

        fr = consent_confirmation.flow_request
        fr.status = FlowRequest.ACTIVE
        fr.save()
        return True
    return False


@require_GET
@login_required
def consents_confirmed(request):
    consent_confirm_ids = request.GET.getlist('consent_confirm_id')
    success = json.loads(request.GET['success'])
    flow_requests = FlowRequest.objects.filter(consentconfirmation__confirmation_id__in=consent_confirm_ids) \
        .distinct()
    if flow_requests.count() != 1:
        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_DATA'])
    flow_request = flow_requests[0]
    logger.debug("Flow request found")
    callback = flow_request.consentconfirmation_set.all()[0].destination_endpoint_callback_url
    done = False
    if success:
        for consent_confirm_id in consent_confirm_ids:
            logger.debug("Checking consents")
            done = _confirm(request, consent_confirm_id)
    return HttpResponseRedirect('{}?process_id={}&success={}'.format(
        callback, flow_request.process_id, json.dumps(done))
    )


@require_GET
@login_required
def confirm_request(request):
    if not request.user.fiscalNumber:
        return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PERSON_ID'])

    try:
        logger.debug('request.GET.keys() %s', request.GET.keys())
        fr_confirm_code = request.GET['confirm_id']
        fr_callback_url = request.GET['callback_url']
        action = request.GET['action']
    except KeyError as ex:
        return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PARAM'])
    else:
        if action not in CONFIRM_ACTIONS:
            return HttpResponseBadRequest(ERRORS_MESSAGE['UNKNOWN_ACTION'])
        try:
            cc = ConfirmationCode.objects.get(code=fr_confirm_code)
        except ConfirmationCode.DoesNotExist:
            return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_CONFIRMATION_CODE'])
        else:
            if not cc.check_validity():
                return HttpResponseBadRequest(ERRORS_MESSAGE['EXPIRED_CONFIRMATION_ID'])
            else:
                fr = cc.flow_request
                if action == CONFIRM_ACTIONS[0]:
                    return _ask_consent(request, fr, fr_callback_url)
                else:
                    if fr.status == FlowRequest.DELETE_REQUESTED:
                        fr.delete()
                        return HttpResponseRedirect(fr_callback_url)
                    else:
                        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_FR_STATUS'])
