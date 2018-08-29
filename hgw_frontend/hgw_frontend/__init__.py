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


CONFIRM_ACTIONS = (
    'add',
    'delete'
)

ERRORS_MESSAGE = {
    'MISSING_PARAM': 'Missing parameters',
    'UNKNOWN_ACTION': 'Unknown action',
    'INVALID_CONFIRMATION_CODE': 'Confirmation code not valid',
    'INVALID_FR_STATUS': 'Invalid flow request status',
    'EXPIRED_CONFIRMATION_ID': 'Confirmation code expired',
    'INVALID_CONSENT_STATUS': 'Invalid consent status',
    'UNKNOWN_CONSENT': 'Unknown consent',
    'INVALID_DATA': 'Invalid parameters',
    'MISSING_PERSON_ID': 'Missing person id',
    'INVALID_CONSENT_CLIENT': 'Error creating consents in consent manager',
    'CANNOT_CONTACT_CONSENT': 'Cannot contact consent manager',
    'INVALID_BACKEND_CLIENT': 'Error getting source from backend',
    'CANNOT_CONTACT_BACKEND': 'Cannot contact backend'
}
