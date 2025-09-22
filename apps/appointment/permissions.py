from rest_framework import permissions


class IsAppointmentOwnerOrBarbershopOwner(permissions.BasePermission):
    """
    Permissão para permitir apenas o cliente dono do agendamento,
    o barbeiro do agendamento, o dono da barbearia ou admins.
    """

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o cliente do agendamento
        if obj.customer.customer == request.user:
            return True
        
        # Verificar se é o barbeiro do agendamento
        if obj.barber == request.user:
            return True
        
        # Verificar se é o dono da barbearia
        if obj.barbershop.owner == request.user:
            return True
        
        return False


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
        
        # Verificar se é barbeiro (usando property)
        if request.user.is_barber:
            return True
        
        # Verificar se é dono de barbearia
        if request.user.is_barbershop_owner:
            return True
        
        return False


class IsBarberScheduleOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para permitir apenas o barbeiro dono da agenda,
    o dono da barbearia ou admins.
    """

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o barbeiro da agenda
        if obj.barber == request.user:
            return True
        
        # Verificar se é o dono da barbearia
        if obj.barbershop.owner == request.user:
            return True
        
        return False

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Para criação, verificar se é barbeiro ou dono de barbearia
        if view.action == 'create':
            # Verificar se é admin
            if hasattr(request.user, 'role') and request.user.role == "ADMIN":
                return True
            
            # Verificar se é barbeiro (chamando o método)
            if request.user.is_barber():
                return True
            
            # Verificar se é dono de barbearia
            if request.user.is_barbershop_owner:
                return True
            
            return False
        
        return True


class IsCustomerOrBarbershopOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão para permitir apenas clientes, donos de barbearia ou admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é cliente (usando property)
        if request.user.is_customer:
            return True
        
        # Verificar se é dono de barbearia
        if request.user.is_barbershop_owner:
            return True
        
        return False


class IsAppointmentParticipantOrAdmin(permissions.BasePermission):
    """
    Permissão para permitir apenas participantes do agendamento
    (cliente, barbeiro, dono da barbearia) ou admins.
    """

    def has_object_permission(self, request, view, obj):
        # Verificar se é admin
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Verificar se é o cliente do agendamento
        if obj.customer.customer == request.user:
            return True
        
        # Verificar se é o barbeiro do agendamento
        if obj.barber == request.user:
            return True
        
        # Verificar se é o dono da barbearia
        if obj.barbershop.owner == request.user:
            return True
        
        return False


class CanManageAppointments(permissions.BasePermission):
    """
    Permissão para verificar se o usuário pode gerenciar agendamentos.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins podem gerenciar todos os agendamentos
        if hasattr(request.user, 'role') and request.user.role == "ADMIN":
            return True
        
        # Barbeiros podem gerenciar seus próprios agendamentos
        if request.user.is_barber:
            return True
        
        # Donos de barbearia podem gerenciar agendamentos de suas barbearias
        if request.user.is_barbershop_owner:
            return True
        
        # Clientes podem ver e criar agendamentos
        if request.user.is_customer:
            return view.action in ['list', 'retrieve', 'create']
        
        return False