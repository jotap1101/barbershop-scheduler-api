from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.appointment.models import Appointment, BarberSchedule
from apps.appointment.permissions import (
    IsAppointmentParticipant,
    IsBarberSchedulePermission,
    IsOwnerOrBarberOrAdmin,
)
from apps.appointment.serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentSerializer,
    AvailableSlotsSerializer,
    BarberScheduleDetailSerializer,
    BarberScheduleListSerializer,
    BarberScheduleSerializer,
)
from apps.appointment.utils import (
    bulk_create_barber_schedules,
    calculate_appointment_revenue,
    get_all_available_slots,
    get_barber_stats,
    get_barbershop_appointments_for_period,
)
from apps.barbershop.models import Barbershop, Service

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar horários de barbeiros",
        description="Retorna uma lista paginada de horários de barbeiros.",
        tags=["appointments"],
    ),
    retrieve=extend_schema(
        summary="Detalhes do horário do barbeiro",
        description="Retorna os detalhes de um horário específico do barbeiro.",
        tags=["appointments"],
    ),
    create=extend_schema(
        summary="Criar horário de barbeiro",
        description="Cria um novo horário para um barbeiro.",
        tags=["appointments"],
    ),
    update=extend_schema(
        summary="Atualizar horário de barbeiro",
        description="Atualiza um horário existente do barbeiro.",
        tags=["appointments"],
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente horário de barbeiro",
        description="Atualiza parcialmente um horário existente do barbeiro.",
        tags=["appointments"],
    ),
    destroy=extend_schema(
        summary="Deletar horário de barbeiro",
        description="Deleta um horário existente do barbeiro.",
        tags=["appointments"],
    ),
)
class BarberScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar horários de barbeiros
    """

    queryset = BarberSchedule.objects.all().select_related("barber", "barbershop")
    permission_classes = [IsBarberSchedulePermission]
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
        if self.action == "list":
            return BarberScheduleListSerializer
        elif self.action == "retrieve":
            return BarberScheduleDetailSerializer
        return BarberScheduleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Se não é admin, mostrar apenas horários relacionados ao usuário
        if not user.is_staff and user.role != User.Role.ADMIN:
            if user.role == User.Role.BARBER:
                # Barbeiro vê apenas seus próprios horários
                queryset = queryset.filter(barber=user)
            elif user.is_barbershop_owner:
                # Proprietário vê horários de sua barbearia
                queryset = queryset.filter(barbershop__owner=user)
            else:
                # Cliente vê apenas horários ativos para agendamento
                queryset = queryset.filter(is_available=True)

        return queryset

    @extend_schema(
        summary="Horários do barbeiro",
        description="Retorna os horários do barbeiro logado.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def my_schedules(self, request):
        """
        Retorna os horários do barbeiro logado
        """
        if request.user.role not in [User.Role.BARBER, User.Role.ADMIN]:
            return Response(
                {"error": "Apenas barbeiros podem acessar seus horários"},
                status=status.HTTP_403_FORBIDDEN,
            )

        schedules = self.get_queryset().filter(barber=request.user)
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Horários por barbearia",
        description="Retorna os horários filtrados por barbearia.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def by_barbershop(self, request):
        """
        Retorna horários filtrados por barbearia
        """
        barbershop_id = request.query_params.get("barbershop_id")
        if not barbershop_id:
            return Response(
                {"error": "barbershop_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            barbershop = Barbershop.objects.get(id=barbershop_id)
        except Barbershop.DoesNotExist:
            return Response(
                {"error": "Barbearia não encontrada"}, status=status.HTTP_404_NOT_FOUND
            )

        schedules = self.get_queryset().filter(barbershop=barbershop)
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Horários disponíveis",
        description="Retorna horários disponíveis para agendamento.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def available_slots(self, request):
        """
        Retorna horários disponíveis para agendamento
        """
        serializer = AvailableSlotsSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        barbershop = get_object_or_404(Barbershop, id=data["barbershop_id"])

        service = None
        if data.get("service_id"):
            service = get_object_or_404(Service, id=data["service_id"])

        barber = None
        if data.get("barber_id"):
            barber = get_object_or_404(User, id=data["barber_id"])

        slots = get_all_available_slots(
            barbershop=barbershop, date_obj=data["date"], service=service, barber=barber
        )

        return Response(
            {
                "barbershop": barbershop.name,
                "date": data["date"].strftime("%Y-%m-%d"),
                "service": service.name if service else None,
                "available_slots": slots,
            }
        )

    @extend_schema(
        summary="Criar múltiplos horários",
        description="Cria múltiplos horários de uma vez.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """
        Cria múltiplos horários de uma vez
        """
        if (
            request.user.role not in [User.Role.BARBER, User.Role.ADMIN]
            and not request.user.is_barbershop_owner
        ):
            return Response(
                {"error": "Sem permissão para criar horários"},
                status=status.HTTP_403_FORBIDDEN,
            )

        barber_id = request.data.get("barber_id")
        barbershop_id = request.data.get("barbershop_id")
        schedules_data = request.data.get("schedules", [])

        if not all([barber_id, barbershop_id, schedules_data]):
            return Response(
                {"error": "barber_id, barbershop_id e schedules são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            barber = User.objects.get(
                id=barber_id, role__in=[User.Role.BARBER, User.Role.ADMIN]
            )
            barbershop = Barbershop.objects.get(id=barbershop_id)
        except (User.DoesNotExist, Barbershop.DoesNotExist):
            return Response(
                {"error": "Barbeiro ou barbearia não encontrados"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verificar permissões
        if (
            request.user != barber
            and request.user != barbershop.owner
            and request.user.role != User.Role.ADMIN
        ):
            return Response(
                {
                    "error": "Sem permissão para criar horários para este barbeiro/barbearia"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            created_schedules = bulk_create_barber_schedules(
                barber=barber, barbershop=barbershop, schedules_data=schedules_data
            )

            serializer = BarberScheduleSerializer(created_schedules, many=True)
            return Response(
                {
                    "message": f"{len(created_schedules)} horários criados com sucesso",
                    "schedules": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"Erro ao criar horários: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Alterar disponibilidade",
        description="Alterna disponibilidade de um horário.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def toggle_availability(self, request, pk=None):
        """
        Alterna disponibilidade de um horário
        """
        schedule = self.get_object()
        schedule.is_available = not schedule.is_available
        schedule.save(update_fields=["is_available"])

        return Response(
            {
                "message": f'Horário {"ativado" if schedule.is_available else "desativado"} com sucesso',
                "is_available": schedule.is_available,
            }
        )

    @extend_schema(
        summary="Listar barbeiros que estão trabalhando agora",
        description="Retorna uma lista de barbeiros que estão trabalhando no momento.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def working_now(self, request):
        """
        Retorna barbeiros que estão trabalhando agora
        """
        now = timezone.now()
        current_weekday = now.weekday()
        current_time = now.time()

        working_schedules = self.get_queryset().filter(
            weekday=current_weekday,
            start_time__lte=current_time,
            end_time__gt=current_time,
            is_available=True,
        )

        serializer = self.get_serializer(working_schedules, many=True)
        return Response(
            {
                "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "working_barbers": serializer.data,
            }
        )


@extend_schema_view(
    list=extend_schema(
        summary="Listar agendamentos",
        description="Retorna uma lista paginada de agendamentos.",
        tags=["appointments"],
    ),
    retrieve=extend_schema(
        summary="Detalhes do agendamento",
        description="Retorna os detalhes de um agendamento específico.",
        tags=["appointments"],
    ),
    create=extend_schema(
        summary="Criar agendamento",
        description="Cria um novo agendamento.",
        tags=["appointments"],
    ),
    update=extend_schema(
        summary="Atualizar agendamento",
        description="Atualiza um agendamento existente.",
        tags=["appointments"],
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente agendamento",
        description="Atualiza parcialmente um agendamento existente.",
        tags=["appointments"],
    ),
    destroy=extend_schema(
        summary="Deletar agendamento",
        description="Deleta um agendamento existente.",
        tags=["appointments"],
    ),
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar agendamentos
    """

    queryset = Appointment.objects.all().select_related(
        "customer__customer", "barber", "service", "barbershop"
    )
    permission_classes = [IsAppointmentParticipant]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["barber", "barbershop", "service", "status"]
    search_fields = [
        "customer__customer__first_name",
        "customer__customer__last_name",
        "barber__first_name",
        "barber__last_name",
        "service__name",
    ]
    ordering_fields = ["start_datetime", "created_at", "final_price"]
    ordering = ["-start_datetime"]

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        elif self.action == "list":
            return AppointmentListSerializer
        elif self.action == "retrieve":
            return AppointmentDetailSerializer
        return AppointmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrar por usuário se não for admin
        if not user.is_staff and user.role != User.Role.ADMIN:
            if user.role == User.Role.BARBER:
                # Barbeiro vê agendamentos dele
                queryset = queryset.filter(barber=user)
            elif user.is_barbershop_owner:
                # Proprietário vê agendamentos da barbearia
                queryset = queryset.filter(barbershop__owner=user)
            else:
                # Cliente vê apenas seus agendamentos
                queryset = queryset.filter(customer__customer=user)

        return queryset

    def perform_create(self, serializer):
        """
        Customizar criação de agendamento
        """
        # Se o usuário é cliente, garantir que o agendamento seja para ele
        if self.request.user.role == User.Role.CLIENT:
            # Buscar ou criar BarbershopCustomer
            from apps.barbershop.models import BarbershopCustomer

            barbershop = serializer.validated_data["barbershop"]
            customer, created = BarbershopCustomer.objects.get_or_create(
                customer=self.request.user, barbershop=barbershop
            )
            serializer.save(customer=customer)
        else:
            serializer.save()

    @extend_schema(
        summary="Listar agendamentos do usuário",
        description="Retorna uma lista paginada de agendamentos do usuário logado.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def my_appointments(self, request):
        """
        Retorna agendamentos do usuário logado
        """
        user = request.user
        appointments = self.get_queryset()

        if user.role == User.Role.CLIENT:
            appointments = appointments.filter(customer__customer=user)
        elif user.role == User.Role.BARBER:
            appointments = appointments.filter(barber=user)
        elif user.is_barbershop_owner:
            appointments = appointments.filter(barbershop__owner=user)

        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Listar agendamentos de hoje",
        description="Retorna uma lista paginada de agendamentos de hoje.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def today(self, request):
        """
        Retorna agendamentos de hoje
        """
        today_appointments = self.get_queryset().filter(
            start_datetime__date=date.today()
        )

        serializer = self.get_serializer(today_appointments, many=True)
        return Response(
            {
                "date": date.today().strftime("%Y-%m-%d"),
                "total_appointments": today_appointments.count(),
                "appointments": serializer.data,
            }
        )

    @extend_schema(
        summary="Listar próximos agendamentos",
        description="Retorna uma lista paginada de próximos agendamentos.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """
        Retorna próximos agendamentos
        """
        days = int(request.query_params.get("days", 7))
        start_date = timezone.now()
        end_date = start_date + timedelta(days=days)

        upcoming_appointments = self.get_queryset().filter(
            start_datetime__gte=start_date,
            start_datetime__lte=end_date,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        )

        serializer = self.get_serializer(upcoming_appointments, many=True)
        return Response(
            {
                "period": f"Próximos {days} dias",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_appointments": upcoming_appointments.count(),
                "appointments": serializer.data,
            }
        )

    @extend_schema(
        summary="Listar agendamentos passados",
        description="Retorna uma lista paginada de agendamentos passados.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        Confirma um agendamento
        """
        appointment = self.get_object()

        if not appointment.can_be_confirmed():
            return Response(
                {"error": "Agendamento não pode ser confirmado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = appointment.confirm()
        if success:
            return Response(
                {
                    "message": "Agendamento confirmado com sucesso",
                    "status": appointment.status,
                }
            )
        else:
            return Response(
                {"error": "Falha ao confirmar agendamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Cancelar agendamento",
        description="Cancela um agendamento existente.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancela um agendamento
        """
        appointment = self.get_object()

        if not appointment.can_be_cancelled():
            return Response(
                {"error": "Agendamento não pode ser cancelado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = appointment.cancel()
        if success:
            return Response(
                {
                    "message": "Agendamento cancelado com sucesso",
                    "status": appointment.status,
                }
            )
        else:
            return Response(
                {"error": "Falha ao cancelar agendamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Marcar agendamento como concluído",
        description="Marca um agendamento como concluído.",
        tags=["appointments"],
    )
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Marca agendamento como concluído
        """
        appointment = self.get_object()

        if not appointment.can_be_completed():
            return Response(
                {"error": "Agendamento não pode ser marcado como concluído"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = appointment.complete()
        if success:
            return Response(
                {
                    "message": "Agendamento marcado como concluído",
                    "status": appointment.status,
                }
            )
        else:
            return Response(
                {"error": "Falha ao completar agendamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Estatísticas de agendamentos",
        description="Retorna estatísticas de agendamentos.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Retorna estatísticas de agendamentos
        """
        # Verificar permissões
        if (
            request.user.role not in [User.Role.BARBER, User.Role.ADMIN]
            and not request.user.is_barbershop_owner
        ):
            return Response(
                {"error": "Sem permissão para ver estatísticas"},
                status=status.HTTP_403_FORBIDDEN,
            )

        period_days = int(request.query_params.get("period_days", 30))
        barbershop_id = request.query_params.get("barbershop_id")

        barbershop = None
        if barbershop_id:
            try:
                barbershop = Barbershop.objects.get(id=barbershop_id)
            except Barbershop.DoesNotExist:
                return Response(
                    {"error": "Barbearia não encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Para barbeiros, mostrar suas próprias estatísticas
        if request.user.role == User.Role.BARBER:
            stats = get_barber_stats(request.user, barbershop, period_days)
            return Response(stats)

        # Para proprietários e admins, estatísticas da barbearia
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        if barbershop:
            appointments = get_barbershop_appointments_for_period(
                barbershop, start_date, end_date
            )
        else:
            appointments = self.get_queryset().filter(
                start_datetime__date__gte=start_date, start_datetime__date__lte=end_date
            )

        # Estatísticas por status
        stats = {
            "period_days": period_days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_appointments": appointments.count(),
            "pending_appointments": appointments.filter(
                status=Appointment.Status.PENDING
            ).count(),
            "confirmed_appointments": appointments.filter(
                status=Appointment.Status.CONFIRMED
            ).count(),
            "completed_appointments": appointments.filter(
                status=Appointment.Status.COMPLETED
            ).count(),
            "cancelled_appointments": appointments.filter(
                status=Appointment.Status.CANCELLED
            ).count(),
        }

        # Receita apenas de agendamentos concluídos
        completed_appointments = appointments.filter(
            status=Appointment.Status.COMPLETED
        )
        total_revenue = (
            completed_appointments.aggregate(total=models.Sum("final_price"))["total"]
            or 0
        )

        stats.update(
            {
                "total_revenue": total_revenue,
                "average_appointment_value": (
                    total_revenue / stats["completed_appointments"]
                    if stats["completed_appointments"] > 0
                    else 0
                ),
            }
        )

        return Response(stats)

    @extend_schema(
        summary="Relatório de receita",
        description="Retorna relatório de receita.",
        tags=["appointments"],
    )
    @action(detail=False, methods=["get"])
    def revenue_report(self, request):
        """
        Retorna relatório de receita
        """
        if (
            request.user.role not in [User.Role.ADMIN]
            and not request.user.is_barbershop_owner
        ):
            return Response(
                {"error": "Sem permissão para ver relatório de receita"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parâmetros da query
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        barbershop_id = request.query_params.get("barbershop_id")

        try:
            start_date = (
                datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date_str
                else date.today() - timedelta(days=30)
            )
            end_date = (
                datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date_str
                else date.today()
            )
        except ValueError:
            return Response(
                {"error": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if barbershop_id:
            try:
                barbershop = Barbershop.objects.get(id=barbershop_id)
                revenue_data = calculate_appointment_revenue(
                    barbershop, start_date, end_date
                )
            except Barbershop.DoesNotExist:
                return Response(
                    {"error": "Barbearia não encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Relatório geral para admin
            appointments = Appointment.objects.filter(
                start_datetime__date__gte=start_date,
                start_datetime__date__lte=end_date,
                status=Appointment.Status.COMPLETED,
            )

            total_revenue = (
                appointments.aggregate(total=models.Sum("final_price"))["total"] or 0
            )
            appointments_count = appointments.count()
            average_price = (
                total_revenue / appointments_count if appointments_count > 0 else 0
            )

            revenue_data = {
                "total_revenue": total_revenue,
                "appointments_count": appointments_count,
                "average_price": average_price,
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                },
            }

        return Response(revenue_data)
