from datetime import datetime, timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Payment
from .permissions import (
    IsBarberOrBarbershopOwnerOrAdmin,
    IsPaymentOwnerOrBarbershopOwnerOrAdmin,
)
from .serializers import (
    PaymentConfirmSerializer,
    PaymentCreateSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentRefundSerializer,
    PaymentSerializer,
    PaymentUpdateSerializer,
)
from utils.throttles.custom_throttles import PaymentThrottle, PaymentBurstThrottle


@extend_schema_view(
    list=extend_schema(
        summary="Listar pagamentos",
        description="Lista todos os pagamentos com paginação e filtros.",
        tags=["payments"],
    ),
    create=extend_schema(
        summary="Criar pagamento",
        description="Cria um novo pagamento para um agendamento.",
        tags=["payments"],
    ),
    retrieve=extend_schema(
        summary="Detalhar pagamento",
        description="Retorna os detalhes de um pagamento específico.",
        tags=["payments"],
    ),
    update=extend_schema(
        summary="Atualizar pagamento",
        description="Atualiza todos os campos de um pagamento.",
        tags=["payments"],
    ),
    partial_update=extend_schema(
        summary="Atualizar pagamento parcialmente",
        description="Atualiza alguns campos de um pagamento.",
        tags=["payments"],
    ),
    destroy=extend_schema(
        summary="Deletar pagamento",
        description="Remove um pagamento do sistema.",
        tags=["payments"],
    ),
)
class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar pagamentos com operações CRUD e ações customizadas.
    """

    queryset = Payment.objects.select_related(
        "appointment",
        "appointment__customer",
        "appointment__service",
        "appointment__barbershop",
    ).all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [
        PaymentThrottle,
        PaymentBurstThrottle,
    ]  # Throttling duplo para pagamentos
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "method",
        "status",
        "appointment__customer",
        "appointment__barbershop",
        "appointment__service",
    ]
    search_fields = [
        "appointment__customer__first_name",
        "appointment__customer__last_name",
        "appointment__service__name",
        "appointment__barbershop__name",
        "notes",
    ]
    ordering_fields = ["amount", "payment_date", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return PaymentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PaymentUpdateSerializer
        elif self.action == "retrieve":
            return PaymentDetailSerializer
        elif self.action == "list":
            return PaymentListSerializer
        elif self.action == "confirm":
            return PaymentConfirmSerializer
        elif self.action == "refund":
            return PaymentRefundSerializer
        return PaymentSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [
                IsAuthenticated,
                IsPaymentOwnerOrBarbershopOwnerOrAdmin,
            ]
        elif self.action == "create":
            permission_classes = [IsAuthenticated, IsBarberOrBarbershopOwnerOrAdmin]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [
                IsAuthenticated,
                IsPaymentOwnerOrBarbershopOwnerOrAdmin,
            ]
        elif self.action in ["confirm", "refund"]:
            permission_classes = [
                IsAuthenticated,
                IsPaymentOwnerOrBarbershopOwnerOrAdmin,
            ]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filtra os pagamentos baseado no usuário.
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Admins veem todos os pagamentos
        if hasattr(user, "role") and user.role == "ADMIN":
            return queryset

        # Donos de barbearia veem pagamentos da sua barbearia
        if hasattr(user, "is_barbershop_owner") and user.is_barbershop_owner:
            return queryset.filter(appointment__barbershop__owner=user)

        # Barbeiros veem pagamentos de seus agendamentos
        if hasattr(user, "role") and user.role == "BARBER":
            return queryset.filter(appointment__barber=user)

        # Clientes veem apenas seus próprios pagamentos
        if hasattr(user, "role") and user.role == "CLIENT":
            return queryset.filter(appointment__customer__customer=user)

        # Caso padrão: sem acesso
        return queryset.none()

    @extend_schema(
        summary="Meus pagamentos",
        description="Lista os pagamentos do usuário autenticado.",
        tags=["payments"],
    )
    @action(detail=False, methods=["get"])
    def my_payments(self, request):
        """
        Retorna os pagamentos do usuário autenticado.
        """
        user = request.user

        if user.is_client():
            payments = self.get_queryset().filter(appointment__customer__customer=user)
        elif user.is_barber():
            payments = self.get_queryset().filter(appointment__barber=user)
        elif user.is_barbershop_owner:
            payments = self.get_queryset().filter(appointment__barbershop__owner=user)
        else:
            payments = self.get_queryset()

        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = PaymentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentListSerializer(payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Confirmar pagamento",
        description="Marca um pagamento como pago.",
        tags=["payments"],
    )
    @action(detail=True, methods=["patch"])
    def confirm(self, request, pk=None):
        """
        Confirma um pagamento marcando-o como pago.
        """
        payment = self.get_object()

        if payment.is_paid():
            return Response(
                {"detail": "Este pagamento já foi confirmado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.is_refunded():
            return Response(
                {"detail": "Não é possível confirmar um pagamento reembolsado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PaymentConfirmSerializer(payment, data=request.data, partial=True)
        if serializer.is_valid():
            payment = serializer.save()
            response_serializer = PaymentDetailSerializer(payment)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Reembolsar pagamento",
        description="Marca um pagamento como reembolsado.",
        tags=["payments"],
    )
    @action(detail=True, methods=["patch"])
    def refund(self, request, pk=None):
        """
        Reembolsa um pagamento marcando-o como reembolsado.
        """
        payment = self.get_object()

        serializer = PaymentRefundSerializer(payment, data=request.data, partial=True)
        if serializer.is_valid():
            payment = serializer.save()
            response_serializer = PaymentDetailSerializer(payment)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Estatísticas de pagamentos",
        description="Retorna estatísticas gerais dos pagamentos.",
        tags=["payments"],
    )
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Retorna estatísticas dos pagamentos.
        """
        queryset = self.get_queryset()

        # Estatísticas gerais
        total_payments = queryset.count()
        total_revenue = queryset.filter(status=Payment.Status.PAID).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        # Status distribution
        status_stats = (
            queryset.values("status")
            .annotate(count=Count("id"), total_amount=Sum("amount"))
            .order_by("status")
        )

        # Method distribution
        method_stats = (
            queryset.filter(status=Payment.Status.PAID)
            .values("method")
            .annotate(count=Count("id"), total_amount=Sum("amount"))
            .order_by("method")
        )

        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_payments = queryset.filter(created_at__gte=thirty_days_ago)
        recent_revenue = recent_payments.filter(status=Payment.Status.PAID).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        return Response(
            {
                "total_payments": total_payments,
                "total_revenue": str(total_revenue),
                "recent_revenue": str(recent_revenue),
                "status_distribution": status_stats,
                "method_distribution": method_stats,
            }
        )

    @extend_schema(
        summary="Pagamentos pendentes",
        description="Lista todos os pagamentos com status pendente.",
        tags=["payments"],
    )
    @action(detail=False, methods=["get"])
    def pending(self, request):
        """
        Lista pagamentos pendentes.
        """
        pending_payments = self.get_queryset().filter(status=Payment.Status.PENDING)

        page = self.paginate_queryset(pending_payments)
        if page is not None:
            serializer = PaymentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentListSerializer(pending_payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Pagamentos do dia",
        description="Lista os pagamentos realizados hoje.",
        tags=["payments"],
    )
    @action(detail=False, methods=["get"])
    def today(self, request):
        """
        Lista pagamentos de hoje.
        """
        today = timezone.now().date()
        today_payments = self.get_queryset().filter(
            payment_date__date=today, status=Payment.Status.PAID
        )

        page = self.paginate_queryset(today_payments)
        if page is not None:
            serializer = PaymentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentListSerializer(today_payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Receita por período",
        description="Retorna a receita total em um período específico.",
        tags=["payments"],
    )
    @action(detail=False, methods=["get"])
    def revenue_by_period(self, request):
        """
        Calcula receita por período especificado.
        """
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response(
                {
                    "detail": "Parâmetros 'start_date' e 'end_date' são obrigatórios (formato: YYYY-MM-DD)."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_revenue = Payment.get_total_revenue(start_date, end_date)
        revenue_by_method = Payment.get_revenue_by_method(start_date, end_date)

        return Response(
            {
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "total_revenue": str(total_revenue),
                "revenue_by_method": revenue_by_method,
            }
        )
