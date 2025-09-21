from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.auth.serializers import CustomTokenObtainPairSerializer


# Create your custom views here.
@extend_schema_view(
    post=extend_schema(
        summary="Obter token JWT",
        description="Obtém um par de tokens JWT (access e refresh) para autenticação.",
        tags=["authentication"],
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    post=extend_schema(
        summary="Atualizar token JWT",
        description="Atualiza o token de acesso usando um token de atualização válido.",
        tags=["authentication"],
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        summary="Verificar token JWT",
        description="Verifica a validade de um token JWT.",
        tags=["authentication"],
    )
)
class CustomTokenVerifyView(TokenVerifyView):
    pass


@extend_schema_view(
    post=extend_schema(
        summary="Invalidar token JWT",
        description="Invalidar um token de atualização, removendo-o da lista de tokens válidos.",
        tags=["authentication"],
    )
)
class CustomTokenBlacklistView(TokenBlacklistView):
    pass
