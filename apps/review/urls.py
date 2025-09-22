from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet

# Router para as views do modelo de avaliação
router = DefaultRouter()
router.register(r"reviews", ReviewViewSet, basename="reviews")

urlpatterns = [
    # Inclui TODAS as rotas do router
    path("", include(router.urls)),
]
