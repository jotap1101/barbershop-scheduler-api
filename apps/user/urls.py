from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.user.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

app_name = "user"

urlpatterns = [
    path("", include(router.urls)),
]
