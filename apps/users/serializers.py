from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name',
                'role', 'phone', 'birth_date', 'profile_picture', 'bio',
                'date_joined', 'created_at', 'updated_at']
        read_only_fields = ['date_joined', 'created_at', 'updated_at']

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate(self, data):
        if not data.get('role'):
            data['role'] = 'CLIENT'  # Default role
        return data

    def create(self, validated_data):
        if 'role' in validated_data and validated_data['role'] == 'ADMIN':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        user = User.objects.create_user(**validated_data)
        return user
    
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)

        if 'role' in validated_data:
            if validated_data['role'] == 'ADMIN':
                instance.is_staff = True
                instance.is_superuser = True
            else:
                instance.is_staff = False
                instance.is_superuser = False
        
        return super().update(instance, validated_data)