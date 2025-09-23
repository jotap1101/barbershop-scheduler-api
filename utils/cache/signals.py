"""
Sistema de invalidação de cache por signals Django

Este módulo conecta aos signals do Django para invalidação automática
de cache quando modelos são modificados
"""

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.apps import apps

from utils.cache import cache_manager, CacheKeys


@receiver(post_save, sender="barbershop.Barbershop")
def invalidate_barbershop_cache(sender, instance, created, **kwargs):
    """
    Invalida cache quando uma barbearia é criada ou atualizada
    """
    cache_manager.invalidate_related_cache("barbershop", instance.id)

    # Se foi criada, invalida listas gerais
    if created:
        cache_manager.invalidate_pattern(CacheKeys.BARBERSHOP_PREFIX)


@receiver(post_delete, sender="barbershop.Barbershop")
def invalidate_barbershop_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida cache quando uma barbearia é deletada
    """
    cache_manager.invalidate_related_cache("barbershop", instance.id)


@receiver(post_save, sender="barbershop.Service")
def invalidate_service_cache(sender, instance, created, **kwargs):
    """
    Invalida cache quando um serviço é criado ou atualizado
    """
    cache_manager.invalidate_related_cache("service", instance.id)

    # Se foi criado, invalida listas gerais
    if created:
        cache_manager.invalidate_pattern(CacheKeys.SERVICE_PREFIX)
        cache_manager.invalidate_pattern(
            CacheKeys.BARBERSHOP_PREFIX
        )  # Pode afetar listagem de barbearias


@receiver(post_delete, sender="barbershop.Service")
def invalidate_service_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida cache quando um serviço é deletado
    """
    cache_manager.invalidate_related_cache("service", instance.id)


@receiver(post_save, sender="appointment.Appointment")
def invalidate_appointment_cache(sender, instance, created, **kwargs):
    """
    Invalida cache quando um agendamento é criado ou atualizado
    """
    cache_manager.invalidate_related_cache("appointment", instance.id)

    # Invalida horários disponíveis pois podem ter mudado
    if instance.barber:
        # Invalida cache de horários disponíveis para o barbeiro
        schedule_cache_patterns = [
            f"{CacheKeys.AVAILABLE_SLOTS}:schedule_id:{instance.barber.id}",
        ]
        for pattern in schedule_cache_patterns:
            cache_manager.invalidate_pattern(pattern)


@receiver(post_delete, sender="appointment.Appointment")
def invalidate_appointment_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida cache quando um agendamento é deletado
    """
    cache_manager.invalidate_related_cache("appointment", instance.id)

    # Invalida horários disponíveis pois podem ter mudado
    if instance.barber:
        schedule_cache_patterns = [
            f"{CacheKeys.AVAILABLE_SLOTS}:schedule_id:{instance.barber.id}",
        ]
        for pattern in schedule_cache_patterns:
            cache_manager.invalidate_pattern(pattern)


@receiver(post_save, sender="appointment.BarberSchedule")
def invalidate_schedule_cache(sender, instance, created, **kwargs):
    """
    Invalida cache quando uma agenda de barbeiro é criada ou atualizada
    """
    cache_manager.invalidate_related_cache("barberschedule", instance.id)

    # Invalida horários disponíveis pois a agenda mudou
    schedule_cache_patterns = [
        f"{CacheKeys.AVAILABLE_SLOTS}:schedule_id:{instance.id}",
    ]
    for pattern in schedule_cache_patterns:
        cache_manager.invalidate_pattern(pattern)


@receiver(post_delete, sender="appointment.BarberSchedule")
def invalidate_schedule_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida cache quando uma agenda de barbeiro é deletada
    """
    cache_manager.invalidate_related_cache("barberschedule", instance.id)

    # Invalida horários disponíveis
    schedule_cache_patterns = [
        f"{CacheKeys.AVAILABLE_SLOTS}:schedule_id:{instance.id}",
    ]
    for pattern in schedule_cache_patterns:
        cache_manager.invalidate_pattern(pattern)


@receiver(post_save, sender="review.Review")
def invalidate_review_cache(sender, instance, created, **kwargs):
    """
    Invalida cache quando uma avaliação é criada ou atualizada
    """
    cache_manager.invalidate_related_cache("review", instance.id)

    # Reviews afetam estatísticas de barbearias/barbeiros
    if instance.barbershop:
        cache_manager.invalidate_related_cache("barbershop", instance.barbershop.id)


@receiver(post_delete, sender="review.Review")
def invalidate_review_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida cache quando uma avaliação é deletada
    """
    cache_manager.invalidate_related_cache("review", instance.id)

    # Reviews afetam estatísticas de barbearias/barbeiros
    if instance.barbershop:
        cache_manager.invalidate_related_cache("barbershop", instance.barbershop.id)


@receiver(post_save, sender="user.User")
def invalidate_user_cache(sender, instance, created, **kwargs):
    """
    Invalida cache quando um usuário é criado ou atualizado
    """
    cache_manager.invalidate_related_cache("user", instance.id)


@receiver(post_delete, sender="user.User")
def invalidate_user_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida cache quando um usuário é deletado
    """
    cache_manager.invalidate_related_cache("user", instance.id)


def manual_cache_invalidation():
    """
    Função utilitária para invalidação manual completa do cache
    Útil para manutenção ou quando necessário limpar todo o cache
    """
    patterns_to_clear = [
        CacheKeys.BARBERSHOP_PREFIX,
        CacheKeys.SERVICE_PREFIX,
        CacheKeys.APPOINTMENT_PREFIX,
        CacheKeys.REVIEW_PREFIX,
        CacheKeys.USER_PREFIX,
        CacheKeys.SEARCH_PREFIX,
    ]

    for pattern in patterns_to_clear:
        cache_manager.invalidate_pattern(pattern)

    return "Cache invalidado manualmente para todos os padrões"


def get_cache_stats():
    """
    Função utilitária para obter estatísticas básicas do cache
    Útil para monitoramento e debug
    """
    try:
        # Para cache database, não temos estatísticas nativas
        # Retorna informações básicas
        return {
            "cache_backend": "django.core.cache.backends.db.DatabaseCache",
            "cache_tables": ["cache_table", "throttle_cache_table"],
            "status": "active",
            "message": "Cache database configurado e funcionando",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao obter estatísticas do cache: {str(e)}",
        }
