from django.urls import path

from .views import (
    CustomTokenBlacklistView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
)

urlpatterns = [
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain"),
    path("api/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    path(
        "api/token/blacklist/",
        CustomTokenBlacklistView.as_view(),
        name="token_blacklist",
    ),
]
