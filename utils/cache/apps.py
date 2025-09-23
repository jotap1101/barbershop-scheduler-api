"""
Configuração do sistema de cache

Este módulo configura o sistema de cache e registra os signals
"""

from django.apps import AppConfig


class CacheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utils.cache"
    verbose_name = "Sistema de Cache"

    def ready(self):
        """
        Registra os signals quando a app está pronta
        """
        try:
            from . import signals
        except ImportError:
            pass
