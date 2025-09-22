from rest_framework import permissions

from apps.review.models import Review


class IsReviewOwnerOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão que permite acesso apenas ao dono da avaliação,
    dono da barbearia ou admin.
    """

    def has_object_permission(self, request, view, obj):
        # Admins têm acesso total
        if hasattr(request.user, 'role') and request.user.role == 'ADMIN':
            return True

        # Donos de barbearia podem ver avaliações de sua barbearia
        if hasattr(request.user, 'is_barbershop_owner') and request.user.is_barbershop_owner:
            if obj.barbershop.owner == request.user:
                return True

        # Cliente que fez a avaliação pode ver/editar
        if obj.barbershop_customer.customer == request.user:
            return True

        # Barbeiro avaliado pode ver a avaliação
        if obj.barber == request.user:
            return True

        return False


class CanCreateReview(permissions.BasePermission):
    """
    Permissão para criar avaliações.
    Apenas clientes autenticados podem criar avaliações.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Apenas clientes podem criar avaliações
        return hasattr(request.user, 'role') and request.user.role == 'CLIENT'


class CanUpdateOwnReview(permissions.BasePermission):
    """
    Permissão para atualizar próprias avaliações.
    """

    def has_object_permission(self, request, view, obj):
        # Apenas o cliente que criou a avaliação pode editá-la
        return obj.barbershop_customer.customer == request.user


class CanDeleteReview(permissions.BasePermission):
    """
    Permissão para deletar avaliações.
    Apenas o dono da avaliação, dono da barbearia ou admin.
    """

    def has_object_permission(self, request, view, obj):
        # Admins podem deletar qualquer avaliação
        if hasattr(request.user, 'role') and request.user.role == 'ADMIN':
            return True

        # Donos de barbearia podem deletar avaliações de sua barbearia
        if hasattr(request.user, 'is_barbershop_owner') and request.user.is_barbershop_owner:
            if obj.barbershop.owner == request.user:
                return True

        # Cliente que fez a avaliação pode deletá-la
        if obj.barbershop_customer.customer == request.user:
            return True

        return False


class CanViewReviewStatistics(permissions.BasePermission):
    """
    Permissão para visualizar estatísticas de avaliações.
    Barbeiros, donos de barbearia e admins.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admins têm acesso total
        if hasattr(request.user, 'role') and request.user.role == 'ADMIN':
            return True

        # Donos de barbearia podem ver estatísticas
        if hasattr(request.user, 'is_barbershop_owner') and request.user.is_barbershop_owner:
            return True

        # Barbeiros podem ver suas próprias estatísticas
        if hasattr(request.user, 'role') and request.user.role == 'BARBER':
            return True

        return False


class IsBarberOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para barbeiros, donos de barbearia ou admins.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admins têm acesso
        if hasattr(request.user, 'role') and request.user.role == 'ADMIN':
            return True

        # Donos de barbearia têm acesso
        if hasattr(request.user, 'is_barbershop_owner') and request.user.is_barbershop_owner:
            return True

        # Barbeiros têm acesso
        if hasattr(request.user, 'role') and request.user.role == 'BARBER':
            return True

        return False
