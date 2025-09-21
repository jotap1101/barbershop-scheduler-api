from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.user.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("api/", include(router.urls)),
]
