from rest_framework import permissions

class IsBarbershopOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a barbershop to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class IsBarberInBarbershop(permissions.BasePermission):
    """
    Custom permission to only allow barbers to manage their own schedules.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.barber == request.user