from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BarbershopCustomerViewSet, BarbershopViewSet, ServiceViewSet

# Router para as views dos modelos da barbearia
router = DefaultRouter()
router.register(r"barbershops", BarbershopViewSet, basename="barbershops")
router.register(r"services", ServiceViewSet, basename="services")
router.register(
    r"barbershop-customers", BarbershopCustomerViewSet, basename="barbershop-customers"
)

urlpatterns = [
    # Inclui TODAS as rotas do router
    path("", include(router.urls)),
]
