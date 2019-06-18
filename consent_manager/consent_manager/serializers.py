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
from hgw_common.utils import ERRORS, get_logger


logger = get_logger('consent_manager.serializers')


class AttributesNotAllowed(ValidationError): pass


class EnpointDuplicateValidator(object):
    """
    Validator for duplicate Endpoint. It checks if the Endpoint already exists with the correct attribute
    """
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
    """
    Serializer for Endpoint model
    """
    id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
    name = serializers.CharField(max_length=100, allow_null=False, allow_blank=False)

    def get_validators(self):
        return super(EndpointSerializer, self).get_validators() + [EnpointDuplicateValidator()]

    class Meta:
        model = Endpoint
        fields = ('id', 'name')


class ConsentSerializer(serializers.ModelSerializer):
    """
    Serializer for Consent model
    """
    update_fields = {'start_validity', 'expire_validity'}
    profile = ProfileSerializer(many=False, allow_null=False)
    source = EndpointSerializer(many=False, allow_null=False)
    destination = EndpointSerializer(many=False, allow_null=False)

    def create(self, validated_data):
        try:
            profile = Profile.objects.get(code=validated_data['profile']['code'],
                                          version=validated_data['profile']['version'])
            logger.info('Profile with the same parameters found')
        except Profile.DoesNotExist:
            logger.info('Profile not found. Creating a new one')
            profile_serializer = ProfileSerializer(data=validated_data['profile'])
            if profile_serializer.is_valid():
                profile = profile_serializer.save()
                logger.info('Created profile')
            else:
                logger.error('Profile not valid')
        
        source, _ = Endpoint.objects.get_or_create(**validated_data.get('source'))
        destination, _ = Endpoint.objects.get_or_create(**validated_data.get('destination'))
        validated_data['profile'] = profile
        validated_data['source'] = source
        validated_data['destination'] = destination
        return Consent.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.start_validity = validated_data['start_validity']
        instance.expire_validity = validated_data['expire_validity']
        instance.save()
        return instance

    def _updating(self):
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
        if self._updating():
            if not set(attrs.keys()).issubset(self.update_fields):
                raise ValidationError('attributes_not_editable', code='attributes_not_editable')
            return attrs

        try:
            source = Endpoint.objects.get(**attrs['source'])
            destination = Endpoint.objects.get(**attrs['destination'])
            profile = Profile.objects.get(code=attrs['profile']['code'], version=attrs['profile']['version'])
            consents = Consent.objects.filter(source=source, destination=destination, profile=profile, person_id=attrs['person_id'])
        except (Consent.DoesNotExist, Endpoint.DoesNotExist, Profile.DoesNotExist):
            logger.info("No consent with same parameters has been found. It is possible to continue with the Consent creation")
            # If one among source, destination and profile doesn't exist it means that neither the consent exists
            return attrs
        else:
            logger.info("Consent with the same parameter has been found. Checking if the current consent is ACTIVE")
            for consent in consents:
                if consent.status == Consent.ACTIVE:
                    logger.info("The consent is ACTIVE. Aborting the new Consent creation")
                    raise ValidationError(ERRORS.DUPLICATED)
                elif consent.status == Consent.PENDING:
                    logger.info("Old consent is in PENDING status. Setting it to NOT_VAID")
                    consent.status = Consent.NOT_VALID
                    consent.save()
            return attrs


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
