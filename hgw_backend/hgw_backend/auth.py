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
from enum import Enum
import requests

from hgw_backend.settings import SOURCE_ENDPOINT_CLIENT_KEY, SOURCE_ENDPOINT_CLIENT_CERT


class AuthType(Enum):
    CERTIFICATES_BASED = 'CERTIFICATES_BASED'

    @staticmethod
    def get_values():
        return AuthType.__members__


class AbstractAuthProxy(object):
    def create_connector(self, source, connector):
        raise NotImplemented


class CertificateBasedAuthProxy(AbstractAuthProxy):

    @staticmethod
    def _get_absolute_path(cert_path):
        return os.path.join(
            os.path.dirname(__file__),
            CertificateBasedAuthProxy.CERTS_RELATIVE_DIR,
            cert_path
        )

    def create_connector(self, source, connector):
        client_cert_path = SOURCE_ENDPOINT_CLIENT_CERT
        client_key_path = SOURCE_ENDPOINT_CLIENT_KEY

        return requests.post(source.url,
                             json=connector,
                             verify=True,
                             cert=(client_cert_path, client_key_path)
                             )


class AuthProxy(AbstractAuthProxy):
    def __init__(self):
        self._proxies_dict = {
            AuthType.CERTIFICATES_BASED: CertificateBasedAuthProxy
        }

    def _get_auth_proxy(self, source):
        return self._proxies_dict[AuthType(source.auth_type)]

    def create_connector(self, source, connector):
        return self._get_auth_proxy(source)().create_connector(source, connector)
