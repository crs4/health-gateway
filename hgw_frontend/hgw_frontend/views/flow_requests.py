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

import requests
import six
from dateutil.tz import gettz
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, IntegrityError
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from oauthlib.oauth2 import InvalidClientError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from hgw_common.models import OAuth2SessionProxy
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import ERRORS
from hgw_common.utils.authorization import TokenHasResourceDetailedScope
from hgw_frontend import CONFIRM_ACTIONS, ERRORS_MESSAGE
from hgw_frontend.models import (Channel, ConfirmationCode,
                                 ConsentConfirmation, FlowRequest, Source)
from hgw_frontend.serializers import (ChannelSerializer, FlowRequestSerializer,
                                      SourceSerializer)
from hgw_frontend.settings import (CONSENT_MANAGER_CLIENT_ID,
                                   CONSENT_MANAGER_CLIENT_SECRET,
                                   CONSENT_MANAGER_CONFIRMATION_PAGE,
                                   CONSENT_MANAGER_URI, HGW_BACKEND_CLIENT_ID,
                                   HGW_BACKEND_CLIENT_SECRET, HGW_BACKEND_URI,
                                   TIME_ZONE)

logger = logging.getLogger('hgw_frontend.flow_request')
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class UnknownConsentConfirmation(Exception):
    pass


class FlowRequestView(ViewSet):
    """
    Class with REST views for /flow_requests/ API
    """
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
            logger.warning("Flow request not found")
            raise Http404

    def list(self, request):
        """
        REST function to get all FlowRequests
        """
        if request.auth.application.is_super_client():
            flow_requests = FlowRequest.objects.all()
        else:
            flow_requests = FlowRequest.objects.filter(destination=request.auth.application.destination)
        serializer = FlowRequestSerializer(flow_requests, many=True)
        return Response(serializer.data, headers={'X-Total-Count': flow_requests.count()})

    def create(self, request):
        """
        REST function to create a FlowRequest
        """
        if 'flow_id' not in request.data or \
                xor(('start_validity' not in request.data), ('expire_validity' not in request.data)):
            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

        # We get the sources. If the client specified a subset it checks if it's correct,
        # otherwise it gets all the sources from backend
        logger.info("Received create flow_request request")
        if 'sources' in request.data:
            logger.info("Required flow request only for sources %s", request.data['sources'])
            sources = Source.objects.filter(source_id__in=[s['source_id'] for s in request.data['sources']])
        else:
            sources = Source.objects.all()
            logger.info("Source(s) not specified. Using all available sources")

        if not sources:
            return Response({'errors': [ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        sources_serializer = SourceSerializer(sources, many=True)
        data = {
            'flow_id': request.data['flow_id'],
            'process_id': get_random_string(32),
            'status': FlowRequest.PENDING,
            'profile': request.data['profile'] if 'profile' in request.data else None,
            'destination': request.auth.application.destination.pk,
            'sources': sources_serializer.data
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
                flow_request = fr_serializer.save()
            except IntegrityError as ex:
                logger.debug("Integrity error adding FR with data: %s\nDetails: %s", fr_serializer.data, ex)
                return Response(ERRORS_MESSAGE['INVALID_DATA'], status=status.HTTP_400_BAD_REQUEST)
            cc = ConfirmationCode.objects.create(flow_request=flow_request)
            cc.save()
            res = {k: v for k, v in six.iteritems(fr_serializer.data)}
            res.update({'confirm_id': cc.code})

            return Response(res, status=status.HTTP_201_CREATED)

        logger.error("Error adding Flow Request with data %s. Details %s", data, fr_serializer.errors)
        return Response(ERRORS_MESSAGE['INVALID_DATA'], status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, process_id, format=None):
        """
        REST function to delete a FlowRequest
        """
        flow_request = self.get_flow_request(request, process_id)
        flow_request.status = FlowRequest.DELETE_REQUESTED
        flow_request.save()

        cc = ConfirmationCode.objects.create(flow_request=flow_request)
        cc.save()
        res = {'confirm_id': cc.code}

        return Response(res, status=status.HTTP_202_ACCEPTED)

    def retrieve(self, request, process_id, format=None):
        """
        REST function to get one FlowRequest
        """
        flow_request = self.get_flow_request(request, process_id)
        serializer = FlowRequestSerializer(flow_request)
        res = {k: v for k, v in six.iteritems(serializer.data) if k != 'destination'}
        return Response(res)

    def channels(self, request, process_id):
        """
        Returns a list of Channels belonging to the FlowRequest identified by :param:`process_id`
        """
        logger.info("Requested channels for flow_request %s", process_id)
        flow_request = self.get_flow_request(request, process_id)
        if 'status' in request.GET:
            if request.GET['status'] not in list(zip(*Channel.STATUS_CHOICES))[0]:
                return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
            channels = Channel.objects.filter(flow_request=flow_request, status=request.GET['status'])
        else:
            channels = Channel.objects.filter(flow_request=flow_request)
        count = channels.count()
        if count == 0:
            raise Http404
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data, headers={'X-Total-Count': count})

    def search(self, request):
        """
        REST function to search FlowRequest by channel id
        """
        if 'channel_id' in request.GET:
            try:
                channel = Channel.objects.get(channel_id=request.GET['channel_id'])
                flow_request = channel.flow_request
                serializer = FlowRequestSerializer(instance=flow_request)
            except Channel.DoesNotExist:
                raise Http404
            return Response(serializer.data, headers={'X-Total-Count': '1'})
        else:
            return Response({'errors': ['missing_parameter']}, status.HTTP_400_BAD_REQUEST)


def _get_backend_session():
    return OAuth2SessionProxy('{}/oauth2/token/'.format(HGW_BACKEND_URI),
                              HGW_BACKEND_CLIENT_ID,
                              HGW_BACKEND_CLIENT_SECRET)


def _get_consent_session():
    return OAuth2SessionProxy('{}/oauth2/token/'.format(CONSENT_MANAGER_URI),
                              CONSENT_MANAGER_CLIENT_ID,
                              CONSENT_MANAGER_CLIENT_SECRET)


def _create_consents(flow_request, destination_endpoint_callback_url, user):
    destination = flow_request.destination
    sources = flow_request.sources.all()
    try:
        oauth_consent_session = _get_consent_session()
    except InvalidClientError:
        logger.error("Invalid oAuth2 client contacting the consent manager")
        return [], ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']
    except requests.exceptions.ConnectionError:
        logger.error("Consent Manager connection error while getting an oAuth2 tokern")
        return [], ERRORS_MESSAGE['INTERNAL_GATEWAY_ERROR']

    confirm_ids = []
    connection_errors = 0
    for source in sources:
        channel = Channel.objects.create(channel_id=get_random_string(32), flow_request=flow_request,
                                         source=source, status=Channel.CONSENT_REQUESTED)
        channel.save()

        consent_data = {
            'source': {
                'id': source.source_id,
                'name': source.name
            },
            'destination': {
                'id': destination.destination_id,
                'name': destination.name
            },
            'profile': ProfileSerializer(source.profile).data,
            'person_id': user.fiscalNumber,
            'start_validity': flow_request.start_validity.strftime(TIME_FORMAT),
            'expire_validity': flow_request.expire_validity.strftime(TIME_FORMAT)
        }
        logger.info("Creating consent with data %s", consent_data)
        res = oauth_consent_session.post('{}/v1/consents/'.format(CONSENT_MANAGER_URI), json=consent_data)
        if res is not None:
            json_res = res.json()
            if res.status_code == 201:
                ConsentConfirmation.objects.create(flow_request=flow_request, consent_id=json_res['consent_id'],
                                                   channel=channel, confirmation_id=json_res['confirm_id'],
                                                   destination_endpoint_callback_url=destination_endpoint_callback_url)
                confirm_ids.append(json_res['confirm_id'])
            else:
                logger.error('Consent not created. Response is: %s, %s', res.status_code, res.content)
        else:
            connection_errors += 1
            logger.error('Consent not created. Error occurred contacting the consent manager')
    if not confirm_ids:
        return confirm_ids, ERRORS_MESSAGE['ALL_CONSENTS_ALREADY_CREATED']
    return confirm_ids, ""


def _get_consent(confirm_id):
    """
    Query the consent manager for the consent with confirmation_id equal to confirm_id
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
    logger.debug("Callback url %s", callback_url)
    return callback_url


def _ask_consent(request, flow_request, destination_callback_url):
    consents, error = _create_consents(flow_request, destination_callback_url, request.user)

    if error:
        return HttpResponseRedirect('{}?process_id={}&success={}&error={}'.format(
            destination_callback_url, flow_request.process_id, json.dumps(False), error))

    logger.debug("Created consent")
    consent_callback_url = _get_callback_url(request)
    return HttpResponseRedirect('{}?{}&callback_url={}'.
                                format(CONSENT_MANAGER_CONFIRMATION_PAGE,
                                       '&'.join(['confirm_id={}'.format(consent) for consent in consents]),
                                       consent_callback_url))


def _confirm(consent_confirm_id):
    result = False
    try:
        logger.debug("Getting consent from Consent Manager")
        consent_confirmation, consent = _get_consent(consent_confirm_id)
        logger.debug("Found consent")
    except UnknownConsentConfirmation:
        return result

    flow_request = consent_confirmation.flow_request
    if consent['status'] == 'AC':
        logger.debug("Consent Accepted")
        flow_request.status = FlowRequest.ACTIVE
        flow_request.save()
        result = True
    if consent['status'] == 'NV':
        logger.debug("Consent Invalid, it must have been Aborted")
        flow_request.status = FlowRequest.DELETE_REQUESTED
        flow_request.save()
    return result


@require_GET
@login_required
def consents_confirmed(request):
    consent_confirm_ids = request.GET.getlist('consent_confirm_id')
    success = json.loads(request.GET['success'])
    if 'status' in request.GET:
        state = request.GET['status']
    else:
        state = 'failed'

    flow_requests = FlowRequest.objects.filter(consentconfirmation__confirmation_id__in=consent_confirm_ids) \
        .distinct()
    if flow_requests.count() != 1:
        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_DATA'])
    flow_request = flow_requests[0]
    logger.debug("Flow request found")
    callback = flow_request.consentconfirmation_set.all()[0].destination_endpoint_callback_url

    output_success = False
    if success or state == 'aborted':
        for consent_confirm_id in consent_confirm_ids:
            logger.debug("Checking consents")
            # This looks naive, but we just want to switch to true if we did something at least on one consent
            if _confirm(consent_confirm_id):
                output_success = True
                state = 'ok'

    if state == 'aborted':
        for ch in Channel.objects.filter(flow_request=flow_request).all():
            logger.debug("Marking channels as aborted")
            ch.status = Channel.CONSENT_ABORTED
            ch.save()

    return HttpResponseRedirect('{}?process_id={}&success={}&status={}'.format(
        callback, flow_request.process_id, json.dumps(output_success), state))


@require_GET
@login_required
def confirm_request(request):
    if not request.user.fiscalNumber:
        return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PERSON_ID'])
    try:
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
                flow_request = cc.flow_request
                if action == CONFIRM_ACTIONS[0]:
                    if flow_request.status == FlowRequest.PENDING:
                        flow_request.person_id = request.user.fiscalNumber
                        flow_request.save()
                        return _ask_consent(request, flow_request, fr_callback_url)
                    else:
                        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_FR_STATUS'])
                else:
                    if flow_request.status == FlowRequest.DELETE_REQUESTED:
                        flow_request.delete()
                        return HttpResponseRedirect(fr_callback_url)
                    else:
                        return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_FR_STATUS'])
