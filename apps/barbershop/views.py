from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Barbershop, BarbershopCustomer, Service
from .permissions import (
    IsBarbershopCustomerOwnerOrAdmin,
    IsBarbershopOwnerOrAdmin,
    IsCustomerOrBarbershopOwnerOrAdmin,
    IsOwnerOrAdminBarbershop,
    IsOwnerOrAdminOrReadOnly,
    IsServiceOwnerOrAdmin,
    IsServiceOwnerOrAdminOrReadOnly,
)
from .serializers import (
    BarbershopCreateSerializer,
    BarbershopCustomerDetailSerializer,
    BarbershopCustomerListSerializer,
    BarbershopCustomerSerializer,
    BarbershopDetailSerializer,
    BarbershopListSerializer,
    BarbershopSerializer,
    BarbershopUpdateSerializer,
    ServiceCreateSerializer,
    ServiceDetailSerializer,
    ServiceListSerializer,
    ServiceSerializer,
    ServiceUpdateSerializer,
)
from utils.throttles.custom_throttles import SearchThrottle
from utils.cache import CompleteCacheMixin, CacheKeys


@extend_schema_view(
    list=extend_schema(
        summary="Listar barbearias",
        description="Lista todas as barbearias com paginação e filtros.",
        tags=["barbershops"],
    ),
    create=extend_schema(
        summary="Criar barbearia",
        description="Cria uma nova barbearia no sistema.",
        tags=["barbershops"],
    ),
    retrieve=extend_schema(
        summary="Detalhar barbearia",
        description="Retorna os detalhes de uma barbearia específica.",
        tags=["barbershops"],
    ),
    update=extend_schema(
        summary="Atualizar barbearia",
        description="Atualiza todos os campos de uma barbearia.",
        tags=["barbershops"],
    ),
    partial_update=extend_schema(
        summary="Atualizar barbearia parcialmente",
        description="Atualiza alguns campos de uma barbearia.",
        tags=["barbershops"],
    ),
    destroy=extend_schema(
        summary="Deletar barbearia",
        description="Remove uma barbearia do sistema.",
        tags=["barbershops"],
    ),
)
class BarbershopViewSet(CompleteCacheMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciar barbearias com operações CRUD e ações customizadas.
    Inclui cache automático para listagens e detalhes com invalidação inteligente.
    """

    queryset = Barbershop.objects.all()
    serializer_class = BarbershopSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [SearchThrottle]  # Throttling para busca de barbearias
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["owner"]
    search_fields = ["name", "description", "address", "email"]
    ordering_fields = ["created_at", "updated_at", "name"]
    ordering = ["-created_at"]

    # Configuração de cache
    cache_model_name = "barbershop"
    cache_ttl_type = "LISTING"  # 15 minutos para listagens
    cache_key_prefix = CacheKeys.BARBERSHOP_PREFIX
    additional_cache_patterns = [
        CacheKeys.SERVICE_PREFIX
    ]  # Serviços podem ser afetados

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return BarbershopCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return BarbershopUpdateSerializer
        elif self.action == "retrieve":
            return BarbershopDetailSerializer
        elif self.action == "list":
            return BarbershopListSerializer
        return BarbershopSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action == "create":
            permission_classes = [IsAuthenticated, IsBarbershopOwnerOrAdmin]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsOwnerOrAdminBarbershop]
        elif self.action in ["my_barbershops"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["stats", "revenue_report"]:
            permission_classes = [IsAuthenticated, IsOwnerOrAdminBarbershop]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Minhas barbearias",
        description="Retorna as barbearias do usuário autenticado.",
        tags=["barbershops"],
    )
    @action(detail=False, methods=["get"], url_path="my-barbershops")
    def my_barbershops(self, request):
        """
        Retorna as barbearias do usuário autenticado.
        """
        barbershops = Barbershop.objects.filter(owner=request.user)

        # Aplicar filtros de busca se fornecidos
        search = request.query_params.get("search", None)
        if search:
            barbershops = barbershops.filter(
                models.Q(name__icontains=search)
                | models.Q(description__icontains=search)
                | models.Q(address__icontains=search)
            )

        page = self.paginate_queryset(barbershops)
        if page is not None:
            serializer = BarbershopListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = BarbershopListSerializer(
            barbershops, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Serviços da barbearia",
        description="Retorna todos os serviços de uma barbearia específica.",
        tags=["barbershops"],
    )
    @action(detail=True, methods=["get"])
    def services(self, request, pk=None):
        """
        Retorna os serviços de uma barbearia específica.
        """
        barbershop = self.get_object()
        services = barbershop.services.all()

        # Filtrar apenas serviços disponíveis se solicitado
        available_only = (
            request.query_params.get("available_only", "false").lower() == "true"
        )
        if available_only:
            services = services.filter(available=True)

        # Aplicar filtros de busca se fornecidos
        search = request.query_params.get("search", None)
        if search:
            services = services.filter(
                models.Q(name__icontains=search)
                | models.Q(description__icontains=search)
            )

        # Ordenação
        ordering = request.query_params.get("ordering", "name")
        if ordering in [
            "name",
            "-name",
            "price",
            "-price",
            "created_at",
            "-created_at",
        ]:
            services = services.order_by(ordering)

        page = self.paginate_queryset(services)
        if page is not None:
            serializer = ServiceListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = ServiceListSerializer(
            services, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Clientes da barbearia",
        description="Retorna todos os clientes de uma barbearia específica.",
        tags=["barbershops"],
    )
    @action(detail=True, methods=["get"])
    def customers(self, request, pk=None):
        """
        Retorna os clientes de uma barbearia específica.
        """
        barbershop = self.get_object()
        customers = barbershop.barbershop_customers.all()

        # Filtrar apenas clientes ativos se solicitado
        active_only = request.query_params.get("active_only", "false").lower() == "true"
        if active_only:
            cutoff_date = timezone.now() - timedelta(days=90)
            customers = customers.filter(last_visit__gte=cutoff_date)

        # Filtrar por tier se fornecido
        tier = request.query_params.get("tier", None)
        if tier:
            # Esta é uma implementação simplificada - idealmente seria feita no banco
            all_customers = list(customers)
            filtered_customers = [
                c
                for c in all_customers
                if c.get_customer_tier().lower() == tier.lower()
            ]

            serializer = BarbershopCustomerListSerializer(
                filtered_customers, many=True, context={"request": request}
            )
            return Response(serializer.data)

        # Aplicar filtros de busca se fornecidos
        search = request.query_params.get("search", None)
        if search:
            customers = customers.filter(
                models.Q(customer__username__icontains=search)
                | models.Q(customer__first_name__icontains=search)
                | models.Q(customer__last_name__icontains=search)
                | models.Q(customer__email__icontains=search)
            )

        # Ordenação
        ordering = request.query_params.get("ordering", "-last_visit")
        if ordering in ["last_visit", "-last_visit"]:
            customers = customers.order_by(ordering)

        page = self.paginate_queryset(customers)
        if page is not None:
            serializer = BarbershopCustomerListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = BarbershopCustomerListSerializer(
            customers, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Estatísticas da barbearia",
        description="Retorna estatísticas detalhadas de uma barbearia específica.",
        tags=["barbershops"],
    )
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """
        Retorna estatísticas da barbearia.
        """
        barbershop = self.get_object()

        # Estatísticas básicas
        total_services = barbershop.get_total_services()
        available_services = barbershop.get_available_services_count()
        total_customers = barbershop.get_total_customers()
        total_appointments = barbershop.get_total_appointments()
        total_revenue = barbershop.get_total_revenue()
        average_service_price = barbershop.get_average_service_price()

        # Serviços mais populares
        popular_services = barbershop.get_most_popular_services(limit=5)
        popular_services_data = ServiceListSerializer(
            popular_services, many=True, context={"request": request}
        ).data

        # Clientes recentes
        recent_customers = barbershop.get_recent_customers(limit=10)
        recent_customers_data = BarbershopCustomerListSerializer(
            recent_customers, many=True, context={"request": request}
        ).data

        return Response(
            {
                "basic_stats": {
                    "total_services": total_services,
                    "available_services": available_services,
                    "total_customers": total_customers,
                    "total_appointments": total_appointments,
                    "total_revenue": str(total_revenue),
                    "average_service_price": (
                        str(average_service_price) if average_service_price else None
                    ),
                },
                "popular_services": popular_services_data,
                "recent_customers": recent_customers_data,
            }
        )

    @extend_schema(
        summary="Relatório de receita",
        description="Retorna relatório detalhado de receita da barbearia por período.",
        tags=["barbershops"],
    )
    @action(detail=True, methods=["get"], url_path="revenue-report")
    def revenue_report(self, request, pk=None):
        """
        Retorna relatório de receita da barbearia.
        """
        barbershop = self.get_object()

        # Parâmetros de data
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de data inválido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de data inválido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Se não fornecidas, usar últimos 30 dias
        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).date()
        if not end_date:
            end_date = timezone.now().date()

        # Receita total no período
        total_revenue = barbershop.get_total_revenue(
            start_date=start_date, end_date=end_date
        )

        # Receita por serviço
        services_revenue = []
        for service in barbershop.services.all():
            service_revenue = service.get_total_revenue(
                start_date=start_date, end_date=end_date
            )
            if service_revenue > 0:
                services_revenue.append(
                    {
                        "service_id": str(service.id),
                        "service_name": service.name,
                        "revenue": str(service_revenue),
                    }
                )

        return Response(
            {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                },
                "total_revenue": str(total_revenue),
                "services_revenue": services_revenue,
            }
        )


@extend_schema_view(
    list=extend_schema(
        summary="Listar serviços",
        description="Lista todos os serviços com paginação e filtros.",
        tags=["barbershops"],
    ),
    create=extend_schema(
        summary="Criar serviço",
        description="Cria um novo serviço para uma barbearia.",
        tags=["barbershops"],
    ),
    retrieve=extend_schema(
        summary="Detalhar serviço",
        description="Retorna os detalhes de um serviço específico.",
        tags=["barbershops"],
    ),
    update=extend_schema(
        summary="Atualizar serviço",
        description="Atualiza todos os campos de um serviço.",
        tags=["barbershops"],
    ),
    partial_update=extend_schema(
        summary="Atualizar serviço parcialmente",
        description="Atualiza alguns campos de um serviço.",
        tags=["barbershops"],
    ),
    destroy=extend_schema(
        summary="Deletar serviço",
        description="Remove um serviço do sistema.",
        tags=["barbershops"],
    ),
)
class ServiceViewSet(CompleteCacheMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciar serviços com operações CRUD e ações customizadas.
    Inclui cache automático para listagens e detalhes com invalidação inteligente.
    """

    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [SearchThrottle]  # Throttling para busca de serviços
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["barbershop", "available"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "updated_at", "name", "price"]
    ordering = ["-created_at"]

    # Configuração de cache
    cache_model_name = "service"
    cache_ttl_type = "LISTING"  # 15 minutos para listagens
    cache_key_prefix = CacheKeys.SERVICE_PREFIX
    additional_cache_patterns = [
        CacheKeys.BARBERSHOP_PREFIX
    ]  # Barbearias podem ser afetadas

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return ServiceCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ServiceUpdateSerializer
        elif self.action == "retrieve":
            return ServiceDetailSerializer
        elif self.action == "list":
            return ServiceListSerializer
        return ServiceSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action == "create":
            permission_classes = [IsAuthenticated, IsBarbershopOwnerOrAdmin]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsServiceOwnerOrAdmin]
        elif self.action in ["toggle_availability"]:
            permission_classes = [IsAuthenticated, IsServiceOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Alternar disponibilidade",
        description="Alterna a disponibilidade de um serviço.",
        tags=["barbershops"],
    )
    @action(detail=True, methods=["post"], url_path="toggle-availability")
    def toggle_availability(self, request, pk=None):
        """
        Alterna a disponibilidade do serviço.
        """
        service = self.get_object()
        service.toggle_availability()

        status_text = "disponível" if service.available else "indisponível"
        return Response(
            {
                "message": f"Serviço '{service.name}' agora está {status_text}.",
                "available": service.available,
            }
        )

    @extend_schema(
        summary="Serviços populares",
        description="Lista os serviços mais populares baseado em agendamentos.",
        tags=["barbershops"],
    )
    @action(detail=False, methods=["get"], url_path="popular")
    def popular(self, request):
        """
        Lista serviços populares (mais de 10 agendamentos).
        """
        popular_services = (
            Service.objects.annotate(appointment_count=models.Count("appointments"))
            .filter(appointment_count__gt=10)
            .order_by("-appointment_count")
        )

        # Filtrar por barbearia se fornecido
        barbershop_id = request.query_params.get("barbershop", None)
        if barbershop_id:
            popular_services = popular_services.filter(barbershop_id=barbershop_id)

        page = self.paginate_queryset(popular_services)
        if page is not None:
            serializer = ServiceListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = ServiceListSerializer(
            popular_services, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Listar clientes de barbearia",
        description="Lista todos os relacionamentos cliente-barbearia com paginação e filtros.",
        tags=["barbershops"],
    ),
    create=extend_schema(
        summary="Criar relacionamento cliente-barbearia",
        description="Cria um novo relacionamento entre cliente e barbearia.",
        tags=["barbershops"],
    ),
    retrieve=extend_schema(
        summary="Detalhar cliente de barbearia",
        description="Retorna os detalhes de um relacionamento cliente-barbearia específico.",
        tags=["barbershops"],
    ),
    update=extend_schema(
        summary="Atualizar cliente de barbearia",
        description="Atualiza um relacionamento cliente-barbearia.",
        tags=["barbershops"],
    ),
    partial_update=extend_schema(
        summary="Atualizar cliente de barbearia parcialmente",
        description="Atualiza alguns campos de um relacionamento cliente-barbearia.",
        tags=["barbershops"],
    ),
    destroy=extend_schema(
        summary="Deletar cliente de barbearia",
        description="Remove um relacionamento cliente-barbearia do sistema.",
        tags=["barbershops"],
    ),
)
class BarbershopCustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar relacionamentos cliente-barbearia com operações CRUD e ações customizadas.
    """

    queryset = BarbershopCustomer.objects.all()
    serializer_class = BarbershopCustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["barbershop", "customer"]
    search_fields = [
        "customer__username",
        "customer__first_name",
        "customer__last_name",
        "customer__email",
    ]
    ordering_fields = ["last_visit"]
    ordering = ["-last_visit"]

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "retrieve":
            return BarbershopCustomerDetailSerializer
        elif self.action == "list":
            return BarbershopCustomerListSerializer
        return BarbershopCustomerSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsBarbershopCustomerOwnerOrAdmin]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated, IsCustomerOrBarbershopOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Clientes VIP",
        description="Lista clientes VIP baseado no valor gasto.",
        tags=["barbershops"],
    )
    @action(detail=False, methods=["get"], url_path="vip")
    def vip_customers(self, request):
        """
        Lista clientes VIP (que gastaram mais de R$ 500).
        """
        min_spent = float(request.query_params.get("min_spent", 500))
        barbershop_id = request.query_params.get("barbershop", None)

        if barbershop_id:
            try:
                barbershop = Barbershop.objects.get(id=barbershop_id)
                vip_customers = BarbershopCustomer.get_vip_customers(
                    barbershop, min_spent
                )
            except Barbershop.DoesNotExist:
                return Response(
                    {"error": "Barbearia não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Retorna erro se não especificar barbearia
            return Response(
                {"error": "Parâmetro 'barbershop' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filtrar os que realmente são VIP
        vip_list = [
            customer
            for customer in vip_customers
            if customer.is_vip_customer(min_spent)
        ]

        serializer = BarbershopCustomerListSerializer(
            vip_list, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Clientes inativos",
        description="Lista clientes inativos que não visitaram há muito tempo.",
        tags=["barbershops"],
    )
    @action(detail=False, methods=["get"], url_path="inactive")
    def inactive_customers(self, request):
        """
        Lista clientes inativos (que não visitaram nos últimos 90 dias).
        """
        days_threshold = int(request.query_params.get("days_threshold", 90))
        barbershop_id = request.query_params.get("barbershop", None)

        if barbershop_id:
            try:
                barbershop = Barbershop.objects.get(id=barbershop_id)
                inactive_customers = BarbershopCustomer.get_inactive_customers(
                    barbershop, days_threshold
                )
            except Barbershop.DoesNotExist:
                return Response(
                    {"error": "Barbearia não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Retorna erro se não especificar barbearia
            return Response(
                {"error": "Parâmetro 'barbershop' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        page = self.paginate_queryset(inactive_customers)
        if page is not None:
            serializer = BarbershopCustomerListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = BarbershopCustomerListSerializer(
            inactive_customers, many=True, context={"request": request}
        )
        return Response(serializer.data)
