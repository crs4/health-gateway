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
from oauth2_provider.models import AbstractApplication

from consent_manager.settings import REQUEST_VALIDITY_SECONDS, DEFAULT_SCOPES
from hgw_common.utils import generate_id, get_logger

logger = get_logger('consent_manager')


class Consent(models.Model):
    PENDING = 'PE'
    ACTIVE = 'AC'
    REVOKED = 'RE'
    NOT_VALID = 'NV'

    STATUS_CHOICES = (
        (REVOKED, 'REVOKED'),  # Status set to a Consent that was never confirmed
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
    start_validity = models.DateTimeField(null=False)
    expire_validity = models.DateTimeField(null=False)

    def save(self, *args, **kwargs):
        super(Consent, self).save(*args, **kwargs)


def get_validity():
    return timezone.now() + timedelta(seconds=REQUEST_VALIDITY_SECONDS)


class ConfirmationCode(models.Model):
    consent = models.ForeignKey('Consent', on_delete=models.CASCADE)
    code = models.CharField(max_length=32, blank=False, null=False, unique=True, default=generate_id)
    validity = models.DateTimeField(default=get_validity)

    def check_validity(self):
        return timezone.now() < self.validity


class ConsentManagerUser(AbstractUser):
    fiscalNumber = models.CharField(max_length=16, blank=True, null=True)


class Endpoint(models.Model):
    """
    Generic Endpoint (Destination or Source). It contains the id and name of the
    Destinations and Sources to be used in Consent
    """
    id = models.CharField(max_length=32, blank=False, null=False, primary_key=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    #
    # class Meta:
    #     unique_together = ('id', 'name')


class RESTClient(AbstractApplication):
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
        return self.client_role == self.SUPER

    def has_scope(self, scope):
        return scope in self.scopes
