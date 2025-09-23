from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auth"
    label = "apps_auth"
    verbose_name = "Authentication"
    verbose_name_plural = "Authentications"
    app_label = "auth"
