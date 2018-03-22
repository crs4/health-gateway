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


from django.db import models
from django.utils.crypto import get_random_string

import hgw_backend.auth as auth


def get_source_id():
    return get_random_string(32)


class Source(models.Model):
    source_id = models.CharField(max_length=32, blank=False, null=False, default=get_source_id, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    url = models.URLField(blank=False, null=False)
    auth_type = models.CharField(
        max_length=128,
        blank=False,
        null=False,
        choices=auth.AuthType.get_values().items(),
        default=auth.AuthType.CERTIFICATES_BASED.value
    )

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Source, self).__init__(*args, **kwargs)
        self._auth_type = None

    def create_connector(self, connector):
        return auth.AuthProxy().create_connector(self, connector)

    def get_auth_param(self, key):
        return SourceAuthenticationParam.objects.get(source=self, key=key).value


class SourceAuthenticationParam(models.Model):
    source = models.ForeignKey(Source)
    key = models.CharField(max_length=128, blank=False, null=False)
    value = models.TextField(blank=False, null=False)

    class Meta:
        unique_together = ('source', 'key')

