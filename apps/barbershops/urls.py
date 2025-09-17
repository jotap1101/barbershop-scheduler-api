from rest_framework.routers import DefaultRouter
from .views import (
    BarbershopViewSet, ServiceViewSet,
    BarberViewSet, BarbershopCustomerViewSet
)

app_name = 'barbershops'

router = DefaultRouter()
router.register('', BarbershopViewSet, basename='barbershop')
router.register('services', ServiceViewSet, basename='service')
router.register('barbers', BarberViewSet, basename='barber')
router.register('customers', BarbershopCustomerViewSet, basename='customer')

urlpatterns = router.urls