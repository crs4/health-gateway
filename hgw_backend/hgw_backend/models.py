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

import requests
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator, _lazy_re_compile
from django.db import models
from django.forms import URLField as URLFormField
from django.utils.crypto import get_random_string
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session


def get_source_id():
    return get_random_string(32)


class CustomURLValidator(URLValidator):
    """
    Custom URL Validator that support the presence of only the hostname (e.g.: "https://hostname/" is a valid value)
    """
    tld_re = (
        r'(\.'                                # dot
        r'(?!-)'                             # can't start with a dash
        r'(?:[a-z' + URLValidator.ul + '-]{2,63}'         # domain label
        r'|xn--[a-z0-9]{1,59})'              # or punycode label
        r'(?<!-)'                            # can't end with a dash
        r'\.?)*'                               # may have a trailing dot
    )
    host_re = '(' + URLValidator.hostname_re + URLValidator.domain_re + tld_re + '|localhost)'

    regex = _lazy_re_compile(
        r'^(?:[a-z0-9\.\-\+]*)://'  # scheme is validated separately
        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
        r'(?:' + URLValidator.ipv4_re + '|' + URLValidator.ipv6_re + '|' + host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z', re.IGNORECASE)


class CustomURLFormField(URLFormField):
    """
    Form field that uses CustomURLValidator
    """
    default_validators = [CustomURLValidator]


class CustomURLField(models.URLField):
    """
    Model field that uses CustomURLValidator and CustomURLFormField
    """
    default_validators = [CustomURLValidator]

    def formfield(self, **kwargs):
        defaults = {
            'form_class': CustomURLFormField,
        }
        defaults.update(kwargs)
        return super(CustomURLField, self).formfield(**defaults)


class Source(models.Model):
    source_id = models.CharField(max_length=32, blank=False, null=False, default=get_source_id, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    url = CustomURLField(blank=False, null=False)

    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.name

    def create_connector(self, connector):
        return self.content_object.create_connector(self, connector)


class CertificatesAuthentication(models.Model):
    source = GenericRelation(Source)
    cert = models.FileField(blank=False, null=False)
    key = models.FileField(blank=False, null=False)

    def create_connector(self, source, connector):
        return requests.post(source.url,
                             json=connector,
                             verify=True,
                             cert=(self.cert.file.name, self.key.file.name)
                             )

    def __str__(self):
        try:
            return "ID: {id}. SOURCE: {source}".format(id=self.id, source=self.source.get())
        except Source.DoesNotExist:
            return "ID: {id}".format(id=self.id)


class OAuth2Authentication(models.Model):
    source = GenericRelation(Source)
    token_url = models.CharField(max_length=100, blank=False, null=False)
    client_id = models.CharField(max_length=40, blank=False, null=False)
    client_secret = models.CharField(max_length=128, blank=False, null=False)
    token = models.CharField(max_length=1024, blank=True, null=True)

    def _get_new_token(self, oauth_session):
        res = oauth_session.fetch_token(token_url=self.token_url,
                                        client_id=self.client_id,
                                        client_secret=self.client_secret)
        self.token = res['access_token']
        self.save()
        return res

    def _get_oauth2_token(self, force_new=False):
        client = BackendApplicationClient(self.client_id)
        if self.token is None or force_new is True:
            oauth_session = OAuth2Session(client=client)
            token = self._get_new_token(oauth_session)
        else:
            token = {'access_token': self.token, 'token_type': 'Bearer'}
            oauth_session = OAuth2Session(client=client, token=token)

        access_token_header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
        return oauth_session, access_token_header

    def create_connector(self, source, connector):
        session, header = self._get_oauth2_token()
        try:
            res = session.post(source.url, json=connector)
        except TokenExpiredError:
            session, header = self._get_oauth2_token(force_new=True)
            res = session.post(source.url, json=connector)
        return res

    def __str__(self):
        try:
            return "ID: {id}. SOURCE: {source}".format(id=self.id, source=self.source.get())
        except Source.DoesNotExist:
            return "ID: {id}".format(id=self.id)

    class Meta:
        verbose_name = 'OAuth2 Authentication'
