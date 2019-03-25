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
import requests
import six
from dateutil.tz import gettz
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from kafka import KafkaProducer
from oauthlib.oauth2 import InvalidClientError
from operator import xor
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.models import OAuth2SessionProxy
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import TokenHasResourceDetailedScope, ERRORS
from hgw_frontend import CONFIRM_ACTIONS, ERRORS_MESSAGE
from hgw_frontend.models import FlowRequest, ConfirmationCode, ConsentConfirmation, Destination, Channel
from hgw_frontend.serializers import FlowRequestSerializer, ChannelSerializer
from hgw_frontend.settings import CONSENT_MANAGER_CLIENT_ID, CONSENT_MANAGER_CLIENT_SECRET, CONSENT_MANAGER_URI, \
    KAFKA_TOPIC, KAFKA_BROKER, HGW_BACKEND_URI, KAFKA_CLIENT_KEY, KAFKA_CLIENT_CERT, KAFKA_CA_CERT, \
    CONSENT_MANAGER_CONFIRMATION_PAGE, HGW_BACKEND_CLIENT_ID, HGW_BACKEND_CLIENT_SECRET, TIME_ZONE, KAFKA_SSL

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

    def list(self, request):
        if request.auth.application.is_super_client():
            flow_requests = FlowRequest.objects.all()
        else:
            flow_requests = FlowRequest.objects.filter(destination=request.auth.application.destination)
        serializer = FlowRequestSerializer(flow_requests, many=True)
        return Response(serializer.data)

    def create(self, request):
        logger.debug(request.scheme)
        if 'flow_id' not in request.data or \
                xor(('start_validity' not in request.data), ('expire_validity' not in request.data)):
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
        data = {
            'flow_id': request.data['flow_id'],
            'process_id': get_random_string(32),
            'status': FlowRequest.PENDING,
            'profile': request.data['profile'] if 'profile' in request.data else None,
            'destination': request.auth.application.destination.pk
        }
        if 'start_validity' not in request.data and 'expire_validity' not in request.data:
            # Assign default values for the validity range: current datetime + 6 months
            start_datetime = datetime.datetime.now(gettz(TIME_ZONE))
            expire_datetime = start_datetime + datetime.timedelta(days=180)
            data['start_validity'] = start_datetime.strftime(TIME_FORMAT)
            data['expire_validity'] = expire_datetime.strftime(TIME_FORMAT)
        else:
            data['start_validity'] = request.data['start_validity']
            data['expire_validity'] = request.data['expire_validity']

        fr_serializer = FlowRequestSerializer(data=data)
        if fr_serializer.is_valid():
            try:
                fr = fr_serializer.save()
            except IntegrityError as e:
                logger.debug("Integrity error adding FR with data: %s\nDetails: %s",fr_serializer.data, e)
                return Response(ERRORS_MESSAGE['INVALID_DATA'], status=status.HTTP_400_BAD_REQUEST)
            cc = ConfirmationCode.objects.create(flow_request=fr)
            cc.save()
            res = {k: v for k, v in six.iteritems(fr_serializer.data)}
            res.update({'confirm_id': cc.code})

            return Response(res, status=status.HTTP_201_CREATED)
        else:
            logger.error("Error adding Flow Request with data %s. Details %s", data, fr_serializer.errors)
        return Response(ERRORS_MESSAGE['INVALID_DATA'], status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, process_id, format=None):
        fr = self.get_flow_request(request, process_id)
        fr.status = FlowRequest.DELETE_REQUESTED
        fr.save()

        cc = ConfirmationCode.objects.create(flow_request=fr)
        cc.save()
        res = {'confirm_id': cc.code}

        return Response(res, status=status.HTTP_202_ACCEPTED)

    def retrieve(self, request, process_id, format=None):
        fr = self.get_flow_request(request, process_id)
        serializer = FlowRequestSerializer(fr)
        res = {k: v for k, v in six.iteritems(serializer.data) if k != 'destination'}
        return Response(res)

    def search(self, request):
        if 'channel_id' in request.GET:
            try:
                consent_confirmation = ConsentConfirmation.objects.get(consent_id=request.GET['channel_id'])
                flow_request = consent_confirmation.flow_request
                serializer = FlowRequestSerializer(instance=flow_request)
            except ConsentConfirmation.DoesNotExist:
                return Response({}, status.HTTP_404_NOT_FOUND)
            return Response(serializer.data)
        else:
            return Response({}, status.HTTP_400_BAD_REQUEST)


def _get_backend_session():
    return OAuth2SessionProxy('{}/oauth2/token/'.format(HGW_BACKEND_URI),
                              HGW_BACKEND_CLIENT_ID,
                              HGW_BACKEND_CLIENT_SECRET)


def _get_consent_session():
    return OAuth2SessionProxy('{}/oauth2/token/'.format(CONSENT_MANAGER_URI),
                              CONSENT_MANAGER_CLIENT_ID,
                              CONSENT_MANAGER_CLIENT_SECRET)


def _create_channels(flow_request, destination_endpoint_callback_url, user):
    destination = flow_request.destination

    try:
        oauth_backend_session = _get_backend_session()
    except InvalidClientError:
        logger.error("Invalid oAuth2 client contacting the backend")
        return [], ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']
    except requests.exceptions.ConnectionError:
        logger.error("Backend connection error while getting an oAuth2 tokern")
        return [], ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']
    else:
        sources = oauth_backend_session.get('{}/v1/sources/'.format(HGW_BACKEND_URI))

    try:
        oauth_consent_session = _get_consent_session()
    except InvalidClientError:
        logger.error("Invalid oAuth2 client contacting the consent manager")
        return [], ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']
    except requests.exceptions.ConnectionError:
        logger.error("Consent Manager connection error while getting an oAuth2 tokern")
        return [], ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']

    confirm_ids = []
    for source_data in sources.json():
        channel = Channel.objects.create(channel_id=get_random_string(32), flow_request=flow_request,
                                         source_id=source_data['source_id'])
        channel.save()

        consent_data = {
            'source': {
                'id': source_data['source_id'],
                'name': source_data['name']
            },
            'destination': {
                'id': destination.destination_id,
                'name': destination.name
            },
            'profile': source_data['profile'],
            'person_id': user.fiscalNumber,
            'start_validity': flow_request.start_validity.strftime(TIME_FORMAT),
            'expire_validity': flow_request.expire_validity.strftime(TIME_FORMAT)
        }

        res = oauth_consent_session.post('{}/v1/consents/'.format(CONSENT_MANAGER_URI), json=consent_data)
        json_res = res.json()
        if res.status_code == 201:
            ConsentConfirmation.objects.create(flow_request=flow_request, consent_id=json_res['consent_id'],
                                               confirmation_id=json_res['confirm_id'],
                                               destination_endpoint_callback_url=destination_endpoint_callback_url)
            confirm_ids.append(json_res['confirm_id'])
        else:
            logger.info('Consent not created. Response is: %s, %s', res.status_code, res.content)
    if not confirm_ids:
        return confirm_ids, ERRORS_MESSAGE['ALL_CONSENTS_ALREADY_CREATED']
    return confirm_ids, ""


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
    oauth_consent_session = _get_consent_session()
    res = oauth_consent_session.get('{}/v1/consents/{}/'.format(CONSENT_MANAGER_URI, consent_id))
    return consent_confirmation, res.json()


def _get_callback_url(request):
    """
    Return the URL to confirm a flow request
    :param request:
    :return:
    """
    callback_url = '{}://{}/v1/flow_requests/consents_confirmed/'.format('https', request.get_host())
    logger.debug("Callback url {}".format(callback_url))
    return callback_url


def _ask_consent(request, flow_request, destination_callback_url):
    consents, error = _create_channels(flow_request, destination_callback_url, request.user)

    if error:
        return HttpResponseRedirect('{}?process_id={}&success={}&error={}'.format( 
            destination_callback_url, flow_request.process_id, json.dumps(False), error))

    logger.debug("Created consent")
    consent_callback_url = _get_callback_url(request)
    return HttpResponseRedirect('{}?{}&callback_url={}'.
                                format(CONSENT_MANAGER_CONFIRMATION_PAGE,
                                       '&'.join(['confirm_id={}'.format(consent) for consent in consents]),
                                       consent_callback_url))


def _confirm(request, consent_confirm_id):
    try:
        logger.debug("Getting consent from Consent Manager")
        consent_confirmation, consent = _get_consent(consent_confirm_id)
        logger.debug("Found consent")
    except UnknownConsentConfirmation:
        return False

    if consent['status'] == 'AC':
        logger.debug("Consent status is AC. Sending message to KAFKA")
        if KAFKA_SSL:
            producer_params = {
                'bootstrap_servers': KAFKA_BROKER,
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': KAFKA_CA_CERT,
                'ssl_certfile': KAFKA_CLIENT_CERT,
                'ssl_keyfile': KAFKA_CLIENT_KEY
            }
        else:
            producer_params = {
                'bootstrap_servers': KAFKA_BROKER
            }
        kp = KafkaProducer(**producer_params)

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
    logger.debug("Scheme: %s", request.scheme)
    logger.debug("User: %s", request.user.fiscalNumber)
    if not request.user.fiscalNumber:
        return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PERSON_ID'])
    try:
        logger.debug('request.GET.keys() %s', request.GET.keys())
        fr_confirm_code = request.GET['confirm_id']
        fr_callback_url = request.GET['callback_url']
        action = request.GET['action']
    except KeyError:
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
                    if fr.status == FlowRequest.PENDING:
                        fr.person_id = request.user.fiscalNumber
                        fr.save()
                        return _ask_consent(request, fr, fr_callback_url)
                    else:
                        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_FR_STATUS'])
                else:
                    if fr.status == FlowRequest.DELETE_REQUESTED:
                        fr.delete()
                        return HttpResponseRedirect(fr_callback_url)
                    else:
                        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_FR_STATUS'])
