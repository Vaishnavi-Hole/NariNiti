from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, INDIAN_STATES, INDIAN_LANGUAGES
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    preferred_language = serializers.ChoiceField(choices=INDIAN_LANGUAGES, default='en')
    state = serializers.ChoiceField(choices=INDIAN_STATES, required=False, allow_blank=True)
    accept_terms = serializers.BooleanField(required=True)
    receive_updates = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'password', 'confirm_password', 'preferred_language', 'state', 'accept_terms', 'receive_updates']

    def validate_phone(self, value):
        if not re.match(r'^\d{10,15}$', value):
            raise serializers.ValidationError("Phone number must be between 10 and 15 digits.")
        if UserProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number is already registered.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not data.get('accept_terms'):
            raise serializers.ValidationError({"accept_terms": "You must accept the terms and conditions."})
        return data

    def create(self, validated_data):
        email = validated_data.get('email', '')
        user = User.objects.create_user(
            username=validated_data['phone'],
            email=email,
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        UserProfile.objects.create(
            user=user,
            phone=validated_data['phone'],
            preferred_language=validated_data.get('preferred_language', 'en'),
            state=validated_data.get('state', ''),
            receive_updates=validated_data.get('receive_updates', False)
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'preferred_language', 'state', 'receive_updates']


class SafeUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
