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


import os

import json
import requests
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from destination_mockup.settings import HGW_FRONTEND_URI, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET


def generate_flow_id():
    return get_random_string(32)


def home(request):
    return render(request, 'index.html')


@csrf_exempt
def flow_requests(request, pk=None):
    client = BackendApplicationClient(OAUTH_CLIENT_ID)
    oauth_session = OAuth2Session(client=client)
    token_url = '{}/oauth2/token/'.format(HGW_FRONTEND_URI)
    access_token = oauth_session.fetch_token(token_url=token_url, client_id=OAUTH_CLIENT_ID,
                                             client_secret=OAUTH_CLIENT_SECRET)

    access_token = access_token["access_token"]
    access_token_header = {"Authorization": "Bearer {}".format(access_token)}
    action = request.GET['action']
    if action == 'get':
        if pk is not None:
            res = oauth_session.get('{}/v1/flow_requests/{}'.format(HGW_FRONTEND_URI, pk),
                                    headers=access_token_header)
        else:
            res = oauth_session.get('{}/v1/flow_requests/'.format(HGW_FRONTEND_URI),
                                    headers=access_token_header)
    elif action == 'post':
        payload = '[{"clinical_domain": "Laboratory", ' \
                  '"filters": [{"excludes": "HDL", "includes": "immunochemistry"}]}, ' \
                  '{"clinical_domain": "Radiology", ' \
                  '"filters": [{"excludes": "Radiology", "includes": "Tomography"}]}, ' \
                  '{"clinical_domain": "Emergency", ' \
                  '"filters": [{"excludes": "", "includes": ""}]}, ' \
                  '{"clinical_domain": "Prescription", ' \
                  '"filters": [{"excludes": "", "includes": ""}]}]'
        data = {
            'flow_id': generate_flow_id(),
            'profile': {
                'code': 'PROF002',
                'version': 'hgw.document.profile.v0',
                'payload': payload
            }
        }
        res = oauth_session.post('{}/v1/flow_requests/'.format(HGW_FRONTEND_URI),
                                 json=data, headers=access_token_header)
        print(res.status_code)
        if res.status_code == 201:
            json_res = res.json()
            request.session['flow_id'] = data['flow_id']
            request.session['process_id'] = json_res['process_id']
            # store somewhere association between process_id and flow_id
            callback_url = 'https://{}/flow_request_callback/'.format(request.get_host())
            confirm_url = '{}/v1/flow_requests/confirm/?confirm_id={}&action=add&callback_url={}'.format(
                HGW_FRONTEND_URI,
                json_res['confirm_id'],
                callback_url)
            return JsonResponse({'confirm_url': confirm_url})
        else:
            return HttpResponse("ERROR OPENING FLOW REQUEST %s" % res.content)
    elif action == 'delete':
        process_id = request.session['process_id']
        res = oauth_session.delete('{}/v1/flow_requests/{}'.format(HGW_FRONTEND_URI, process_id),
                                   headers=access_token_header)
        json_res = res.json()
        callback_url = 'https://{}/flow_request_callback/'.format(request.get_host())
        confirm_url = '{}/v1/flow_requests/confirm/?confirm_id={}&action=delete&callback_url={}'.format(
            HGW_FRONTEND_URI,
            json_res['confirm_id'],
            callback_url)
        return JsonResponse({'confirm_url': confirm_url})
    else:
        return HttpResponseNotAllowed
    print(res.content)
    return JsonResponse(res.json(), safe=False)


def protocol(request):
    access_token = request.session['access_token']
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    res = requests.get('{}/protocol/version'.format(HGW_FRONTEND_URI), headers=headers)
    return HttpResponse(res.content)


def flow_request_callback(request):
    return render(request, 'flow_request_feedback.html')
