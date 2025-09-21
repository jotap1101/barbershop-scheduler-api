from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.appointment.views import AppointmentViewSet, BarberScheduleViewSet

router = DefaultRouter()

router.register(r"barber-schedules", BarberScheduleViewSet, basename="barberschedule")
router.register(r"appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
]
