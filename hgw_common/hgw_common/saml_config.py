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


try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

from os import path
from saml2 import saml
import saml2

IDP_META_PATH = path.join(path.dirname(__file__), './saml2/idp_metadata.xml')
ATTRIB_MAP_DIR_PATH = path.join(path.dirname(__file__), './saml2/attribute-maps')


def get_saml_config(root_url, sp_name, sp_key_file, sp_cert_file):
    return {

        # full path to the xmlsec1 binary programm
        'xmlsec_binary': '/usr/bin/xmlsec1',

        # your entity id, usually your subdomain plus the url to the metadata view
        'entityid': urljoin(root_url, '/saml2/metadata/'),
        'allow_unknown_attributes': True,

        # directory with attribute mapping
        'attribute_map_dir': ATTRIB_MAP_DIR_PATH,
        # this block states what services we provide
        'service': {
            # we are just a lonely SP
            'sp': {

                # fixme!
                'allow_unsolicited': True,
                'logout_requests_signed': True,
                'authn_requests_signed': True,
                'want_response_signed': True,
                'name': sp_name,
                'name_id_format': saml.NAMEID_FORMAT_TRANSIENT,
                'requested_attributes': [{
                     'name': 'uid',
                     'name_format': 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic'
                 }, {
                    'name': 'fiscalNumber',
                    'name_format': 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic'
                }],
                'required_attributes': ['uid','fiscalNumber'],
                'endpoints': {
                    # url and binding to the assetion consumer service view
                    # do not change the binding or service name
                    'assertion_consumer_service': [
                        (urljoin(root_url, '/saml2/acs/'), saml2.BINDING_HTTP_POST),
                    ],
                    # url and binding to the single logout service view
                    # do not change the binding or service name
                    'single_logout_service': [
                        (urljoin(root_url, '/saml2/ls/'), saml2.BINDING_HTTP_REDIRECT),
                        (urljoin(root_url, '/saml2/ls/post/'), saml2.BINDING_HTTP_POST),
                    ],
                },

            },
            # 'idp': {
            #     # we do not need a WAYF service since there is
            #     # only an IdP defined here. This IdP should be
            #     # present in our metadata
            #     'sign_assertion': False,
            #     'sign_response': False,
            #     # the keys of this dictionary are entity ids
            #     'https://spid-testenv-identityserver:9443': {
            #         'single_sign_on_service': {
            #             saml2.BINDING_HTTP_REDIRECT: 'https://spid-testenv-identityserver:9443/samlsso',
            #             saml2.BINDING_HTTP_POST: 'https://spid-testenv-identityserver:9443/samlsso',
            #         },
            #         'single_logout_service': {
            #             saml2.BINDING_HTTP_REDIRECT: 'https://spid-testenv-identityserver:9443/samlsso',
            #             saml2.BINDING_HTTP_POST: 'https://spid-testenv-identityserver:9443/samlsso',
            #         },
            #     },
            # },
        },
        # where the remote metadata is stored
        'metadata': {
            'local': [IDP_META_PATH],
        },
        # set to 1 to output debugging information
        'debug': 1,
        'timeslack': 5000,
        'accepted_time_diff': 5000,

        # certificate
        'key_file': sp_key_file,  # private part
        'cert_file': sp_cert_file,  # public part
        'valid_for': 24 * 365,  # how long is our metadata valid
    }
