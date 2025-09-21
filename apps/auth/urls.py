from django.urls import path

from apps.auth.views import (
    CustomTokenBlacklistView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
)

# app_name = "auth"

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    path(
        "token/blacklist/", CustomTokenBlacklistView.as_view(), name="token_blacklist"
    ),
]
