from django.urls import path
from .jwt_views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView
)

urlpatterns = [
    path('', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
]