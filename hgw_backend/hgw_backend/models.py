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
import copy
import re
import time
from datetime import datetime

import requests
from requests.exceptions import ConnectionError
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator, _lazy_re_compile
from django.db import models
from django.forms import URLField as URLFormField
from django.utils.crypto import get_random_string
from oauth2_provider.models import AbstractApplication
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError, InvalidClientError, MissingTokenError
from requests_oauthlib import OAuth2Session


def get_source_id():
    return get_random_string(32)


class CustomURLValidator(URLValidator):
    """
    Custom URL Validator that support the presence of only the hostname (e.g.: "https://hostname/" is a valid value)
    """
    tld_re = (
            r'(\.'  # dot
            r'(?!-)'  # can't start with a dash
            r'(?:[a-z' + URLValidator.ul + '-]{2,63}'  # domain label
                                           r'|xn--[a-z0-9]{1,59})'  # or punycode label
                                           r'(?<!-)'  # can't end with a dash
                                           r'\.?)*'  # may have a trailing dot
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


class WrongUrlException(Exception):
    pass


class OAuth2Authentication(models.Model):
    source = GenericRelation(Source)
    token_url = models.CharField(max_length=100, blank=False, null=False)
    client_id = models.CharField(max_length=40, blank=False, null=False)
    client_secret = models.CharField(max_length=128, blank=False, null=False)

    def _get_token(self):
        try:
            ac = AccessToken.objects.get(oauth2_authentication=self)
        except AccessToken.DoesNotExist:
            return None
        return ac.to_python()

    def _fetch_token(self, oauth_session):
        oauth_session.fetch_token(token_url=self.token_url,
                                  client_id=self.client_id,
                                  client_secret=self.client_secret)

        self._save_token(oauth_session.token)

    def _save_token(self, token_data):
        token_data = copy.copy(token_data)
        token_data['expires_at'] = datetime.fromtimestamp(token_data['expires_at'])
        try:
            access_token = AccessToken.objects.get(oauth2_authentication=self)
        except AccessToken.DoesNotExist:
            AccessToken.objects.create(oauth2_authentication=self, **token_data)
        else:
            for k, v in token_data.items():
                setattr(access_token, k, v)
            access_token.save()

    def _get_oauth2_session(self):
        client = BackendApplicationClient(self.client_id)

        access_token = self._get_token()

        if access_token is None:
            oauth_session = OAuth2Session(client=client)
            self._fetch_token(oauth_session)
        else:
            oauth_session = OAuth2Session(client=client, token=access_token)

        return oauth_session

    def create_connector(self, source, connector):
        try:
            session = self._get_oauth2_session()
        except (ConnectionError, InvalidClientError, MissingTokenError):
            res = None
        else:
            try:
                res = session.post(source.url, json=connector)
                if res.status_code == 401:
                    raise TokenExpiredError
            except TokenExpiredError:
                self._fetch_token(session)
                res = session.post(source.url, json=connector)
            except ConnectionError:
                res = None
            except MissingTokenError:
                res = None

        if res is not None and res.status_code != 200:
            return None
        return res

    def __str__(self):
        try:
            return "ID: {id}. SOURCE: {source}".format(id=self.id, source=self.source.get())
        except Source.DoesNotExist:
            return "ID: {id}".format(id=self.id)

    class Meta:
        verbose_name = 'OAuth2 Authentication'


class RESTClient(AbstractApplication):
    STANDARD = 'STANDARD'
    SUPER = 'SUPER'

    ROLE_CHOICES = (
        ('ST', STANDARD),
        ('SU', SUPER)
    )

    source = models.OneToOneField('Source', null=True, blank=True)
    client_role = models.CharField(max_length=2, choices=ROLE_CHOICES, null=False, blank=False, default=STANDARD)
    scopes = models.CharField(max_length=100, blank=False, null=False, default=" ".join(settings.DEFAULT_SCOPES),
                              help_text="Space separated scopes to assign to the REST client")

    def is_super_client(self):
        return self.client_role == self.SUPER

    def has_scope(self, scope):
        return scope in self.scopes


class AccessToken(models.Model):
    oauth2_authentication = models.ForeignKey(OAuth2Authentication)
    access_token = models.CharField(max_length=1024, null=False, blank=False)
    token_type = models.CharField(max_length=10, null=False, blank=False)
    expires_in = models.IntegerField()
    expires_at = models.DateTimeField()
    scope = models.CharField(max_length=30)

    def to_python(self):
        return {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'expires_at': self.expires_at.timestamp(),
            'scope': self.scope
        }
