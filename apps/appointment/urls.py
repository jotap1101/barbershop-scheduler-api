from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, BarberScheduleViewSet

# Router para as views dos modelos de agendamento
router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointments")
router.register(r"barber-schedules", BarberScheduleViewSet, basename="barber-schedules")

urlpatterns = [
    # Inclui TODAS as rotas do router
    path("", include(router.urls)),
]