from decimal import Decimal

from django.db.models import Avg, Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.review.models import Review
from apps.review.permissions import (
    CanCreateReview,
    CanDeleteReview,
    CanUpdateOwnReview,
    CanViewReviewStatistics,
    IsReviewOwnerOrBarbershopOwnerOrAdmin,
)
from apps.review.serializers import (
    ReviewCreateSerializer,
    ReviewDetailSerializer,
    ReviewListSerializer,
    ReviewSerializer,
    ReviewStatisticsSerializer,
    ReviewUpdateSerializer,
)
from apps.review.utils import (
    calculate_review_statistics,
    get_review_trends,
    get_top_rated_barbers,
    get_top_rated_barbershops,
    get_top_rated_services,
)
from utils.throttles.custom_throttles import ReviewThrottle
from utils.cache import CompleteCacheMixin, CacheKeys, cache_manager


@extend_schema_view(
    list=extend_schema(
        summary="Listar avaliações",
        description="Retorna uma lista paginada de avaliações com filtros e busca.",
        tags=["reviews"],
    ),
    create=extend_schema(
        summary="Criar avaliação",
        description="Cria uma nova avaliação para um serviço/barbeiro após agendamento.",
        tags=["reviews"],
    ),
    retrieve=extend_schema(
        summary="Obter avaliação",
        description="Retorna os detalhes completos de uma avaliação específica.",
        tags=["reviews"],
    ),
    update=extend_schema(
        summary="Atualizar avaliação",
        description="Atualiza completamente uma avaliação existente.",
        tags=["reviews"],
    ),
    partial_update=extend_schema(
        summary="Atualizar avaliação parcialmente",
        description="Atualiza parcialmente uma avaliação existente.",
        tags=["reviews"],
    ),
    destroy=extend_schema(
        summary="Deletar avaliação",
        description="Remove uma avaliação do sistema.",
        tags=["reviews"],
    ),
)
class ReviewViewSet(CompleteCacheMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciar avaliações com operações CRUD e ações customizadas.
    Inclui cache automático para listagens e detalhes com invalidação inteligente.
    """

    queryset = Review.objects.select_related(
        "barbershop_customer",
        "barbershop_customer__customer",
        "barber",
        "service",
        "barbershop",
    ).all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReviewThrottle]  # Throttling para reviews
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "rating",
        "barber",
        "service",
        "barbershop",
        "barbershop_customer",
    ]
    search_fields = [
        "comment",
        "barber__first_name",
        "barber__last_name",
        "service__name",
        "barbershop__name",
    ]
    ordering_fields = ["rating", "created_at", "updated_at"]
    ordering = ["-created_at"]

    # Configuração de cache
    cache_model_name = "review"
    cache_ttl_type = "LISTING"  # 15 minutos para reviews
    cache_key_prefix = CacheKeys.REVIEW_PREFIX
    additional_cache_patterns = [CacheKeys.BARBERSHOP_PREFIX, CacheKeys.SERVICE_PREFIX]
    cache_vary_on_user = True  # Cache varia por usuário

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == "create":
            return ReviewCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ReviewUpdateSerializer
        elif self.action == "retrieve":
            return ReviewDetailSerializer
        elif self.action == "list":
            return ReviewListSerializer
        return ReviewSerializer

    def get_permissions(self):
        """
        Define as permissões baseadas na ação.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [
                IsAuthenticated,
                IsReviewOwnerOrBarbershopOwnerOrAdmin,
            ]
        elif self.action == "create":
            permission_classes = [IsAuthenticated, CanCreateReview]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, CanUpdateOwnReview]
        elif self.action == "destroy":
            permission_classes = [IsAuthenticated, CanDeleteReview]
        elif self.action in ["statistics", "trends", "top_rated"]:
            permission_classes = [IsAuthenticated, CanViewReviewStatistics]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filtra as avaliações baseado no usuário.
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Admins veem todas as avaliações
        if hasattr(user, "role") and user.role == "ADMIN":
            return queryset

        # Donos de barbearia veem avaliações de suas barbearias
        if hasattr(user, "is_barbershop_owner") and user.is_barbershop_owner:
            return queryset.filter(barbershop__owner=user)

        # Barbeiros veem suas próprias avaliações
        if hasattr(user, "role") and user.role == "BARBER":
            return queryset.filter(barber=user)

        # Clientes veem apenas suas próprias avaliações
        if hasattr(user, "role") and user.role == "CLIENT":
            return queryset.filter(barbershop_customer__customer=user)

        # Caso padrão: sem acesso
        return queryset.none()

    @extend_schema(
        summary="Minhas avaliações",
        description="Retorna as avaliações do usuário logado (como cliente ou barbeiro).",
        tags=["reviews"],
    )
    @action(detail=False, methods=["get"])
    def my_reviews(self, request):
        """
        Retorna as avaliações relacionadas ao usuário logado.
        Para clientes: avaliações que eles fizeram
        Para barbeiros: avaliações que receberam
        """
        user = request.user

        if hasattr(user, "role") and user.role == "CLIENT":
            # Cliente vê avaliações que fez
            reviews = self.get_queryset().filter(barbershop_customer__customer=user)
        elif hasattr(user, "role") and user.role == "BARBER":
            # Barbeiro vê avaliações que recebeu
            reviews = self.get_queryset().filter(barber=user)
        else:
            reviews = self.get_queryset()

        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Estatísticas de avaliações",
        description="Retorna estatísticas gerais das avaliações (filtradas por contexto do usuário).",
        tags=["reviews"],
    )
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Retorna estatísticas das avaliações.
        """
        queryset = self.get_queryset()
        barbershop = request.query_params.get("barbershop")
        barber = request.query_params.get("barber")
        service = request.query_params.get("service")

        stats = calculate_review_statistics(
            queryset=queryset, barbershop=barbershop, barber=barber, service=service
        )

        serializer = ReviewStatisticsSerializer(stats)
        return Response(serializer.data)

    @extend_schema(
        summary="Tendências de avaliações",
        description="Retorna tendências de avaliações comparando períodos.",
        tags=["reviews"],
    )
    @action(detail=False, methods=["get"])
    def trends(self, request):
        """
        Retorna tendências das avaliações nos últimos X dias.
        """
        days = int(request.query_params.get("days", 30))
        barbershop_id = request.query_params.get("barbershop")

        barbershop = None
        if barbershop_id:
            try:
                from apps.barbershop.models import Barbershop

                barbershop = Barbershop.objects.get(id=barbershop_id)
            except Barbershop.DoesNotExist:
                pass

        trends = get_review_trends(days=days, barbershop=barbershop)
        return Response(trends)

    @extend_schema(
        summary="Top avaliações",
        description="Retorna rankings dos melhores barbeiros, serviços e barbearias.",
        tags=["reviews"],
    )
    @action(detail=False, methods=["get"])
    def top_rated(self, request):
        """
        Retorna rankings de melhor avaliação.
        """
        category = request.query_params.get(
            "category", "all"
        )  # all, barbers, services, barbershops
        limit = int(request.query_params.get("limit", 10))
        barbershop_id = request.query_params.get("barbershop")

        barbershop = None
        if barbershop_id:
            try:
                from apps.barbershop.models import Barbershop

                barbershop = Barbershop.objects.get(id=barbershop_id)
            except Barbershop.DoesNotExist:
                pass

        result = {}

        if category in ["all", "barbers"]:
            top_barbers = get_top_rated_barbers(limit=limit, barbershop=barbershop)
            result["top_barbers"] = [
                {
                    "id": barber.id,
                    "name": barber.get_display_name(),
                    "avg_rating": float(barber.avg_rating),
                    "total_reviews": barber.total_reviews,
                }
                for barber in top_barbers
            ]

        if category in ["all", "services"]:
            top_services = get_top_rated_services(limit=limit, barbershop=barbershop)
            result["top_services"] = [
                {
                    "id": service.id,
                    "name": service.name,
                    "avg_rating": float(service.avg_rating),
                    "total_reviews": service.total_reviews,
                    "price": str(service.price),
                    "barbershop_name": service.barbershop.name,
                }
                for service in top_services
            ]

        if category in ["all", "barbershops"] and not barbershop:
            top_barbershops = get_top_rated_barbershops(limit=limit)
            result["top_barbershops"] = [
                {
                    "id": shop.id,
                    "name": shop.name,
                    "avg_rating": float(shop.avg_rating),
                    "total_reviews": shop.total_reviews,
                    "address": shop.address,
                }
                for shop in top_barbershops
            ]

        return Response(result)

    @extend_schema(
        summary="Avaliações por período",
        description="Retorna avaliações filtradas por período específico.",
        tags=["reviews"],
    )
    @action(detail=False, methods=["get"])
    def by_period(self, request):
        """
        Retorna avaliações por período (dia, semana, mês).
        """
        period = request.query_params.get("period", "week")  # day, week, month

        if period == "day":
            date_filter = timezone.now().date()
            reviews = self.get_queryset().filter(created_at__date=date_filter)
        elif period == "week":
            from datetime import timedelta

            start_week = timezone.now() - timedelta(days=7)
            reviews = self.get_queryset().filter(created_at__gte=start_week)
        elif period == "month":
            from datetime import timedelta

            start_month = timezone.now() - timedelta(days=30)
            reviews = self.get_queryset().filter(created_at__gte=start_month)
        else:
            reviews = self.get_queryset()

        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Avaliações por rating",
        description="Retorna avaliações filtradas por rating específico.",
        tags=["reviews"],
    )
    @action(detail=False, methods=["get"])
    def by_rating(self, request):
        """
        Retorna avaliações filtradas por rating.
        """
        rating_param = request.query_params.get("rating")
        rating_type = request.query_params.get("type")  # positive, negative, neutral

        queryset = self.get_queryset()

        if rating_param:
            try:
                rating = int(rating_param)
                if 1 <= rating <= 5:
                    queryset = queryset.filter(rating=rating)
            except ValueError:
                pass
        elif rating_type:
            if rating_type == "positive":
                queryset = queryset.filter(rating__gte=4)
            elif rating_type == "negative":
                queryset = queryset.filter(rating__lte=2)
            elif rating_type == "neutral":
                queryset = queryset.filter(rating=3)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewListSerializer(queryset, many=True)
        return Response(serializer.data)
