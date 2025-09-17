from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, BarberScheduleViewSet

app_name = 'appointments'

router = DefaultRouter()
router.register('', AppointmentViewSet, basename='appointment')
router.register('schedules', BarberScheduleViewSet, basename='barberschedule')

urlpatterns = router.urls