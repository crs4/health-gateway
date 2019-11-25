# Copyright (consent) 2017-2018 CRS4
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
"""
Views for consents functionalities
"""

import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from rest_framework import status as http_status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from consent_manager import serializers
from consent_manager.models import ConfirmationCode, Consent
from consent_manager.serializers import ConsentSerializer
from consent_manager.settings import KAFKA_NOTIFICATION_TOPIC, USER_ID_FIELD
from hgw_common.messaging.sender import SendingError, create_sender
from hgw_common.utils import ERRORS, create_broker_parameters_from_settings
from hgw_common.utils.authorization import \
    IsAuthenticatedOrTokenHasResourceDetailedScope

logger = logging.getLogger('consent_manager.views')


class ConsentView(ViewSet):
    """
    Viewset with REST function of /v1/consents API and some GUI views
    """
    permission_classes = (IsAuthenticatedOrTokenHasResourceDetailedScope,)
    oauth_views = ['list', 'create', 'retrieve']
    required_scopes = ['consent']

    def __init__(self, *args, **kwargs):
        self._sender = None
        super(ConsentView, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_consent(consent_id):
        try:
            return Consent.objects.get(consent_id=consent_id)
        except Consent.DoesNotExist:
            raise Http404

    @staticmethod
    def _get_person_id(request):
        return getattr(request.user, USER_ID_FIELD)

    def _send_changes(self, consent):
        """
        Method to send consent changes. If the sender is None it gets one
        """
        if self._sender is None:
            self._sender = create_sender(create_broker_parameters_from_settings())
        consent_serializer = ConsentSerializer(consent)
        if self._sender.send(KAFKA_NOTIFICATION_TOPIC, consent_serializer.data):
            logger.info('Action on consent notified correctly')

    def list(self, request):
        """
        Returns the list of the consents. If the request arrives from
        an authenticated user (i.e.. from the GUI) it returns only the
        consents belonging to him. Otherwise all consents
        """
        if request.user is not None:
            person_id = self._get_person_id(request)
            consents = Consent.objects.filter(person_id=person_id,
                                              status__in=(Consent.ACTIVE, Consent.REVOKED))
            logger.info('Found %s consents for user %s', len(consents), person_id)
        else:
            consents = Consent.objects.all()
        serializer = serializers.ConsentSerializer(consents, many=True)
        if request.user is not None or request.auth.application.is_super_client():
            return Response(serializer.data)

        res = []
        for consent in serializer.data:
            res.append({
                'consent_id': consent['consent_id'],
                'source': consent['source'],
                'status': consent['status'],
                'start_validity': consent['start_validity'],
                'expire_validity': consent['expire_validity']
            })
        return Response(res)

    @staticmethod
    def create(request):
        """
        REST API to create a new consent (i.e., it implements the POST function)
        """
        logger.debug(request.scheme)
        request.data.update({
            'consent_id': get_random_string(32),
            'status': Consent.PENDING
        })
        serializer = serializers.ConsentSerializer(data=request.data)
        if serializer.is_valid():
            consent = serializer.save()
            confirmation_code = ConfirmationCode.objects.create(consent=consent)
            confirmation_code.save()
            res = {'confirm_id': confirmation_code.code,
                   'consent_id': consent.consent_id}

            return Response(res, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def update(self, request, consent_id):
        """
        REST function to update a consent
        """
        logger.info('Received update request for consent with id %s', consent_id)
        consent = self._get_consent(consent_id)
        if consent.status != Consent.ACTIVE:
            logger.info('Consent is not ACTIVE. Not updated')
            return Response({'errors': ['wrong_consent_status']}, status=http_status.HTTP_400_BAD_REQUEST)
        elif consent.person_id != self._get_person_id(request):
            logger.warning('Consent doesn\'t belong to the logged in person so it has not been changed')
            return Response({'errors': ['wrong_person']}, status=http_status.HTTP_400_BAD_REQUEST)

        logger.info('Update data: %s', request.data)
        serializer = serializers.ConsentSerializer(consent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            self._send_changes(consent)
        else:
            logger.info('Update data are not valid. Errors are: %s', serializer.errors)
            return Response({'errors': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return Response({}, status=http_status.HTTP_200_OK)

    def retrieve(self, request, consent_id, format=None):
        """
        REST function to GET only one consent
        """
        consent = self._get_consent(consent_id)
        serializer = serializers.ConsentSerializer(consent)
        if request.auth.application.is_super_client():
            return Response(serializer.data)
        else:
            res = {
                'consent_id': serializer.data['consent_id'],
                'source': serializer.data['source'],
                'status': serializer.data['status'],
                'start_validity': serializer.data['start_validity'],
                'expire_validity': serializer.data['expire_validity']
            }
            return Response(res)

    def _revoke_consent(self, consent_id, person_id, raise_exc=False):
        try:
            consent = self._get_consent(consent_id)
        except Http404:
            if raise_exc:
                raise
            else:
                return http_status.HTTP_404_NOT_FOUND, {'errors': ['wrong_consent_status']}
        if consent.status != Consent.ACTIVE:
            logger.info('Consent is not ACTIVE. Not revoked')
            return http_status.HTTP_400_BAD_REQUEST, {'errors': ['wrong_consent_status']}
        elif consent.person_id != person_id:
            logger.warning('Consent not of the logged in person so it is not revoked')
            return http_status.HTTP_400_BAD_REQUEST, {'errors': ['wrong_person']}
        else:
            logger.info('Consent revoked')
            consent.status = Consent.REVOKED
            consent.save()
            self._send_changes(consent)

            return http_status.HTTP_200_OK, {}

    def revoke_list(self, request):
        """
        Revokes a list of consents
        """
        try:
            consents = request.data['consents']
        except KeyError:
            return Response({'errors': [ERRORS.MISSING_PARAMETERS]}, http_status.HTTP_400_BAD_REQUEST)
        logger.info('Received consents revoke request for consents %s', ', '.join(consents))

        revoked = []
        failed = []
        person_id = self._get_person_id(request)
        for consent_id in consents:
            logger.info('Revoking consent %s', consent_id)
            status, _ = self._revoke_consent(consent_id, person_id)
            if status == http_status.HTTP_200_OK:
                revoked.append(consent_id)
            else:
                failed.append(consent_id)
        return Response({'revoked': revoked, 'failed': failed}, status=http_status.HTTP_200_OK)

    def revoke(self, request, consent_id):
        """
        Revoke a consent
        """
        logger.info('Received consent revoke request for consent %s', consent_id)
        status, res = self._revoke_consent(consent_id, self._get_person_id(request), raise_exc=True)
        return Response(res, status)

    @staticmethod
    def find(request):
        """
        Method to find consent. The only supported query parameter is by confirmation_id
        :param request:
        :return:
        """
        if 'confirm_id' not in request.query_params:
            logger.debug('confirm_id paramater not present')
            return Response({'errors': [ERRORS.MISSING_PARAMETERS]}, http_status.HTTP_400_BAD_REQUEST)

        confirm_ids = request.GET.getlist('confirm_id')
        logger.info('Called /v1/consents/find/ with query paramaters %s', request.query_params)
        confirmation_codes = ConfirmationCode.objects.filter(code__in=confirm_ids, consent__status=Consent.PENDING)
        if not confirmation_codes:
            return Response({}, http_status.HTTP_404_NOT_FOUND)
        logger.debug('Found %s consents', len(confirmation_codes))
        logger.debug('Checking validity')
        consents = []
        for code in confirmation_codes:
            if code.check_validity():
                serializer = serializers.ConsentSerializer(code.consent)
                consent_data = serializer.data.copy()
                consent_data.update({'confirm_id': code.code})
                del consent_data['consent_id']
                consents.append(consent_data)
        logger.info('Found %s valid consents', len(consents))
        return Response(consents, status=http_status.HTTP_200_OK)

    def confirm(self, request):
        """
        View to confirm consents
        """
        logger.info('Received consent confirmation request from user')
        if 'consents' not in request.data:
            logger.info('Missing the consents query params. Returning error')
            return Response({'errors': [ERRORS.MISSING_PARAMETERS]}, http_status.HTTP_400_BAD_REQUEST)

        consents = request.data['consents']
        logger.info('Specified the following consents: %s', ', '.join(consents.keys()))

        confirmed = []
        failed = []
        for confirm_id, consent_data in consents.items():
            try:
                confirmation_code = ConfirmationCode.objects.get(code=confirm_id)
            except ConfirmationCode.DoesNotExist:
                logger.info('Consent associated to confirm_id %s not found', confirm_id)
                failed.append(confirm_id)
            else:
                if not confirmation_code.check_validity():
                    logger.info('Confirmation expired')
                    failed.append(confirm_id)
                else:
                    consent = confirmation_code.consent
                    logger.info('consent_id is %s', consent.consent_id)
                    if consent.status != Consent.PENDING:
                        logger.info('consent not in PENDING http_status. Cannot confirm it')
                        failed.append(confirm_id)
                    elif consent.person_id != self._get_person_id(request):
                        logger.info('consent found but it does not belong to the logged user. Cannot confirm it')
                        failed.append(confirm_id)
                    else:
                        consent.status = Consent.ACTIVE
                        consent.confirmed = datetime.now()
                        if 'start_validity' in consent_data:
                            consent.start_validity = consent_data['start_validity']
                        if 'expire_validity' in consent_data:
                            consent.expire_validity = consent_data['expire_validity']
                        consent.save()
                        confirmed.append(confirm_id)
                        logger.info('consent with id %s confirmed', consent)

                        try:
                            self._send_changes(consent)
                            logger.info("Consent creation notified correctly")
                        except SendingError:
                            # TODO: we should retry to send the frontend
                            logger.error("It was impossible to send the message to the HGW Frontend")

        return Response({'confirmed': confirmed, 'failed': failed}, status=http_status.HTTP_200_OK)

    def abort(self, request):
        """
        View to abort consents
        """
        logger.info('Received consent to abort request from user')
        if 'consents' not in request.data:
            logger.info('Missing the consents query params. Returning error')
            return Response({'errors': [ERRORS.MISSING_PARAMETERS]}, http_status.HTTP_400_BAD_REQUEST)

        consents = request.data['consents']
        logger.info('Specified the following consents: %s', ', '.join(consents.keys()))

        confirmed = []
        failed = []
        for confirm_id, consent_data in consents.items():
            try:
                confirmation_code = ConfirmationCode.objects.get(code=confirm_id)
            except ConfirmationCode.DoesNotExist:
                logger.info('Consent associated to confirm_id %s not found', confirm_id)
                failed.append(confirm_id)
            else:
                if not confirmation_code.check_validity():
                    logger.info('Confirmation expired')
                    failed.append(confirm_id)
                else:
                    consent = confirmation_code.consent
                    logger.info('consent_id is %s', consent.consent_id)
                    if consent.status != Consent.PENDING:
                        logger.info('consent not in PENDING http_status. Cannot abort it')
                        failed.append(confirm_id)
                    elif consent.person_id != self._get_person_id(request):
                        logger.info('consent found but it does not belong to the logged user. Cannot abort it')
                        failed.append(confirm_id)
                    else:
                        consent.status = Consent.NOT_VALID
                        consent.confirmed = datetime.now()
                        # if 'start_validity' in consent_data:
                        #     consent.start_validity = consent_data['start_validity']
                        # if 'expire_validity' in consent_data:
                        #     consent.expire_validity = consent_data['expire_validity']
                        consent.save()
                        confirmed.append(confirm_id)
                        logger.info('consent with id %s aborted', consent)

                        try:
                            self._send_changes(consent)
                            logger.info("Consent creation notified correctly")
                        except SendingError:
                            # TODO: we should retry to send the frontend
                            logger.error("It was impossible to send the message to the HGW Frontend")

        return Response({'confirmed': confirmed, 'failed': failed}, status=http_status.HTTP_200_OK)

@require_http_methods(["GET", "POST"])
@login_required
def confirm_consent(request):
    """
    View for consent confirmation
    """
    return render(request, 'index.html', context={'nav_bar': True})
