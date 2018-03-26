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
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from consent_manager import serializers, ERRORS_MESSAGE
from consent_manager.models import Consent, ConfirmationCode
from hgw_common.utils import TokenHasResourceDetailedScope


class ConsentView(ViewSet):
    permission_classes = (TokenHasResourceDetailedScope,)
    required_scopes = ['consent']

    @staticmethod
    def get_consent(consent_id):
        try:
            return Consent.objects.get(consent_id=consent_id)
        except Consent.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_description='Get the list of consents',
        security=[{'consents': ['consent:read']}],
        responses={
            200: openapi.Response('The list of consents', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'consent_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                     description='The id of the consent'),
                        'person_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                     description='The id of the person'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='The status of the consent',
                                                 enum=[sc[0] for sc in Consent.STATUS_CHOICES]),
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
                                                         description='The start date validity of the consent'),
                        'expire_validity': openapi.Schema(type=openapi.TYPE_STRING,
                                                          format=openapi.FORMAT_DATETIME,
                                                          description='The end date validity of the consent'),
                        'source': openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={
                                                     'id': openapi.Schema(type=openapi.TYPE_STRING,
                                                                          description='The id of the source'),
                                                     'name': openapi.Schema(type=openapi.TYPE_STRING,
                                                                            description='The name of the source'),
                                                 })
                    }
                ))
                                  ),
            401: openapi.Response('The client has not provide a valid token or the token has expired'),
            403: openapi.Response('The token provided has not the right scope for the operation')
        })
    def list(self, request):
        consents = Consent.objects.all()
        serializer = serializers.ConsentSerializer(consents, many=True)
        if request.auth.application.is_super_client():
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

    @swagger_auto_schema(
        operation_description='Creates a new consent which is set in a PENDING status until the user confirms it',
        security=[{'consents': ['consent:write']}],
        responses={
            201: openapi.Response('The consent has been created successfully', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'consent_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                         description='the id of the newly created consent'),
                            'confirmation_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                              description='the id to send to the confirmation '
                                                                          'url to activate the consent')}
            )),
            401: openapi.Response('The client has not provide a valid token or the token has expired'),
            403: openapi.Response('The token provided has not the right scope for the operation')
        })
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

    @swagger_auto_schema(
        operation_description='Get the consent identified by the consent id',
        security=[{'consents': ['consent:read']}],
        manual_parameters=[
            openapi.Parameter('consents_id', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              description='The id of the consents to retrieve')
        ],
        responses={
            200: openapi.Response('The consent object', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'consent_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='The id of the consent'),
                    'person_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description='The id of the person'),
                    'status': openapi.Schema(type=openapi.TYPE_STRING,
                                             description='The status of the consent',
                                             enum=[sc[0] for sc in Consent.STATUS_CHOICES]),
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
                                                      description='The end date validity of the flow request'),
                    'source': openapi.Schema(type=openapi.TYPE_OBJECT,
                                             properties={
                                                 'id': openapi.Schema(type=openapi.TYPE_STRING,
                                                                      description='The id of the source'),
                                                 'name': openapi.Schema(type=openapi.TYPE_STRING,
                                                                        description='The name of the source'),
                                             })
                }
            )),
            401: openapi.Response('The client has not provide a valid token or the token has expired'),
            403: openapi.Response('The token provided has not the right scope for the operation')
        })
    def retrieve(self, request, consent_id, format=None):
        consent = self.get_consent(consent_id)
        serializer = serializers.ConsentSerializer(consent)
        if request.auth.application.is_super_client():
            print(request)
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


@require_http_methods(["GET", "POST"])
@login_required
def confirm_consent(request):
    try:
        if request.method == 'GET':
            confirm_ids = request.GET.getlist('confirm_id')
            callback_url = request.GET['callback_url']
        else:
            confirm_ids = request.POST.getlist('confirm_id')
            callback_url = request.POST['callback_url']
    except KeyError:
        return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PARAM'])
    else:
        if not confirm_ids:
            return HttpResponseBadRequest(ERRORS_MESSAGE['MISSING_PARAM'])

        ccs = ConfirmationCode.objects.filter(code__in=confirm_ids)
        if not ccs:
            return HttpResponseBadRequest(ERRORS_MESSAGE['INVALID_CONFIRMATION_CODE'])

        if request.method == 'GET':
            consent = ccs[0].consent
            payload = json.loads(consent.profile.payload)
            destination_name = consent.destination.name

            ctx = {
                'callback_url': callback_url,
                'destination_name': destination_name,
                'profile_payload': payload,
                'consents': [],
                'errors': []
            }

            for cc in ccs:
                if cc.consent.status == Consent.PENDING and cc.check_validity():
                    ctx['consents'].append({
                        'confirm_id': cc.code,
                        'source': cc.consent.source.name,
                        'is_valid': cc.check_validity(),
                        'status': cc.consent.status,
                        'start_validity': consent.start_validity.strftime('%Y-%m-%dT%H:%M:%S'),
                        'expire_validity': consent.expire_validity.strftime('%Y-%m-%dT%H:%M:%S')
                    })
                else:
                    ctx['errors'].append(cc.code)

            return render(request, 'confirm_consent.html', context=ctx)
        else:
            success = False
            for cc in ccs:
                if cc.check_validity() and cc.consent.status == Consent.PENDING:
                    cc.consent.status = Consent.ACTIVE
                    cc.consent.confirmed = datetime.now()
                    cc.consent.save()
                    if not success:
                        success = True

            return HttpResponseRedirect(
                '{}?{}{}'.format(callback_url,
                                 'success={}&'.format(json.dumps(success)),
                                 '&'.join(['consent_confirm_id={}'.format(confirm_id) for confirm_id in
                                           confirm_ids]),
                                 )
            )


@require_http_methods(["GET", "POST"])
@login_required
def revoke_consents(request):
    page_status = {
        'REVOKING': 0,
        'REVOKED': 1
    }
    if request.method == 'GET':
        consents = Consent.objects.filter(person_id=request.user.fiscalNumber)
        consent_list = []
        for c in consents:
            if c.status == 'AC':
                consent_list.append({
                    'source_name': c.source.name,
                    'destination_name': c.destination.name,
                    'status': c.status,
                    'profile': json.loads(c.profile.payload),
                    'id': c.id
                })
        context = {'status': page_status['REVOKING'], 'consents': consent_list}
    else:
        revoke_list = request.POST.getlist('revoke_list')
        revoked = []
        for consent in revoke_list:
            try:
                c = Consent.objects.get(id=consent, status=Consent.ACTIVE, person_id=request.user.fiscalNumber)
            except Consent.DoesNotExist:
                pass
            else:
                c.status = Consent.REVOKED
                c.save()
                revoked.append({
                    'source_name': c.source.name,
                    'destination_name': c.destination.name,
                    'profile': json.loads(c.profile.payload),
                })
        context = {'status': page_status['REVOKED'], 'consents': revoked}
    return render(request, 'revoke_consent.html', context=context)
