from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()


class IsBarberOrAdmin(permissions.BasePermission):
    """
    Permissão para barbeiros e administradores
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return (
            request.user.role in [User.Role.BARBER, User.Role.ADMIN]
            or request.user.is_barbershop_owner
        )


class IsOwnerOrBarberOrAdmin(permissions.BasePermission):
    """
    Permissão para proprietário do recurso, barbeiros ou administradores
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True

        # Para agendamentos, verificar se é cliente, barbeiro ou proprietário da barbearia
        if hasattr(obj, "customer"):  # Appointment
            return (
                obj.customer.customer == request.user  # Cliente do agendamento
                or obj.barber == request.user  # Barbeiro do agendamento
                or obj.barbershop.owner == request.user  # Proprietário da barbearia
            )

        # Para horários de barbeiro, verificar se é o próprio barbeiro ou proprietário da barbearia
        if hasattr(obj, "barber"):  # BarberSchedule
            return (
                obj.barber == request.user  # O próprio barbeiro
                or obj.barbershop.owner == request.user  # Proprietário da barbearia
            )

        return False


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permissão para participantes do agendamento (cliente, barbeiro, proprietário da barbearia)
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True

        # Verificar se é cliente, barbeiro ou proprietário da barbearia
        return (
            obj.customer.customer == request.user  # Cliente
            or obj.barber == request.user  # Barbeiro
            or obj.barbershop.owner == request.user  # Proprietário da barbearia
        )


class IsBarberScheduleOwner(permissions.BasePermission):
    """
    Permissão para o barbeiro proprietário do horário ou proprietário da barbearia
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True

        return (
            obj.barber == request.user  # O próprio barbeiro
            or obj.barbershop.owner == request.user  # Proprietário da barbearia
        )


class CanManageAppointments(permissions.BasePermission):
    """
    Permissão para gerenciar agendamentos (barbeiros, proprietários de barbearias ou admins)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return (
            request.user.role in [User.Role.BARBER, User.Role.ADMIN]
            or request.user.is_barbershop_owner
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True

        # Verificar se é barbeiro do agendamento ou proprietário da barbearia
        return obj.barber == request.user or obj.barbershop.owner == request.user


class CanCreateAppointment(permissions.BasePermission):
    """
    Permissão para criar agendamentos (todos os usuários autenticados)
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsReadOnlyOrOwner(permissions.BasePermission):
    """
    Permissão somente leitura para todos, escrita apenas para proprietários
    """

    def has_permission(self, request, view):
        if request.method in permissions.READONLY_METHODS:
            return True

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.READONLY_METHODS:
            return True

        if request.user.role == User.Role.ADMIN:
            return True

        # Para modificações, verificar se é proprietário
        if hasattr(obj, "customer"):  # Appointment
            return (
                obj.customer.customer == request.user
                or obj.barber == request.user
                or obj.barbershop.owner == request.user
            )

        if hasattr(obj, "barber"):  # BarberSchedule
            return obj.barber == request.user or obj.barbershop.owner == request.user

        return False
