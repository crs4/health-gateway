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
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import get_logger
from hgw_frontend.models import Channel, FlowRequest, Source

logger = get_logger("hgw_frontend")


class SourceSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False, allow_null=False)

    def create(self, validated_data):
        if validated_data['profile'] is not None:
            profile, _ = Profile.objects.get_or_create(**validated_data.get('profile'))
            validated_data['profile'] = profile

        source = Source.objects.create(**validated_data)
        return source

    def update(self, instance, validated_data):
        if validated_data['profile'] is not None:
            profile, _ = Profile.objects.get_or_create(**validated_data.get('profile'))
            validated_data['profile'] = profile

        instance.name = validated_data.get('name', instance.name)
        instance.profile = validated_data.get('profile', instance.profile)
        instance.save()
        return instance

    class Meta:
        model = Source
        fields = ('source_id', 'name', 'profile')
        extra_kwargs = {
            'name': {
                'validators': []
            },
            'source_id': {
                'validators': []
            }
        }


class FlowRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for Flow Request
    """
    profile = ProfileSerializer(many=False, allow_null=True)
    sources = SourceSerializer(many=True, allow_null=False)

    def create(self, validated_data):
        sources = validated_data.pop('sources')
        logger.debug(sources)
        if validated_data['profile'] is not None:
            profile, _ = Profile.objects.get_or_create(**validated_data.get('profile'))
            validated_data['profile'] = profile
        flow_request = FlowRequest.objects.create(**validated_data)

        for source_data in sources:
            try:
                source = Source.objects.get(source_id=source_data['source_id'])
            except Source.DoesNotExist:
                pass
            else:
                flow_request.sources.add(source)

        return flow_request

    class Meta:
        model = FlowRequest
        fields = ('flow_id', 'process_id', 'status', 'profile', 'destination', 'sources', 'start_validity', 'expire_validity')


class ChannelSerializer(serializers.ModelSerializer):
    destination_id = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    source = SourceSerializer(allow_null=False)

    class Meta:
        model = Channel
        fields = ('channel_id', 'status', 'destination_id', 'source', 'profile')

    @staticmethod
    def get_destination_id(obj):
        return obj.flow_request.destination.destination_id

    @staticmethod
    def get_profile(obj):
        return ProfileSerializer(obj.flow_request.profile).data
