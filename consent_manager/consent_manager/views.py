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

from consent_manager import serializers, ERRORS_MESSAGE
from consent_manager.models import Consent, ConfirmationCode
from consent_manager.settings import USER_ID_FIELD
from hgw_common.utils import IsAuthenticatedOrTokenHasResourceDetailedScope, get_logger

logger = get_logger('consent_manager')


class ConsentView(ViewSet):
    permission_classes = (IsAuthenticatedOrTokenHasResourceDetailedScope,)
    oauth_views = ['list', 'create', 'retrieve']
    required_scopes = ['consent']

    @staticmethod
    def _get_consent(consent_id):
        return get_object_or_404(Consent, consent_id=consent_id)

    @staticmethod
    def _get_person_id(request):
        return getattr(request.user, USER_ID_FIELD)

    def list(self, request):
        if request.user is not None:
            person_id = self._get_person_id(request)
            consents = Consent.objects.filter(person_id=person_id,
                                              status__in=(Consent.ACTIVE, Consent.REVOKED))
            logger.info('Found {} consents for user {}'.format(len(consents), person_id))
        else:
            consents = Consent.objects.all()
        serializer = serializers.ConsentSerializer(consents, many=True)
        if request.user is not None or request.auth.application.is_super_client():
            return Response(serializer.data)
        else:
            res = []
            for c in serializer.data:
                res.append({
                    'consent_id': c['consent_id'],
                    'source': c['source'],
                    'status': c['status'],
                    'start_validity': c['start_validity'],
                    'expire_validity': c['expire_validity']
                })
            return Response(res)

    def create(self, request):
        logger.debug(request.scheme)
        request.data.update({
            'consent_id': get_random_string(32),
            'status': Consent.PENDING
        })
        serializer = serializers.ConsentSerializer(data=request.data)
        if serializer.is_valid():
            co = serializer.save()
            cc = ConfirmationCode.objects.create(consent=co)
            cc.save()
            res = {'confirm_id': cc.code,
                   'consent_id': co.consent_id}

            return Response(res, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def update(self, request, consent_id):
        logger.info('Received update request for consent with id {}'.format(consent_id))
        consent = self._get_consent(consent_id)
        if consent.status != Consent.ACTIVE:
            logger.info('Consent is not ACTIVE. Not revoked')
            return Response({'errors': ['wrong_consent_status']}, status=http_status.HTTP_400_BAD_REQUEST)
        elif consent.person_id != self._get_person_id(request):
            logger.warn('Consent doesn\'t belong to the logged in person so it is not revoked')
            return Response({'errors': ['wrong_person']}, status=http_status.HTTP_400_BAD_REQUEST)

        serializer = serializers.ConsentSerializer(consent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
        else:
            logger.info('Update data are not valid. Errors are: {}'.format(serializer.errors))
            return Response({'errors': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return Response({}, status=http_status.HTTP_200_OK)

    def retrieve(self, request, consent_id, format=None):
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
            c = self._get_consent(consent_id)
        except Http404:
            if raise_exc:
                raise
            else:
                return http_status.HTTP_404_NOT_FOUND, {'error': 'wrong_consent_status'}
        if c.status != Consent.ACTIVE:
            logger.info('Consent is not ACTIVE. Not revoked')
            return http_status.HTTP_400_BAD_REQUEST, {'error': 'wrong_consent_status'}
        elif c.person_id != person_id:
            logger.warn('Consent not of the logged in person so it is not revoked')
            return http_status.HTTP_400_BAD_REQUEST, {'error': 'wrong_person'}
        else:
            logger.info('Consent revoked')
            c.status = Consent.REVOKED
            c.save()
            return http_status.HTTP_200_OK, {}

    def revoke_list(self, request):
        try:
            consents = request.data['consents']
        except KeyError:
            return Response({'error': 'missing_parameters'}, http_status.HTTP_400_BAD_REQUEST)
        logger.info('Received consents revoke request for consents {}'.format(', '.join(consents)))

        revoked = []
        failed = []
        person_id = self._get_person_id(request)
        for consent_id in consents:
            logger.info('Revoking consent {}'.format(consent_id))
            status, res = self._revoke_consent(consent_id, person_id)
            if status == http_status.HTTP_200_OK:
                revoked.append(consent_id)
            else:
                failed.append(consent_id)
        return Response({'revoked': revoked, 'failed': failed}, status=http_status.HTTP_200_OK)

    def revoke(self, request, consent_id):
        logger.info('Received consent revoke request for consent {}'.format(consent_id))
        status, res = self._revoke_consent(consent_id, self._get_person_id(request), raise_exc=True)
        return Response(res, status)

    def find(self, request):
        """
        Method to find consent. The only supported query parameter is by confirmation_id
        :param request:
        :return:
        """
        if 'confirm_id' not in request.query_params:
            logger.debug('confirm_id paramater not present')
            return Response({'error': ERRORS_MESSAGE['MISSING_PARAM']}, http_status.HTTP_400_BAD_REQUEST)

        confirm_ids = request.GET.getlist('confirm_id')
        logger.info('Called /v1/consents/find/ with query paramaters {}'.format(request.query_params))
        ccs = ConfirmationCode.objects.filter(code__in=confirm_ids, consent__status=Consent.PENDING)
        if not ccs:
            return Response({}, http_status.HTTP_404_NOT_FOUND)
        logger.debug('Found {} consents'.format(len(ccs)))
        logger.debug('Checking validity'.format(len(ccs)))
        consents = []
        for cc in ccs:
            if cc.check_validity():
                serializer = serializers.ConsentSerializer(cc.consent)
                consent_data = serializer.data.copy()
                consent_data.update({'confirm_id': cc.code})
                del consent_data['consent_id']
                consents.append(consent_data)
        logger.info('Found {} valid consents'.format(len(consents)))
        return Response(consents, status=http_status.HTTP_200_OK)

    def confirm(self, request):
        logger.info('Received consent confirmation request')
        if 'consents' not in request.data:
            logger.info('Missing the consents query params. Returning error')
            return Response({'error': 'missing_parameters'}, http_status.HTTP_400_BAD_REQUEST)

        consents = request.data['consents']
        logger.info('Specified the following consents: {}'.format(', '.join(consents.keys())))

        confirmed = []
        failed = []
        for confirm_id, consent_data in consents.items():
            try:
                cc = ConfirmationCode.objects.get(code=confirm_id)
            except ConfirmationCode.DoesNotExist:
                logger.info('Consent associated to confirm_id {} not found'.format(confirm_id))
                failed.append(confirm_id)
            else:
                if not cc.check_validity():
                    logger.info('Confirmation expired'.format(confirm_id))
                    failed.append(confirm_id)
                else:
                    c = cc.consent
                    logger.info('consent_id is {}'.format(c.consent_id))
                    if c.status != Consent.PENDING:
                        logger.info('consent not in PENDING http_status. Cannot confirm it')
                        failed.append(confirm_id)
                    elif c.person_id != self._get_person_id(request):
                        logger.info('consent found but it is not of the logged user. Cannot confirm it')
                        failed.append(confirm_id)
                    else:
                        c.status = Consent.ACTIVE
                        c.confirmed = datetime.now()
                        if 'start_validity' in consent_data:
                            c.start_validity = consent_data['start_validity']
                        if 'expire_validity' in consent_data:
                            c.expire_validity = consent_data['expire_validity']
                        c.save()
                        confirmed.append(confirm_id)
                        logger.info('consent with id {} confirmed'.format(c))
        return Response({'confirmed': confirmed, 'failed': failed}, status=http_status.HTTP_200_OK)


@require_http_methods(["GET", "POST"])
@login_required
def confirm_consent(request):
    return render(request, 'index.html', context={'nav_bar': True})
    # try:
    #     if request.method == 'GET':
    #         confirm_ids = request.GET.getlist('confirm_id')
    #         callback_url = request.GET['callback_url']
    #     else:
    #         confirm_ids = request.POST.getlist('confirm_id')
    #         callback_url = request.POST['callback_url']
    # except KeyError:
    #     return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PARAM'])
    # else:
    #     if not confirm_ids:
    #         return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PARAM'])
    #
    #     ccs = ConfirmationCode.objects.filter(code__in=confirm_ids)
    #     if not ccs:
    #         return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_CONFIRMATION_CODE'])
    #
    #     if request.method == 'GET':
    #         consent = ccs[0].consent
    #         payload = json.loads(consent.profile.payload)
    #         destination_name = consent.destination.name
    #
    #         ctx = {
    #             'callback_url': callback_url,
    #             'destination_name': destination_name,
    #             'profile_payload': payload,
    #             'consents': [],
    #             'errors': []
    #         }
    #
    #         for cc in ccs:
    #             if cc.consent.status == Consent.PENDING and cc.check_validity():
    #                 ctx['consents'].append({
    #                     'confirm_id': cc.code,
    #                     'source': cc.consent.source.name,
    #                     'status': cc.consent.status,
    #                     'start_validity': cc.consent.start_validity.strftime('%Y-%m-%dT%H:%M:%S'),
    #                     'expire_validity': cc.consent.expire_validity.strftime('%Y-%m-%dT%H:%M:%S')
    #                 })
    #             else:
    #                 ctx['errors'].append(cc.code)
    #
    #         return render(request, 'confirm_consent.html', context=ctx)
    #     else:
    #         success = False
    #         for cc in ccs:
    #             if cc.check_validity() and cc.consent.status == Consent.PENDING:
    #                 cc.consent.status = Consent.ACTIVE
    #                 cc.consent.confirmed = datetime.now()
    #                 cc.consent.save()
    #                 if not success:
    #                     success = True
    #
    #         return HttpResponseRedirect(
    #             '{}?{}{}'.format(callback_url,
    #                              'success={}&'.format(json.dumps(success)),
    #                              '&'.join(['consent_confirm_id={}'.format(confirm_id) for confirm_id in
    #                                        confirm_ids]),
    #                              )
    #         )
