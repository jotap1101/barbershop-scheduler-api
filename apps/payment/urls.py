from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet

# Router para as views do modelo de pagamento
router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    # Inclui TODAS as rotas do router
    path("", include(router.urls)),
]
