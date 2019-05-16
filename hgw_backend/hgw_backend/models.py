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
import json
from datetime import datetime

import requests
from django.conf import settings
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from oauth2_provider.models import AbstractApplication
from oauthlib.oauth2 import (BackendApplicationClient, InvalidClientError,
                             MissingTokenError, TokenExpiredError)
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from requests_oauthlib import OAuth2Session

from hgw_backend.fields import HostnameURLField
from hgw_backend.settings import KAFKA_NOTIFICATION_TOPIC
from hgw_backend.utils import get_kafka_producer
from hgw_common.utils import get_logger

logger = get_logger('hgw_backend')


def get_source_id():
    return get_random_string(32)


class Source(models.Model):
    """
    Model that represent a Source. A Source is registered with an unique id, a name, a url, which is the rest endpoint
    to use to open a Connector in the Source, a Profile and a triple that identifies the authentication method to use
    with that Source. Available authentication methods are Certificates authentication and oAuth2 authentication.
    """
    source_id = models.CharField(max_length=32, blank=False, null=False, default=get_source_id, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    url = HostnameURLField(blank=False, null=False)
    profile = models.ForeignKey('hgw_common.Profile', blank=False, null=False, on_delete=models.DO_NOTHING)

    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.name

    def create_connector(self, connector):
        return self.content_object.create_connector(self, connector)


@receiver(post_save, sender=Source)
def source_saved_handler(sender, instance, **kwargs):
    """
    Post save signal handler for Source model.
    It sends new Source data to kafka
    """
    message = {
        'source_id': instance.source_id,
        'name': instance.name,
        'profile': {
            'code': instance.profile.code,
            'version': instance.profile.version,
            'payload': instance.profile.payload
        }
    }
    kafka_producer = get_kafka_producer()
    kafka_producer.send(KAFKA_NOTIFICATION_TOPIC, value=json.dumps(message).encode('utf-8'))


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


class FailedConnector(models.Model):
    """
    Model to store messages from hgw_frontend that failed delivering to Sources
    """
    JSON_DECODING = 'JS'
    DECODING = 'DE'
    SOURCE_NOT_FOUND = 'SN'
    WRONG_MESSAGE_STRUCTURE = 'WS'
    WRONG_DATE_FORMAT = 'WD'
    SENDING_ERROR = 'SE'
    UNKNOWN_ERROR = 'UE'

    FAIL_REASON = ((JSON_DECODING, 'JSON_DECODING'),
                   (DECODING, 'DECODING'),
                   (SOURCE_NOT_FOUND, 'SOURCE_NOT_FOUND'),
                   (WRONG_MESSAGE_STRUCTURE, 'WRONG_MESSAGE_STRUCTURE'),
                   (WRONG_DATE_FORMAT, 'WRONG_DATE_FORMAT'),
                   (SENDING_ERROR, 'SENDING_ERROR'),
                   (UNKNOWN_ERROR, 'UNKNOWN_ERROR'))

    message = models.CharField(max_length=1500, blank=False, null=False)
    reason = models.CharField(max_length=2, choices=FAIL_REASON)
    retry = models.BooleanField()


class WrongUrlException(Exception):
    pass


class OAuth2Authentication(models.Model):
    source = GenericRelation(Source)
    token_url = models.CharField(max_length=100, blank=False, null=False)
    client_id = models.CharField(max_length=40, blank=False, null=False)
    client_secret = models.CharField(max_length=128, blank=False, null=False)
    auth_username = models.CharField(max_length=40, null=True)
    auth_password = models.CharField(max_length=128, null=True)
    basic_auth = models.BooleanField(default=False, null=False)

    def _get_token(self):
        try:
            ac = AccessToken.objects.get(oauth2_authentication=self)
        except AccessToken.DoesNotExist:
            return None
        return ac.to_python()

    def _fetch_token(self, oauth_session):
        if self.basic_auth is True:
            auth = HTTPBasicAuth(self.auth_username, self.auth_password)
            oauth_session.fetch_token(token_url=self.token_url,
                                      client_id=self.client_id,
                                      client_secret=self.client_secret,
                                      auth=auth)
        else:
            oauth_session.fetch_token(token_url=self.token_url,
                                      client_id=self.client_id,
                                      client_secret=self.client_secret)

        self._save_token(oauth_session.token)

    def _save_token(self, token_data):
        new_token_data = {
            'access_token': token_data['access_token'],
            'token_type': token_data['token_type'],
            'expires_in': token_data['expires_in'],
            'expires_at': datetime.fromtimestamp(token_data['expires_at']),
            'scope': ' '.join(token_data['scope'])
        }
        try:
            access_token = AccessToken.objects.get(oauth2_authentication=self)
        except AccessToken.DoesNotExist:
            AccessToken.objects.create(oauth2_authentication=self, **new_token_data)
        else:
            for k, v in new_token_data.items():
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
        except (ConnectionError, InvalidClientError, MissingTokenError) as e:
            logger.debug("Error opening an oauth2 session with the source endpoint: {}".format(e))
            res = None
        else:
            try:
                logger.debug("Creating connector with data %s", connector)
                res = session.post(source.url, json=connector)
                if res.status_code == 401:
                    raise TokenExpiredError
            except TokenExpiredError:
                logger.debug("Token for the source expired. Getting a new one")
                self._fetch_token(session)
                logger.debug("Creating connector with the new token")
                res = session.post(source.url, json=connector)
            except ConnectionError:
                logger.debug("Connection error creating the connector")
                res = None
            except MissingTokenError:
                logger.debug("Missing token for the source endpoint")
                res = None

        if res is not None and res.status_code != 201:
            logger.debug("Error opening connector: {} with status code: {}".format(res.content, res.status_code))
            return None
        logger.debug("Connector created correctly")
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
