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


from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from consent_manager.models import Consent, Endpoint
from hgw_common.models import Profile
from hgw_common.serializers import ProfileSerializer
from hgw_common.utils import ERRORS


class AttributesNotAllowed(ValidationError): pass


class EnpointDuplicateValidator(object):
    message = 'An instance with the same {equal_field} and different {different_field} already exists'

    def __call__(self, attrs):
        try:
            e = Endpoint.objects.get(Q(id=attrs['id']) | Q(name=attrs['name']))
            if e:
                if e.name != attrs['name']:
                    raise ValidationError(self.message.format(equal_field='id', different_field='name'),
                                          code='duplicate')
                if e.id != attrs['id']:
                    raise ValidationError(self.message.format(equal_field='name', different_field='id'),
                                          code='duplicate')
        except Endpoint.DoesNotExist:
            return attrs


class EndpointSerializer(serializers.ModelSerializer):
    id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
    name = serializers.CharField(max_length=100, allow_null=False, allow_blank=False)

    def get_validators(self):
        return super(EndpointSerializer, self).get_validators() + [EnpointDuplicateValidator()]

    class Meta:
        model = Endpoint
        fields = ('id', 'name')


class ConsentSerializerDuplicateValidator(object):
    message = 'Consent already present'

    def __call__(self, attrs):
        try:
            s = Endpoint.objects.get(**attrs['source'])
            d = Endpoint.objects.get(**attrs['destination'])
            p = Profile.objects.get(**attrs['profile'])
            consents = Consent.objects.filter(source=s, destination=d, profile=p, person_id=attrs['person_id'])
        except (Consent.DoesNotExist, Endpoint.DoesNotExist, Profile.DoesNotExist) as ex:
            # If one among source, destination and profile doesn't exist it means that neither the consent exists
            return attrs
        else:
            for c in consents:
                if c.status == Consent.ACTIVE:
                    raise ValidationError(self.message, code='unique')
                elif c.status == Consent.PENDING:
                    c.status = Consent.NOT_VALID
                    c.save()
                    return attrs


class ConsentSerializer(serializers.ModelSerializer):
    update_fields = {'start_validity', 'expire_validity'}
    profile = ProfileSerializer(many=False, allow_null=False)
    source = EndpointSerializer(many=False, allow_null=False)
    destination = EndpointSerializer(many=False, allow_null=False)

    def create(self, validated_data):
        p, _ = Profile.objects.get_or_create(**validated_data.get('profile'))
        s, _ = Endpoint.objects.get_or_create(**validated_data.get('source'))
        d, _ = Endpoint.objects.get_or_create(**validated_data.get('destination'))
        validated_data['profile'] = p
        validated_data['source'] = s
        validated_data['destination'] = d
        cs = Consent.objects.create(**validated_data)
        return cs

    def update(self, instance, validated_data):
        instance.start_validity = validated_data['start_validity']
        instance.expire_validity = validated_data['expire_validity']
        instance.save()
        return instance

    def is_update(self):
        return self.instance is not None

    def validate(self, attrs):
        """
        Perform consent validation checking that:
            - the source exists with the exact same fields' values
            - the destination exists with the exact same fields' values
            - the profile exists with the exact same fields' values
            - the Consent is not ACTIVE. If the consent is ACTIVE the validation fails. If it is PENDING, it is set
              to NOT_VALID and validation passes
        :param attrs: the attributes to validate
        :return: the validated attributes
        """
        if self.is_update():
            if not set(attrs.keys()).issubset(self.update_fields):
                raise ValidationError('attributes_not_editable', code='attributes_not_editable')
            return attrs
        try:
            s = Endpoint.objects.get(**attrs['source'])
            d = Endpoint.objects.get(**attrs['destination'])
            p = Profile.objects.get(**attrs['profile'])
            consents = Consent.objects.filter(source=s, destination=d, profile=p, person_id=attrs['person_id'])
        except (Consent.DoesNotExist, Endpoint.DoesNotExist, Profile.DoesNotExist) as ex:
            # If one among source, destination and profile doesn't exist it means that neither the consent exists
            return attrs
        else:
            for c in consents:
                if c.status == Consent.ACTIVE:
                    raise ValidationError(ERRORS.DUPLICATED)
                elif c.status == Consent.PENDING:
                    c.status = Consent.NOT_VALID
                    c.save()
            return attrs

    # def get_validators(self):
    #     return super(ConsentSerializer, self).get_validators() + [ConsentSerializerDuplicateValidator()]

    class Meta:
        model = Consent
        fields = ('consent_id', 'status', 'source', 'destination', 'person_id',
                  'profile', 'start_validity', 'expire_validity')
        extra_kwargs = {
            'start_validity': {
                'error_messages': {
                    'invalid': 'invalid_date_format'}
            },
            'expire_validity': {
                'error_messages': {
                    'invalid': 'invalid_date_format'}
            }
        }
