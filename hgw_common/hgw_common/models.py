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
from datetime import datetime

from django.db import models
from django.utils.crypto import get_random_string
from oauthlib.oauth2 import BackendApplicationClient, MissingTokenError, TokenExpiredError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests_oauthlib import OAuth2Session

from hgw_common.utils import get_logger

logger = get_logger('hgw_common')


def generate_id():
    """
    Function to generate random id
    """
    return get_random_string(32)


class Profile(models.Model):
    """
    Class for model Profile
    """
    code = models.CharField(max_length=20, blank=False, null=False)
    version = models.CharField(max_length=10, blank=False, null=False)

    def __str__(self):
        return self.code

    class Meta:
        unique_together = ('code', 'version')


class ProfileDomain(models.Model):
    """
    Class for model ProfileDomain
    """
    profile = models.ForeignKey(Profile, related_name="domains", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    coding_system = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class ProfileSection(models.Model):
    """
    Class for model ProfileSection
    """
    profile_domain = models.ForeignKey(ProfileDomain, related_name="domains", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    coding_system = models.CharField(max_length=10)


class Channel(models.Model):
    """
    Class for model Channel
    """
    channel_id = models.CharField(max_length=32, blank=False, null=False, default=generate_id)
    source_id = models.CharField(max_length=32, blank=False, null=False)
    destination_id = models.CharField(max_length=32, blank=False, null=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    person_id = models.CharField(max_length=100, blank=False, null=False)


class AccessToken(models.Model):
    """
    Class for model Consent
    """
    token_url = models.CharField(
        max_length=200, null=False, blank=False, unique=True)
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
            'scope': self.scope.split(" ")
        }


class OAuth2SessionProxy(object):
    """
    This class can be used to access an OAuth2 protected resources. It reuses an AccessToken until the token expires.
    It handles automatic creation and refresh of a token
    """

    def __init__(self, token_url, client_id, client_secret):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._session = self.create_session()

    def request(self, method, url, **kwargs):
        """
        Performs an http request to :url: using :method:
        """
        try:
            logger.debug('Performing request with method %s to %s', method, url)
            if method == 'POST':
                res = self._session.post(url, **kwargs)
            else:
                res = self._session.get(url, **kwargs)
            if res.status_code == 401:
                raise TokenExpiredError
        except TokenExpiredError:
            logger.debug('Token expired. Getting a new one')
            self._fetch_token(self._session)
            logger.debug('Retrying to perform the request')
            res = self._session.get(url)
        except RequestsConnectionError:
            logger.debug('Connection error performing %s on %s', method, url)
            res = None
        except MissingTokenError:
            logger.debug('Missing token for %s', url)
            res = None
        return res

    def get(self, url, **kwargs):
        """
        Perform a GET request to url using the oauth session
        """
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        """
        Perform a POST request to url using the oauth session
        """
        return self.request('POST', url, **kwargs)

    def create_session(self):
        """
        Creates an oauth session, getting a token
        """
        client = BackendApplicationClient(self.client_id)
        try:
            logger.debug("Querying db to check for a previuos token for url: %s", self.token_url)
            access_token = AccessToken.objects.get(token_url=self.token_url)
        except AccessToken.DoesNotExist:
            logger.debug("No token found in the db. Requesting a new one")
            oauth_session = OAuth2Session(client=client)
            self._fetch_token(oauth_session)
        else:
            logger.debug("Token found")
            oauth_session = OAuth2Session(client=client, token=access_token.to_python())
        return oauth_session

    def _fetch_token(self, oauth_session):

        try:
            oauth_session.fetch_token(token_url=self.token_url,
                                      client_id=self.client_id,
                                      client_secret=self.client_secret)
        except RequestsConnectionError:
            logger.warning('Cannot obtain a token: the server is down')
            raise

        token_data = {
            'access_token': oauth_session.token['access_token'],
            'token_type': oauth_session.token['token_type'],
            'expires_in': oauth_session.token['expires_in'],
            'expires_at': datetime.fromtimestamp(oauth_session.token['expires_at']),
            'scope': ' '.join(oauth_session.token['scope'])
        }

        try:
            access_token = AccessToken.objects.get(token_url=self.token_url)
        except AccessToken.DoesNotExist:
            AccessToken.objects.create(token_url=self.token_url, **token_data)
        else:
            for k, v in token_data.items():
                setattr(access_token, k, v)
            access_token.save()


class FailedMessages(models.Model):
    """
    Model to store messages that was not notified
    """
    # JSON_DECODING = 'JS'
    # DECODING = 'DE'
    # SOURCE_NOT_FOUND = 'SN'
    # WRONG_MESSAGE_STRUCTURE = 'WS'
    # WRONG_DATE_FORMAT = 'WD'
    # SENDING_ERROR = 'SE'
    # UNKNOWN_ERROR = 'UE'

    # FAIL_REASON = ((JSON_DECODING, 'JSON_DECODING'),
    #                (DECODING, 'DECODING'),
    #                (SOURCE_NOT_FOUND, 'SOURCE_NOT_FOUND'),
    #                (WRONG_MESSAGE_STRUCTURE, 'WRONG_MESSAGE_STRUCTURE'),
    #                (WRONG_DATE_FORMAT, 'WRONG_DATE_FORMAT'),
    #                (SENDING_ERROR, 'SENDING_ERROR'),
    #                (UNKNOWN_ERROR, 'UNKNOWN_ERROR'))

    message_type = models.CharField(max_length=30, blank=False, null=False)
    message = models.CharField(max_length=1500, blank=False, null=False)
    reason = models.CharField(max_length=10, blank=False, null=False)
    retry = models.BooleanField(help_text="Boolean indicating if the message delivery should be retried")