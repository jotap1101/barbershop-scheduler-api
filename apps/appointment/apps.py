from django.apps import AppConfig


class AppointmentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.appointment"
    verbose_name = "Appointment"
    verbose_name_plural = "Appointments"
    app_label = "appointment"
