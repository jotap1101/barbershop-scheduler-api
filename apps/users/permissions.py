from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a barbershop to edit it.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action in ['list', 'create']:
            return request.user.role == 'OWNER'
        
        # For detail endpoints, check if user is owner of related barbershop
        pk = view.kwargs.get('pk')
        if pk and hasattr(view.queryset.model, 'barbershop'):
            return view.queryset.model.objects.filter(
                barbershop__owner=request.user,
                pk=pk
            ).exists()
            
        return request.user.role == 'OWNER'

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'barbershop'):
            return obj.barbershop.owner == request.user
        return False

class IsBarber(permissions.BasePermission):
    """
    Custom permission to only allow barbers to access specific views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'BARBER'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if the barber is associated with the barbershop
        if hasattr(obj, 'barbershop'):
            return request.user.barber_profile.barbershops.filter(id=obj.barbershop.id).exists()
        elif hasattr(obj, 'barber'):
            return obj.barber == request.user
        return False

class IsClient(permissions.BasePermission):
    """
    Custom permission to only allow clients to access specific views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'CLIENT'

    def has_object_permission(self, request, view, obj):
        # Clients can only view their own appointments/payments
        if hasattr(obj, 'customer'):
            return obj.customer.customer == request.user
        return False

class IsBarberOrOwner(permissions.BasePermission):
    """
    Custom permission to allow both barbers and owners to access views.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if view.action == 'create':
            return request.user.role == 'BARBER'
            
        return request.user.role in ['BARBER', 'OWNER']

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'OWNER':
            if hasattr(obj, 'owner'):
                return obj.owner == request.user
            elif hasattr(obj, 'barbershop'):
                return obj.barbershop.owner == request.user
        elif request.user.role == 'BARBER':
            if hasattr(obj, 'barbershop'):
                return request.user.barber_profile.barbershops.filter(id=obj.barbershop.id).exists()
            elif hasattr(obj, 'barber'):
                return obj.barber == request.user
        return False

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False