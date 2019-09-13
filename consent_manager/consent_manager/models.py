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


import logging
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from oauth2_provider.models import AbstractApplication

from consent_manager.settings import DEFAULT_SCOPES, REQUEST_VALIDITY_SECONDS
from hgw_common.utils import generate_id

logger = logging.getLogger('consent_manager.models')


class Consent(models.Model):
    """
    Model for Consents
    """
    PENDING = 'PE'
    ACTIVE = 'AC'
    REVOKED = 'RE'
    NOT_VALID = 'NV'

    STATUS_CHOICES = (
        (REVOKED, 'REVOKED'),
        (PENDING, 'PENDING'),
        (ACTIVE, 'ACTIVE'),
        (NOT_VALID, 'NOT_VALID'),
    )

    consent_id = models.CharField(db_index=True, max_length=32, blank=False, default=generate_id)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, blank=False, default=PENDING)
    source = models.ForeignKey('Endpoint', on_delete=models.CASCADE, related_name='source')
    destination = models.ForeignKey('Endpoint', on_delete=models.CASCADE, related_name='destination')
    person_id = models.CharField(max_length=20, blank=False, null=False)
    profile = models.ForeignKey('hgw_common.Profile', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    confirmed = models.DateTimeField(null=True)
    start_validity = models.DateTimeField(null=True)
    expire_validity = models.DateTimeField(null=True)

    def __str__(self):
        return 'Consent ID: {} - Person: {} - Status {}'.format(self.consent_id, self.person_id, self.status)


# class ConsentHistory(models.Model):
#     """
#     This models stores the history of a Consent in order to keep track of the changes occurred
#     """
#     consent = models.ForeignKey('Consent')
#     status = models.CharField(max_length=2, choices=Consent.STATUS_CHOICES, null=False)
#     profile = models.ForeignKey('hgw_common.Profile', on_delete=models.CASCADE)
#     start_validity = models.DateTimeField(null=True)
#     expire_validity = models.DateTimeField(null=True)
#     start_date = models.DateTimeField(null=True, desc="The start date the of the validity of this version of the consent")
#     end_date = models.DateTimeField(null=True, desc="The end date the of the validity of this version of the consent")


def get_validity():
    """
    Function that returns the datetime default value for the validity of a :class:`ConfirmationCode`.
    It returns the current time plus :attr:`REQUEST_VALIDITY_SECONDS`
    """
    return timezone.now() + timedelta(seconds=REQUEST_VALIDITY_SECONDS)


class ConfirmationCode(models.Model):
    """
    Model for Confirmation Codes. These are temporary code to be used by the Consent Creator to confirm the consents.
    They are valid for a limited amount of time
    """
    consent = models.ForeignKey('Consent', on_delete=models.CASCADE)
    code = models.CharField(max_length=32, blank=False, null=False, unique=True, default=generate_id)
    validity = models.DateTimeField(default=get_validity)

    def check_validity(self):
        """
        Check if the code is still valid (i.e., the validity field is greater than the current time)
        """
        return timezone.now() < self.validity


class ConsentManagerUser(AbstractUser):
    """
    User model. It adds italian fiscalNumber to the basic Django User
    """
    fiscalNumber = models.CharField(max_length=16, blank=True, null=True)

    def __str__(self):
        return self.fiscalNumber


class Endpoint(models.Model):
    """
    Generic Endpoint (Destination or Source). It contains the id and name of the
    Destinations and Sources to be used in Consent
    """
    id = models.CharField(max_length=32, blank=False, null=False, primary_key=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)

    def __str__(self):
        return self.name


class RESTClient(AbstractApplication):
    """
    Model for REST Clients. It implements the application of django_oauth_toolkit.
    It adds the :attr:`client_role`, which can be STANDARD or SUPER, and :attr:`scopes`
    """
    STANDARD = 'ST'
    SUPER = 'SU'

    ROLE_CHOICES = (
        ('STANDARD', STANDARD),
        ('SUPER', SUPER)
    )

    client_role = models.CharField(max_length=2, choices=ROLE_CHOICES, null=False, blank=False, default=STANDARD)
    scopes = models.CharField(max_length=100, blank=False, null=False, default=" ".join(DEFAULT_SCOPES),
                              help_text="Space separated scopes to assign to the REST client")

    def is_super_client(self):
        """
        Method to check if a client is a SUPER client (i.e., it has special permission) or not
        """
        return self.client_role == self.SUPER

    def has_scope(self, scope):
        """
        Method to check if a client own the scope specified
        """
        return scope in self.scopes

    def __str__(self):
        return self.name
