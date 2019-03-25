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
from rest_framework.exceptions import ValidationError

from hgw_common.models import Profile, ProfileDomain, ProfileSection


class ProfileSectionSerializer(serializers.ModelSerializer):
    """
    Serializer for a ProfileSection model
    """

    class Meta:
        model = ProfileSection
        fields = ('name', 'code', 'coding_system')


class ProfileDomainSerializer(serializers.ModelSerializer):
    """
    Serializer for a ProfileDomain
    """
    sections = ProfileSectionSerializer(many=True, allow_null=False)

    class Meta:
        model = ProfileDomain
        fields = ('name', 'code', 'coding_system', 'sections')


class ProfileValidator(object):

    def __call__(self, attrs):
        try:
            profile = Profile.objects.get(code=attrs['code'], version=attrs['version'])
        except Profile.DoesNotExist:
            return attrs
        else:
            domains = ProfileDomain.objects.filter(profile=profile)
            domain_serializer = ProfileDomainSerializer(instance=domains, many=True)
            if domain_serializer.data == attrs['domains']:
                return attrs
            raise ValidationError('A profile with the same code and version but different sections exists. The profile is not correct',
                                  code='duplicate')


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Profile model
    """

    domains = ProfileDomainSerializer(many=True, allow_null=False)

    def create(self, validated_data):
        domains_data = validated_data.pop('domains')
        profile = Profile.objects.create(**validated_data)
        if profile is not None:
            for domain_data in domains_data:
                sections_data = domain_data.pop('sections')
                domain = ProfileDomain.objects.create(profile=profile, **domain_data)
                if domain:
                    for section_data in sections_data:
                        ProfileSection.objects.create(profile_domain=domain, **section_data)
            return profile

    class Meta:
        model = Profile
        validators = [ProfileValidator()]  # Validation should be performed by clients
        fields = ('code', 'version', 'domains')
