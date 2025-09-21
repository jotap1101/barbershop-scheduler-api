from rest_framework import permissions


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object, admins or read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object or admin users.
        return obj == request.user or request.user.role == "ADMIN"


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit, but allow read access to all authenticated users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins.
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.role == "ADMIN"
