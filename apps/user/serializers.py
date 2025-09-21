from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.user.models import User


# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with all fields"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_barbershop_owner",
            "phone",
            "birth_date",
            "profile_picture",
            "bio",
            "date_joined",
            "updated_at",
            "is_active",
            "is_staff",
        ]
        read_only_fields = ["id", "date_joined", "updated_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
            "phone",
            "birth_date",
            "profile_picture",
            "bio",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Os campos de senha não coincidem."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "birth_date",
            "profile_picture",
            "bio",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user profile"""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_barbershop_owner",
            "phone",
            "birth_date",
            "profile_picture",
            "bio",
            "date_joined",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "username", "email", "date_joined", "updated_at"]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password"""

    old_password = serializers.CharField(
        required=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True, validators=[validate_password], style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        required=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "Os campos de nova senha não coincidem."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("A senha atual está incorreta.")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for user lists"""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "role",
            "is_barbershop_owner",
            "profile_picture",
            "is_active",
        ]
