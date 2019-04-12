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


from rest_framework import serializers

from hgw_common.models import Profile
from hgw_common.utils import get_oauth_token
from source_endpoint.settings import CONSENT_MANAGER_URI, CLIENT_ID, CLIENT_SECRET
from .models import Connector
from hgw_common.serializers import ProfileSerializer


class ConnectorSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = Connector
        fields = ('person_identifier', 'dest_public_key', 'channel_id', 'profile', 'start_validity', 'end_validity')

    def validate_channel_id(self, value):
        oauth_session, access_token_header = get_oauth_token(CONSENT_MANAGER_URI, CLIENT_ID, CLIENT_SECRET)
        res = oauth_session.get('{}/v1/consents/{}'.format(CONSENT_MANAGER_URI, value),
                                headers=access_token_header)

        if not res.ok or res.json()['status'] != 'AC':
            return serializers.ValidationError("Consent relative to channel {} is not active".format(value))
        return value

    def create(self, validated_data):
        profile, _ = Profile.objects.get_or_create(**validated_data.get('profile'))
        validated_data['profile'] = profile
        return Connector.objects.create(**validated_data)

"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkQzZzM/bVgtBUIpYdJAz
0Hdnm3WgdoFg9or4hUz1lknQQpawv8z2R2IPHOcsvjbmvTPivc3zJJetnndOiM6v
N35idgnSHAeyGttIgNTR0e6vd4RcMfwe3MCiM0bem/vkCj7Gb2ALCrIe797du7oc
Bt/k2eGKdXDtIE+/mUUNg17WbIewoOJZBXTcnkRx7mZ5xd9994taV5Fj9/LDiahb
oEc0C0uRP6D5XftXZiH89Tw3oAteraYecWKnpzbcYhasKR+ii//gzueikV4+wuql
W1EyTpcfgwbY/8dJSwHjjLmBPpcgs8ZkS55mur57wvnNUxJRJUYsGqfn9fPmeM5w
OQIDAQAB
-----END PUBLIC KEY-----"""
# {"channel_id": "52jiFVmbxehrozwKAJ2g0eqKZMEjkbct", 
# "source_id": "xaxAXkxi6Yw0KrpeBI5Ips7nVUDNozc7", 
# "destination": {"destination_id": "vnTuqCY3muHipTSan6Xdctj2Y0vUOVkj", "kafka_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp4TF/ETwYKG+eAYZz3wo\n8IYqrPIlQyz1/xljqDD162ZAYJLCYeCfs9yczcazC8keWzGd5/tn4TF6II0oINKh\nkCYLqTIVkVGC7/tgH5UEe/XG1trRZfMqwl1hEvZV+/zanV0cl7IjTR9ajb1TwwQY\nMOjcaaBZj+xfD884pwogWkcSGTEODGfoVACHjEXHs+oVriHqs4iggiiMYbO7TBjg\nBe9p7ZDHSVBbXtQ3XuGKnxs9MTLIh5L9jxSRb9CgAtv8ubhzs2vpnHrRVkRoddrk\n8YHKRryYcVDHVLAGc4srceXU7zrwAMbjS7msh/LK88ZDUWfIZKZvbV0L+/topvzd\nXQIDAQAB\n-----END PUBLIC KEY-----"},
#     "profile": {"code": "PROF002", 
#     "version": "hgw.document.profile.v0", 
#     "payload": "[{\"clinical_domain\": \"Laboratory\", \"filters\": [{\"excludes\": \"HDL\", \"includes\": \"immunochemistry\"}]}, {\"clinical_domain\": \"Radiology\", \"filters\": [{\"excludes\": \"Radiology\", \"includes\": \"Tomography\"}]}, {\"clinical_domain\": \"Emergency\", \"filters\": [{\"excludes\": \"\", \"includes\": \"\"}]}, {\"clinical_domain\": \"Prescription\", \"filters\": [{\"excludes\": \"\", \"includes\": \"\"}]}]"}, 
#         "person_id": "CSRGGL44L13H501E", "start_validity": "2019-04-12T10:03:52+02:00", "expire_validity": "2019-10-09T10:03:52+02:00"}
