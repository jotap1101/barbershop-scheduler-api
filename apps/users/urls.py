from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth_views import (
    CustomTokenBlacklistView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
)
from .views import UserViewSet

# Router para as views do modelo User
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    # Inclui TODAS as rotas do router (isso é crucial!)
    path("api/", include(router.urls)),
    # Rotas de autenticação JWT
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    path(
        "api/token/blacklist/",
        CustomTokenBlacklistView.as_view(),
        name="token_blacklist",
    ),
]
