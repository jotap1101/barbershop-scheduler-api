from django.apps import AppConfig


class BarbershopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.barbershop"
    verbose_name = "Barbershop"
    verbose_name_plural = "Barbershops"
    app_label = "barbershop"
    