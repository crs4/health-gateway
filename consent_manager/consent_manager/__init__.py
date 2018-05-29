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
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, Http404):
        response = Response({'errors': ['not_found']}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Call REST framework's default exception handler first,
        # to get the standard error response.
        response = exception_handler(exc, context)

    return response


ERRORS_MESSAGE = {
    'MISSING_PARAM': 'missing_parameters',
    'UNKNOWN_ACTION': 'Unknown action',
    'INVALID_CONFIRMATION_CODE': 'Confirmation code not valid',
    'INVALID_STATUS': 'Invalid status',
    'EXPIRED_CONFIRMATION_ID': 'Confirmation code expired',
    'INVALID_CONSENT_STATUS': 'Invalid consent status',
    'UNKNOWN_CONSENT': 'Unknown consent',
    'INVALID_DATA': 'Invalid parameters',
    'MISSING_PERSON_ID': 'Missing person id'
}
