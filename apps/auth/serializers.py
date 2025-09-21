from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado que verifica se o usuário está ativo.
    """

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except serializers.ValidationError as e:
            if hasattr(e, "detail") and e.detail.get("code") == "no_active_account":
                raise serializers.ValidationError(
                    {"detail": "Conta de usuário está desativada."}
                )
            raise e
        return data

