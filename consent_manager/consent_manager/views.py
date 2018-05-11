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


import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from consent_manager import serializers, ERRORS_MESSAGE
from consent_manager.models import Consent, ConfirmationCode
from hgw_common.utils import IsAuthenticatedOrTokenHasResourceDetailedScope


class ConsentView(ViewSet):
    permission_classes = (IsAuthenticatedOrTokenHasResourceDetailedScope,)
    oauth_views = ['list', 'create', 'retrieve']
    required_scopes = ['consent']

    @staticmethod
    def get_consent(consent_id):
        try:
            return Consent.objects.get(consent_id=consent_id)
        except Consent.DoesNotExist:
            raise Http404

    def list(self, request):
        if request.user is not None:
            consents = Consent.objects.filter(person_id=request.user.fiscalNumber, status=Consent.ACTIVE)
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

            return Response(res, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, consent_id, format=None):
        consent = self.get_consent(consent_id)
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

    def revoke(self, request):
        try:
            consents = request.data['consents']
        except KeyError:
            return Response({'error': 'missing_parameters'}, status.HTTP_400_BAD_REQUEST)

        revoked = []
        for consent in consents:
            try:
                c = Consent.objects.get(consent_id=consent, status=Consent.ACTIVE,
                                        person_id=request.user.fiscalNumber)
            except Consent.DoesNotExist:
                pass
            else:
                c.status = Consent.REVOKED
                c.save()
                revoked.append(c.consent_id)
        return Response({'revoked': revoked}, status=status.HTTP_200_OK)

    def find(self, request):
        """
        Method to find consent. The only supported query parameter is by confirmation_id
        :param request:
        :return:
        """
        if 'confirm_id' not in request.query_params:
            return Response({'error': ERRORS_MESSAGE['MISSING_PARAM']}, status.HTTP_400_BAD_REQUEST)

        confirm_ids = request.GET.getlist('confirm_id')
        ccs = ConfirmationCode.objects.filter(code__in=confirm_ids, consent__status=Consent.PENDING)
        if not ccs:
            return Response({}, status.HTTP_404_NOT_FOUND)

        consents = [cc.consent for cc in ccs if cc.check_validity()]
        # for cc in ccs:
        #     if cc.check_validity():
        #         consents.append({
        #             'confirm_id': cc.code,
        #             'source': cc.consent.source.name,
        #             'is_valid': cc.check_validity(),
        #             'status': cc.consent.status,
        #             'profile': cc.consent.profile.payload,
        #             'start_validity': cc.consent.start_validity.strftime('%Y-%m-%dT%H:%M:%S'),
        #             'expire_validity': cc.consent.expire_validity.strftime('%Y-%m-%dT%H:%M:%S')
        #         })
        serializer = serializers.ConsentSerializer(consents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@require_http_methods(["GET", "POST"])
@login_required
def confirm_consent(request):
    return render(request, 'index.html', context={'nav_bar': False})
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
