from rest_framework import permissions


class IsPaymentOwnerOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para permitir apenas o cliente dono do pagamento,
    o barbeiro do agendamento, o dono da barbearia ou admins.
    """

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o cliente do agendamento/pagamento
        if obj.appointment.customer == request.user:
            return True
        
        # Verificar se é o barbeiro do agendamento
        if obj.appointment.barber == request.user:
            return True
        
        # Verificar se é o dono da barbearia
        if obj.appointment.barbershop.owner == request.user:
            return True
        
        return False

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True


class IsBarberOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para permitir apenas barbeiros, donos de barbearia ou admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é barbeiro (chamando método)
        if request.user.is_barber():
            return True
        
        # Verificar se é dono de barbearia
        if request.user.is_barbershop_owner:
            return True
        
        return False


class IsClientOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para permitir apenas clientes, donos de barbearia ou admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é cliente (chamando método)
        if request.user.is_client():
            return True
        
        # Verificar se é dono de barbearia
        if request.user.is_barbershop_owner:
            return True
        
        return False


class IsPaymentCustomerOnly(permissions.BasePermission):
    """
    Permissão para permitir apenas o cliente dono do pagamento.
    """

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o cliente do agendamento/pagamento
        return obj.appointment.customer == request.user

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True


class IsPaymentBarbershopOwnerOnly(permissions.BasePermission):
    """
    Permissão para permitir apenas o dono da barbearia do pagamento.
    """

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o dono da barbearia
        return obj.appointment.barbershop.owner == request.user

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True


class CanManagePayments(permissions.BasePermission):
    """
    Permissão para gerenciar pagamentos (confirmar, reembolsar, etc.)
    Apenas admins e donos de barbearia podem gerenciar pagamentos.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é dono de barbearia
        if request.user.is_barbershop_owner:
            return True
        
        return False

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o dono da barbearia do pagamento
        if obj.appointment.barbershop.owner == request.user:
            return True
        
        return False
