from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Appointment, BarberSchedule
from .permissions import (
    IsAppointmentOwnerOrBarbershopOwner,
    IsBarberOrBarbershopOwnerOrAdmin,
    IsBarberScheduleOwnerOrAdmin,
)
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentSerializer,
    AppointmentUpdateSerializer,
    BarberScheduleCreateSerializer,
    BarberScheduleDetailSerializer,
    BarberScheduleListSerializer,
    BarberScheduleSerializer,
    BarberScheduleUpdateSerializer,
)
from utils.throttles.custom_throttles import AppointmentThrottle, SearchThrottle


@extend_schema_view(
    list=extend_schema(
        summary="Listar agendas dos barbeiros",
        description="Lista todas as agendas dos barbeiros com paginação e filtros.",
        tags=["appointments"],
    ),
    create=extend_schema(
        summary="Criar agenda de barbeiro",
        description="Cria uma nova agenda para um barbeiro.",
        tags=["appointments"],
    ),
    retrieve=extend_schema(
        summary="Detalhar agenda de barbeiro",
        description="Retorna os detalhes de uma agenda específica.",
        tags=["appointments"],
    ),
    update=extend_schema(
        summary="Atualizar agenda de barbeiro",
        description="Atualiza todos os campos de uma agenda.",
        tags=["appointments"],
    ),
    partial_update=extend_schema(
        summary="Atualizar agenda parcialmente",
        description="Atualiza alguns campos de uma agenda.",
        tags=["appointments"],
    ),
    destroy=extend_schema(
        summary="Deletar agenda de barbeiro",
        description="Remove uma agenda do sistema.",
        tags=["appointments"],
    ),
)
class BarberScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar agendas dos barbeiros com operações CRUD e ações customizadas.
    """

    queryset = BarberSchedule.objects.select_related("barber", "barbershop").all()
    serializer_class = BarberScheduleSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [SearchThrottle]  # Throttling para buscas de horários
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["barber", "barbershop", "weekday", "is_available"]
    search_fields = ["barber__first_name", "barber__last_name", "barbershop__name"]
    ordering_fields = ["weekday", "start_time", "end_time"]
    ordering = ["weekday", "start_time"]

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return BarberScheduleCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return BarberScheduleUpdateSerializer
        elif self.action == "retrieve":
            return BarberScheduleDetailSerializer
        elif self.action == "list":
            return BarberScheduleListSerializer
        return BarberScheduleSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action == "create":
            permission_classes = [IsAuthenticated, IsBarberScheduleOwnerOrAdmin]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsBarberScheduleOwnerOrAdmin]
        elif self.action in ["available_slots", "my_schedules"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Minhas agendas",
        description="Retorna as agendas do barbeiro autenticado.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"], url_path="my-schedules")
    def my_schedules(self, request):
        """
        Retorna as agendas do barbeiro autenticado.
        """
        schedules = BarberSchedule.objects.filter(barber=request.user)

        # Aplicar filtros
        barbershop = request.query_params.get("barbershop", None)
        if barbershop:
            schedules = schedules.filter(barbershop_id=barbershop)

        weekday = request.query_params.get("weekday", None)
        if weekday:
            schedules = schedules.filter(weekday=weekday)

        is_available = request.query_params.get("is_available", None)
        if is_available is not None:
            schedules = schedules.filter(is_available=is_available.lower() == "true")

        page = self.paginate_queryset(schedules)
        if page is not None:
            serializer = BarberScheduleListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = BarberScheduleListSerializer(
            schedules, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Horários disponíveis",
        description="Retorna os horários disponíveis para uma agenda específica em uma data.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["get"], url_path="available-slots")
    def available_slots(self, request, pk=None):
        """
        Retorna os horários disponíveis para uma agenda específica em uma data.
        """
        schedule = self.get_object()

        # Parâmetros da requisição
        date_param = request.query_params.get("date")
        if not date_param:
            return Response(
                {"error": "Parâmetro 'date' é obrigatório (formato: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_duration = request.query_params.get("duration", 30)
        try:
            service_duration = int(service_duration)
        except ValueError:
            service_duration = 30

        # Obter horários disponíveis
        slots = schedule.get_available_slots(target_date, service_duration)

        return Response(
            {
                "date": target_date,
                "weekday": target_date.weekday(),
                "available_slots": [slot.strftime("%H:%M") for slot in slots],
                "total_slots": len(slots),
            }
        )


@extend_schema_view(
    list=extend_schema(
        summary="Listar agendamentos",
        description="Lista todos os agendamentos com paginação e filtros.",
        tags=["appointments"],
    ),
    create=extend_schema(
        summary="Criar agendamento",
        description="Cria um novo agendamento no sistema.",
        tags=["appointments"],
    ),
    retrieve=extend_schema(
        summary="Detalhar agendamento",
        description="Retorna os detalhes de um agendamento específico.",
        tags=["appointments"],
    ),
    update=extend_schema(
        summary="Atualizar agendamento",
        description="Atualiza todos os campos de um agendamento.",
        tags=["appointments"],
    ),
    partial_update=extend_schema(
        summary="Atualizar agendamento parcialmente",
        description="Atualiza alguns campos de um agendamento.",
        tags=["appointments"],
    ),
    destroy=extend_schema(
        summary="Cancelar agendamento",
        description="Cancela um agendamento do sistema.",
        tags=["appointments"],
    ),
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar agendamentos com operações CRUD e ações customizadas.
    """

    queryset = Appointment.objects.select_related(
        "customer__customer", "barber", "service", "barbershop"
    ).all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AppointmentThrottle]  # Throttling específico para agendamentos
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "customer",
        "barber",
        "service",
        "barbershop",
        "status",
    ]
    search_fields = [
        "customer__customer__first_name",
        "customer__customer__last_name",
        "barber__first_name",
        "barber__last_name",
        "service__name",
        "barbershop__name",
    ]
    ordering_fields = ["start_datetime", "created_at", "updated_at"]
    ordering = ["-start_datetime"]

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return AppointmentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return AppointmentUpdateSerializer
        elif self.action == "retrieve":
            return AppointmentDetailSerializer
        elif self.action == "list":
            return AppointmentListSerializer
        return AppointmentSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated, IsAppointmentOwnerOrBarbershopOwner]
        elif self.action == "create":
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsAppointmentOwnerOrBarbershopOwner]
        elif self.action in [
            "my_appointments",
            "barber_appointments",
            "today_appointments",
            "upcoming_appointments",
            "confirm",
            "cancel",
            "complete",
        ]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def destroy(self, request, *args, **kwargs):
        """
        Cancela o agendamento ao invés de deletar.
        """
        appointment = self.get_object()
        if appointment.cancel():
            return Response(
                {"message": "Agendamento cancelado com sucesso"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Não é possível cancelar este agendamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Meus agendamentos",
        description="Retorna os agendamentos do usuário autenticado (cliente).",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"], url_path="my-appointments")
    def my_appointments(self, request):
        """
        Retorna os agendamentos do usuário autenticado (cliente).
        """
        appointments = Appointment.objects.filter(
            customer__customer=request.user
        ).select_related("customer__customer", "barber", "service", "barbershop")

        # Filtros
        status_filter = request.query_params.get("status")
        if status_filter:
            appointments = appointments.filter(status=status_filter)

        barbershop = request.query_params.get("barbershop")
        if barbershop:
            appointments = appointments.filter(barbershop_id=barbershop)

        # Filtros de data
        today_only = request.query_params.get("today", "false").lower() == "true"
        if today_only:
            appointments = appointments.filter(
                start_datetime__date=timezone.now().date()
            )

        upcoming_only = request.query_params.get("upcoming", "false").lower() == "true"
        if upcoming_only:
            appointments = appointments.filter(start_datetime__gt=timezone.now())

        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = AppointmentListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(
            appointments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Agendamentos do barbeiro",
        description="Retorna os agendamentos do barbeiro autenticado.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"], url_path="barber-appointments")
    def barber_appointments(self, request):
        """
        Retorna os agendamentos do barbeiro autenticado.
        """
        appointments = Appointment.objects.filter(barber=request.user).select_related(
            "customer__customer", "barber", "service", "barbershop"
        )

        # Filtros
        status_filter = request.query_params.get("status")
        if status_filter:
            appointments = appointments.filter(status=status_filter)

        barbershop = request.query_params.get("barbershop")
        if barbershop:
            appointments = appointments.filter(barbershop_id=barbershop)

        # Filtros de data
        today_only = request.query_params.get("today", "false").lower() == "true"
        if today_only:
            appointments = appointments.filter(
                start_datetime__date=timezone.now().date()
            )

        upcoming_only = request.query_params.get("upcoming", "false").lower() == "true"
        if upcoming_only:
            appointments = appointments.filter(start_datetime__gt=timezone.now())

        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = AppointmentListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(
            appointments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Agendamentos de hoje",
        description="Retorna todos os agendamentos para hoje.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"], url_path="today")
    def today_appointments(self, request):
        """
        Retorna os agendamentos de hoje.
        """
        appointments = Appointment.get_today_appointments()

        # Filtros adicionais
        barber = request.query_params.get("barber")
        if barber:
            appointments = appointments.filter(barber_id=barber)

        barbershop = request.query_params.get("barbershop")
        if barbershop:
            appointments = appointments.filter(barbershop_id=barbershop)

        status_filter = request.query_params.get("status")
        if status_filter:
            appointments = appointments.filter(status=status_filter)

        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = AppointmentListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(
            appointments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Próximos agendamentos",
        description="Retorna os agendamentos futuros (próximos 7 dias por padrão).",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming_appointments(self, request):
        """
        Retorna os agendamentos futuros.
        """
        days = request.query_params.get("days", 7)
        try:
            days = int(days)
        except ValueError:
            days = 7

        appointments = Appointment.get_upcoming_appointments(days=days)

        # Filtros adicionais
        barber = request.query_params.get("barber")
        if barber:
            appointments = appointments.filter(barber_id=barber)

        barbershop = request.query_params.get("barbershop")
        if barbershop:
            appointments = appointments.filter(barbershop_id=barbershop)

        status_filter = request.query_params.get("status")
        if status_filter:
            appointments = appointments.filter(status=status_filter)

        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = AppointmentListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = AppointmentListSerializer(
            appointments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Confirmar agendamento",
        description="Confirma um agendamento pendente.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        Confirma um agendamento.
        """
        appointment = self.get_object()
        if appointment.confirm():
            return Response(
                {"message": "Agendamento confirmado com sucesso"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Não é possível confirmar este agendamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Cancelar agendamento",
        description="Cancela um agendamento.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancela um agendamento.
        """
        appointment = self.get_object()
        if appointment.cancel():
            return Response(
                {"message": "Agendamento cancelado com sucesso"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Não é possível cancelar este agendamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Marcar como concluído",
        description="Marca um agendamento como concluído.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Marca um agendamento como concluído.
        """
        appointment = self.get_object()
        if appointment.complete():
            return Response(
                {"message": "Agendamento marcado como concluído"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Não é possível marcar este agendamento como concluído"},
                status=status.HTTP_400_BAD_REQUEST,
            )
