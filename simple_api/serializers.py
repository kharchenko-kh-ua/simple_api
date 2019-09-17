"""
Common serializers
"""
import clearbit

from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework.serializers import ModelSerializer
from rest_framework.validators import ValidationError

from pyhunter import PyHunter


User = get_user_model()


class CreateUserSerializer(ModelSerializer):
    """
    User sign up serializer. Expanded for third party calls for
    email verification and additional data fetch.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        """
        Check if email exists
        """
        if not settings.DEBUG_SIGNUP:
            hunter = PyHunter(settings.HUNTER_API_KEY)
            verification = hunter.email_verifier(value)
            if verification['result'] == 'undeliverable':
                raise ValidationError('Email address does not exist')
        return value

    def create(self, validated_data):
        """
        Retrieve additional data if possible
        """
        instance = super().create(validated_data)
        if not settings.DEBUG_SIGNUP:
            email = validated_data.get('email')
            clearbit.key = settings.CLEARBIT_PUBLISHABLE_KEY
            additional_data = clearbit.Enrichment.find(email=email, stream=True)
            if additional_data:
                try:
                    first_name = additional_data['person']['name']['givenName']
                    last_name = additional_data['person']['name']['familyName']
                    instance.first_name = first_name
                    instance.last_name = last_name
                    instance.save(update_fields=['first_name', 'last_name'])
                except (KeyError, ValueError):
                    pass
        password = validated_data.get('password')
        instance.set_password(password)
        instance.save()
        return instance
