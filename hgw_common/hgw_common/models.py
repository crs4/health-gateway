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

from hgw_common.fields import JSONValidator


def generate_id():
    return get_random_string(32)


class Profile(models.Model):
    code = models.CharField(max_length=10, blank=False, null=False)
    version = models.CharField(max_length=30, blank=False, null=False)
    payload = models.CharField(max_length=1000, blank=False, null=False, validators=[JSONValidator])

    def __str__(self):
        return self.code

    class Meta:
        unique_together = ('code', 'version')


class Channel(models.Model):
    channel_id = models.CharField(max_length=32, blank=False, null=False, default=generate_id)
    source_id = models.CharField(max_length=32, blank=False, null=False)
    destination_id = models.CharField(max_length=32, blank=False, null=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    person_id = models.CharField(max_length=100, blank=False, null=False)
