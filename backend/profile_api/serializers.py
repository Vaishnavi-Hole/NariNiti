from rest_framework import serializers
from authentication.models import UserProfile
from django.contrib.auth.models import User

class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    phone = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'phone', 'preferred_language', 'state', 'receive_updates']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Update User model fields
        user = instance.user
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        if 'email' in user_data:
            user.email = user_data['email']
        user.save()

        # Update UserProfile model fields
        if 'phone' in validated_data:
            # check if phone exists in other profiles
            new_phone = validated_data['phone']
            if UserProfile.objects.exclude(pk=instance.pk).filter(phone=new_phone).exists():
                raise serializers.ValidationError({"phone": "Phone number already in use."})
            instance.phone = new_phone
            
            # Since phone is username, update username too
            user.username = new_phone
            user.save()

        if 'preferred_language' in validated_data:
            instance.preferred_language = validated_data['preferred_language']
        if 'state' in validated_data:
            instance.state = validated_data['state']
        if 'receive_updates' in validated_data:
            instance.receive_updates = validated_data['receive_updates']

        instance.save()
        return instance
