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

import re
import time

import cgi

from hgw_common.utils.mocks import MockRequestHandler

EXPIRED_CONSENT_CHANNEL = 'expired_consent'


class MockSourceEndpointHandler(MockRequestHandler):
    WRITER_CLIENT_ID = 'writer'
    WRITER_CLIENT_SECRET = 'writer'
    WRITE_SCOPE = 'connectors:write'
    GRANT_TYPE = 'client_credentials'

    OAUTH2_PATTERN = re.compile(r'/oauth2/token/')
    CONNECTORS_PATTERN = re.compile(r'/v1/connectors/')

    def _handle_oauth(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        client_id = form.getvalue('client_id')
        client_secret = form.getvalue('client_secret')
        grant_type = form.getvalue('grant_type')

        if client_id == self.WRITER_CLIENT_ID and client_secret == self.WRITER_CLIENT_SECRET \
                and grant_type == self.GRANT_TYPE:
            payload = {'access_token': 'token',
                       'token_type': 'Bearer',
                       'expires_in': 1800,
                       'scope': [self.WRITE_SCOPE]
                       }
            status_code = 201
        else:
            payload = {'error': 'invalid_client'}
            status_code = 401
        return payload, status_code

    def do_POST(self):
        if re.search(self.OAUTH2_PATTERN, self.path):
            payload, status_code = self._handle_oauth()
            self._send_response(payload, status_code)
            return True
        elif self._path_match(self.CONNECTORS_PATTERN):
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            if EXPIRED_CONSENT_CHANNEL.encode('utf-8') in data_string or 'expired' in self.headers['Authorization']:
                status_code = 401
                payload = {'detail': 'Authentication credentials were not provided.'}
            else:
                payload = {}
                status_code = 201
        else:
            payload = {}
            status_code = 404
        self._send_response(payload, status_code)
