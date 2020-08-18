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
import logging

from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse, HttpResponseRedirect

from urllib.parse import urlparse
from urllib.parse import parse_qs

from django.utils.crypto import get_random_string
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from djangosaml2.utils import get_custom_setting

from hgw_frontend.models import ConfirmationCode, FlowRequest, Channel
from hgw_frontend import settings
from hgw_frontend.views.flow_requests import _interrupt_flow_request_at_idp_step

logger = logging.getLogger('hgw_frontend.flow_request')


def view_profile(request):
    return HttpResponse("Home sweet home")


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'flow-requests': reverse('flow-requests-list', request=request, format=format)
    })


def saml_redirect_failures(request, *args, **kwargs):
    # redirect the user to the view where he came from
    default_relay_state = get_custom_setting('ACS_DEFAULT_REDIRECT_URL',
                                             settings.LOGIN_REDIRECT_URL)
    status_type = 'error'
    reason = 'unknown'

    import traceback
    errstr = traceback.format_exc().splitlines()

    logger.debug('Collected SAML2 failure')
    try:
        saml2_err = (errstr[-2].split(': ')[0])
        if saml2_err.find('saml2') >= 0:
            rsn = saml2_err.split('.')[-1]
            if rsn == 'StatusRequestDenied':
                status_type = 'aborted'
                reason = 'idp_rejected'
            elif rsn == 'StatusAuthnFailed':
                reason = 'invalid_credentials'
            else:
                reason = rsn
    except IndexError:
        logger.error('An issue collected in SAML2 ACS does not contain a SAML2 error code. This should not be')

    relay_state = request.POST.get('RelayState', default_relay_state)

    parsed_relay_state_url = urlparse(relay_state)
    try:
        callback = parse_qs(parsed_relay_state_url.query)['callback_url'][0]
        fr_confirm_code = parse_qs(parsed_relay_state_url.query)['confirm_id'][0]
    except (IndexError, KeyError):
        raise SuspiciousOperation('Missing callback_url or confirm_id in querystring. This should not be.')

    return _interrupt_flow_request_at_idp_step(fr_confirm_code, callback, status_type=status_type, reason=reason)
