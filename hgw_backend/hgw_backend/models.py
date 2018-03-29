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
import requests
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.crypto import get_random_string


def get_source_id():
    return get_random_string(32)


class Source(models.Model):
    CERTIFICATES = 'C'
    OAUTH2 = 'O'

    AUTH_TYPES = {
        CERTIFICATES: 'Certificates',
        OAUTH2: 'OAuth2'
    }

    source_id = models.CharField(max_length=32, blank=False, null=False, default=get_source_id, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    url = models.URLField(blank=False, null=False)
    auth_type = models.CharField(
        max_length=3,
        blank=False,
        null=False,
        choices=tuple(AUTH_TYPES.items()),
        default=(CERTIFICATES, AUTH_TYPES[CERTIFICATES])
    )

    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Source, self).__init__(*args, **kwargs)
        self._auth_type = None

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





