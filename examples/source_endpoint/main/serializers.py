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
        fields = ('person_identifier', 'dest_public_key', 'channel_id', 'profile')

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
