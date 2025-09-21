from rest_framework import permissions


class IsOwnerOrAdminBarbershop(permissions.BasePermission):
    """
    Custom permission to only allow owners of a barbershop or admins.
    """

    def has_object_permission(self, request, view, obj):
        # Check if user is the owner of the barbershop or admin
        return obj.owner == request.user or request.user.role == "ADMIN"


class IsBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow barbershop owners or admins.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_barbershop_owner or request.user.role == "ADMIN")
        )


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a barbershop, admins or read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the barbershop or admin users.
        return obj.owner == request.user or request.user.role == "ADMIN"


class IsServiceOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of the barbershop that owns the service or admins.
    """

    def has_object_permission(self, request, view, obj):
        # Check if user is the owner of the barbershop that owns this service or admin
        return obj.barbershop.owner == request.user or request.user.role == "ADMIN"


class IsServiceOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of the barbershop that owns the service, admins or read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the barbershop or admin users.
        return obj.barbershop.owner == request.user or request.user.role == "ADMIN"


class IsBarbershopCustomerOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of the barbershop that has the customer relationship or admins.
    """

    def has_object_permission(self, request, view, obj):
        # Check if user is the owner of the barbershop or admin
        return obj.barbershop.owner == request.user or request.user.role == "ADMIN"


class IsCustomerOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow the customer themselves, barbershop owner, or admins.
    """

    def has_object_permission(self, request, view, obj):
        # Allow the customer themselves, barbershop owner, or admins
        return (
            obj.customer == request.user
            or obj.barbershop.owner == request.user
            or request.user.role == "ADMIN"
        )
