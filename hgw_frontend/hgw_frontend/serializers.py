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


from django.db import IntegrityError
from rest_framework import serializers

from hgw_common.models import Profile
from hgw_common.serializers import ProfileSerializer
from hgw_frontend.models import FlowRequest, Destination


# class DestinationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Destination
#         fields = ('destination_id',)


class FlowRequestSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    def create(self, validated_data):
        pr, _ = Profile.objects.get_or_create(**validated_data.get('profile'))
        validated_data['profile'] = pr
        fr = FlowRequest.objects.create(**validated_data)
        return fr

    class Meta:
        model = FlowRequest
        fields = ('flow_id', 'process_id', 'status', 'profile', 'destination', 'start_validity', 'expire_validity')
