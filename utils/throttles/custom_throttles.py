"""
Throttles personalizados para o sistema de barbearia

Este módulo contém implementações customizadas de throttling para diferentes
tipos de operações no sistema, fornecendo controle granular sobre rate limiting.
"""

from rest_framework.throttling import (
    UserRateThrottle,
    AnonRateThrottle,
    ScopedRateThrottle,
)
from django.contrib.auth.models import AnonymousUser


class AuthThrottle(ScopedRateThrottle):
    """
    Throttle específico para operações de autenticação.

    Aplica rate limiting mais restritivo para login, registro e operações sensíveis.
    """

    scope = "auth"

    def get_cache_key(self, request, view):
        # Usar IP para usuários anônimos, user ID para autenticados
        if isinstance(request.user, AnonymousUser):
            ident = self.get_ident(request)
        else:
            ident = request.user.pk

        return f"throttle_{self.scope}_{ident}"


class AuthBurstThrottle(ScopedRateThrottle):
    """
    Throttle para burst protection em autenticação (rate por minuto).

    Previne ataques de força bruta com limitação por minuto.
    """

    scope = "auth_burst"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"


class AppointmentThrottle(ScopedRateThrottle):
    """
    Throttle específico para agendamentos.

    Limita a criação de agendamentos para prevenir spam e abusos.
    """

    scope = "appointments"

    def get_cache_key(self, request, view):
        if isinstance(request.user, AnonymousUser):
            # Usuários anônimos não podem fazer agendamentos
            return None

        return f"throttle_{self.scope}_{request.user.pk}"


class PaymentThrottle(ScopedRateThrottle):
    """
    Throttle específico para operações de pagamento.

    Aplica rate limiting muito restritivo para operações financeiras.
    """

    scope = "payments"

    def get_cache_key(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return None

        return f"throttle_{self.scope}_{request.user.pk}"


class PaymentBurstThrottle(ScopedRateThrottle):
    """
    Throttle para burst protection em pagamentos (rate por minuto).

    Prevenção extra contra operações fraudulentas.
    """

    scope = "payment_burst"

    def get_cache_key(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return None

        return f"throttle_{self.scope}_{request.user.pk}"


class ReviewThrottle(ScopedRateThrottle):
    """
    Throttle específico para reviews e avaliações.

    Previne spam de avaliações mantendo a qualidade do feedback.
    """

    scope = "reviews"

    def get_cache_key(self, request, view):
        if isinstance(request.user, AnonymousUser):
            ident = self.get_ident(request)
        else:
            ident = request.user.pk

        return f"throttle_{self.scope}_{ident}"


class SearchThrottle(ScopedRateThrottle):
    """
    Throttle para operações de busca.

    Permite mais requisições para busca mantendo performance do sistema.
    """

    scope = "search"

    def get_cache_key(self, request, view):
        if isinstance(request.user, AnonymousUser):
            ident = self.get_ident(request)
        else:
            ident = request.user.pk

        return f"throttle_{self.scope}_{ident}"


class AdminThrottle(UserRateThrottle):
    """
    Throttle específico para usuários administrativos.

    Rate limit mais alto para operações administrativas.
    """

    scope = "admin"

    def allow_request(self, request, view):
        # Só aplica throttling se o usuário for staff/admin
        if not request.user.is_authenticated:
            return True

        if not (request.user.is_staff or request.user.is_superuser):
            return True

        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return None

        if not (request.user.is_staff or request.user.is_superuser):
            return None

        return f"throttle_{self.scope}_{request.user.pk}"


class PasswordResetThrottle(ScopedRateThrottle):
    """
    Throttle específico para reset de senha.

    Rate limiting muito restritivo para prevenir abuso do sistema de reset.
    """

    scope = "password_reset"

    def get_cache_key(self, request, view):
        # Sempre usar IP para reset de senha
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"


class CustomAnonRateThrottle(AnonRateThrottle):
    """
    Throttle customizado para usuários anônimos com logging.
    """

    def throttle_failure(self):
        """
        Log quando throttling é ativado para análise
        """
        import logging

        logger = logging.getLogger("api_usage")
        logger.warning(
            f"Throttle activated for anonymous user: {self.get_ident(self.request)}"
        )
        return super().throttle_failure()


class CustomUserRateThrottle(UserRateThrottle):
    """
    Throttle customizado para usuários autenticados com logging.
    """

    def throttle_failure(self):
        """
        Log quando throttling é ativado para análise
        """
        import logging

        logger = logging.getLogger("api_usage")
        if hasattr(self, "request") and self.request.user.is_authenticated:
            logger.warning(
                f"Throttle activated for user: {self.request.user.username} (ID: {self.request.user.pk})"
            )
        return super().throttle_failure()
