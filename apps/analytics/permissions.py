from rest_framework import permissions


class IsAnalyticsAdmin(permissions.BasePermission):
    """
    Permissão customizada para analytics de administrador.
    Permite acesso apenas para administradores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'ADMIN'
        )


class IsBarbershopOwnerOrAnalyticsAdmin(permissions.BasePermission):
    """
    Permissão para proprietários de barbearia ou administradores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (
                (hasattr(request.user, 'role') and request.user.role == 'ADMIN') or
                (hasattr(request.user, 'is_barbershop_owner') and request.user.is_barbershop_owner)
            )
        )


class IsBarberOrOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para barbeiros, proprietários ou administradores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (
                (hasattr(request.user, 'role') and request.user.role in ['ADMIN', 'BARBER']) or
                (hasattr(request.user, 'is_barbershop_owner') and request.user.is_barbershop_owner)
            )
        )