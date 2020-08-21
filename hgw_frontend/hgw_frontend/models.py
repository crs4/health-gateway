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


from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from oauth2_provider.models import AbstractApplication

from hgw_common.utils import generate_id
from hgw_frontend.settings import REQUEST_VALIDITY_SECONDS, DEFAULT_SCOPES


class Source(models.Model):
    source_id = models.CharField(max_length=32, blank=False, null=False, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    profile = models.ForeignKey('hgw_common.Profile', on_delete=models.CASCADE, null=False)

    def __str__(self):
        return self.name


class FlowRequest(models.Model):
    PENDING = 'PE'
    ACTIVE = 'AC'
    DELETE_REQUESTED = 'DR'

    STATUS_CHOICES = (
        (PENDING, 'PENDING'),
        (ACTIVE, 'ACTIVE'),
        (DELETE_REQUESTED, 'DELETE_REQUIRED')
    )

    flow_id = models.CharField(max_length=32, blank=False)
    process_id = models.CharField(max_length=32, blank=False)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, blank=False, default=PENDING)
    person_id = models.CharField(max_length=20, blank=True, null=True)
    profile = models.ForeignKey('hgw_common.Profile', on_delete=models.CASCADE, null=True)
    sources = models.ManyToManyField(Source)
    destination = models.ForeignKey('Destination', on_delete=models.PROTECT)
    start_validity = models.DateTimeField(null=False)
    expire_validity = models.DateTimeField(null=False)

    def __unicode__(self):
        return 'Destination: {} - Process ID {} - Status: {}'.\
            format(self.destination, self.process_id, self.status)

    def __str__(self):
        return self.__unicode__()


class Channel(models.Model):
    # The channel has been created and the corresponding consent has been created in the consent manager
    CONSENT_REQUESTED = 'CR'
    # The consent has been given and it is waiting for the source to be notified
    WAITING_SOURCE_NOTIFICATION = 'WS'
    # The source has been notified and the channel is active
    ACTIVE = 'AC'
    # The person revoked the consent into the consent manager
    CONSENT_REVOKED = 'CV'
    # The person aborted the consent process
    CONSENT_ABORTED = 'AB'

    STATUS_CHOICES = (
        (CONSENT_REQUESTED, 'CONSENT_REQUESTED'),
        (WAITING_SOURCE_NOTIFICATION, 'WAITING_SOURCE_NOTIFICATION'),
        (ACTIVE, 'ACTIVE'),
        (CONSENT_REVOKED, 'CONSENT_REVOKED'),
        (CONSENT_ABORTED, 'CONSENT_ABORTED')
    )

    channel_id = models.CharField(max_length=32, blank=False)
    flow_request = models.ForeignKey(FlowRequest, null=False, on_delete=models.PROTECT)
    source = models.ForeignKey(Source, null=False, on_delete=models.PROTECT)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, blank=False)
    start_validity = models.DateTimeField(null=True)
    expire_validity = models.DateTimeField(null=True)

    def __str__(self):
        return "{}: {} - {} - {} - {}".format(self.channel_id, self.flow_request.person_id,
                                              self.flow_request.destination.name, self.source.name, self.status)

    class Meta:
        unique_together = ('flow_request', 'source')


def get_validity():
    return timezone.now() + timedelta(seconds=REQUEST_VALIDITY_SECONDS)


def get_confirmation_code():
    return get_random_string(32)


class ConfirmationCode(models.Model):
    flow_request = models.ForeignKey('FlowRequest', on_delete=models.CASCADE)
    code = models.CharField(max_length=32, blank=False, null=False, unique=True, default=get_confirmation_code)
    validity = models.DateTimeField(default=get_validity)

    def check_validity(self):
        return timezone.now() < self.validity

    def __unicode__(self):
        return 'Code {} - Validity: {}'.\
            format(self.code, self.validity)

    def __str__(self):
        return self.__unicode__()


class ConsentConfirmation(models.Model):
    flow_request = models.ForeignKey(FlowRequest, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    consent_id = models.CharField(max_length=32, blank=False, null=False, unique=True)
    confirmation_id = models.CharField(max_length=32, blank=False, null=False)
    destination_endpoint_callback_url = models.CharField(max_length=100, blank=False, null=False)

    def __unicode__(self):
        return 'Consent {} - Confirmation: {}'.format(self.consent_id, self.confirmation_id)

    def __str__(self):
        return self.__unicode__()


class HGWFrontendUser(AbstractUser):
    fiscalNumber = models.CharField(max_length=16, blank=True, null=True)

    def __unicode__(self):
        return self.fiscalNumber

    def __str__(self):
        return self.__unicode__()


class Destination(models.Model):
    KAFKA = 'K'
    REST = 'R'

    destination_id = models.CharField(max_length=32, default=generate_id, null=True, unique=True)
    rest_or_kafka = models.CharField(max_length=1, default='K', blank=False, null=False,
                                     choices=((KAFKA, 'REST'), (REST, 'KAFKA')))
    name = models.CharField(max_length=30, null=False, blank=False, unique=True)
    kafka_public_key = models.TextField(max_length=500, null=True, help_text="Public key in PEM format")

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class RESTClient(AbstractApplication):

    STANDARD = 'ST'
    SUPER = 'SU'

    ROLE_CHOICES = (
        ('ST', STANDARD),
        ('SU', SUPER)
    )

    destination = models.OneToOneField('Destination', null=True, blank=True, on_delete=models.CASCADE)
    client_role = models.CharField(max_length=2, choices=ROLE_CHOICES, null=False, blank=False, default=STANDARD)
    scopes = models.CharField(max_length=100, blank=False, null=False, default=" ".join(DEFAULT_SCOPES),
                              help_text="Space separated scopes to assign to the REST client")

    def is_super_client(self):
        return self.client_role == self.SUPER

    def has_scope(self, scope):
        return scope in self.scopes

    def __unicode__(self):
        return 'Destination: {}'.format(self.destination)

    def __str__(self):
        return self.__unicode__()
