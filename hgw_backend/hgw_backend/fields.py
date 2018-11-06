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
from django import forms
from django.core.validators import URLValidator, _lazy_re_compile
from django.db import models


class HostnameURLValidator(URLValidator):
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


class HostnameURLFormField(forms.URLField):
    """
    Form field that uses HostnameURLValidator
    """
    default_validators = [HostnameURLValidator]


class HostnameURLField(models.URLField):
    """
    Model field that uses HostnameURLValidator and HostnameURLFormField
    """
    default_validators = [HostnameURLValidator]

    def formfield(self, **kwargs):
        defaults = {
            'form_class': HostnameURLFormField,
        }
        defaults.update(kwargs)
        return super(HostnameURLField, self).formfield(**defaults)