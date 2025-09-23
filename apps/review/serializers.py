from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.appointment.models import Appointment
from apps.barbershop.models import Barbershop, BarbershopCustomer, Service
from apps.review.models import Review
from apps.user.models import User


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de avaliações.
    """

    barbershop_customer_id = serializers.UUIDField(write_only=True)
    barber_id = serializers.UUIDField(write_only=True)
    service_id = serializers.UUIDField(write_only=True)
    barbershop_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "barbershop_customer_id",
            "barber_id",
            "service_id",
            "barbershop_id",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_rating(self, value):
        """Valida se o rating está dentro do range válido"""
        if value not in [choice.value for choice in Review.Rating]:
            raise ValidationError("Rating deve estar entre 1 e 5 estrelas.")
        return value

    def validate_barbershop_customer_id(self, value):
        """Valida se o cliente da barbearia existe"""
        try:
            return BarbershopCustomer.objects.get(id=value)
        except BarbershopCustomer.DoesNotExist:
            raise ValidationError("Cliente da barbearia não encontrado.")

    def validate_barber_id(self, value):
        """Valida se o barbeiro existe e tem role de barbeiro"""
        try:
            barber = User.objects.get(id=value)
            if not barber.is_barber():
                raise ValidationError("Usuário deve ter role de barbeiro.")
            return barber
        except User.DoesNotExist:
            raise ValidationError("Barbeiro não encontrado.")

    def validate_service_id(self, value):
        """Valida se o serviço existe e está disponível"""
        try:
            service = Service.objects.get(id=value)
            if not service.available:
                raise ValidationError("Serviço não está disponível para avaliação.")
            return service
        except Service.DoesNotExist:
            raise ValidationError("Serviço não encontrado.")

    def validate_barbershop_id(self, value):
        """Valida se a barbearia existe"""
        try:
            return Barbershop.objects.get(id=value)
        except Barbershop.DoesNotExist:
            raise ValidationError("Barbearia não encontrada.")

    def validate(self, attrs):
        """Validações cruzadas"""
        barbershop_customer = attrs.get("barbershop_customer_id")
        barber = attrs.get("barber_id")
        service = attrs.get("service_id")
        barbershop = attrs.get("barbershop_id")

        # Verificar se o serviço pertence à barbearia
        if service.barbershop != barbershop:
            raise ValidationError("O serviço deve pertencer à barbearia informada.")

        # Verificar se o cliente pertence à barbearia
        if barbershop_customer.barbershop != barbershop:
            raise ValidationError("O cliente deve pertencer à barbearia informada.")

        # Verificar se já existe uma avaliação com essa combinação
        if Review.objects.filter(
            barbershop_customer=barbershop_customer,
            barber=barber,
            service=service,
            barbershop=barbershop,
        ).exists():
            raise ValidationError(
                "Já existe uma avaliação para esta combinação de cliente, barbeiro, serviço e barbearia."
            )

        # Verificar se existe um agendamento confirmado ou finalizado
        appointment_exists = Appointment.objects.filter(
            customer=barbershop_customer,
            barber=barber,
            service=service,
            barbershop=barbershop,
            status__in=[Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED],
        ).exists()

        if not appointment_exists:
            raise ValidationError(
                "Só é possível avaliar após ter um agendamento confirmado ou finalizado."
            )

        return attrs

    def create(self, validated_data):
        """Cria uma nova avaliação"""
        # Substituir os IDs pelos objetos
        validated_data["barbershop_customer"] = validated_data.pop(
            "barbershop_customer_id"
        )
        validated_data["barber"] = validated_data.pop("barber_id")
        validated_data["service"] = validated_data.pop("service_id")
        validated_data["barbershop"] = validated_data.pop("barbershop_id")

        return Review.objects.create(**validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de avaliações.
    Permite apenas atualizar rating e comentário.
    """

    class Meta:
        model = Review
        fields = ["rating", "comment", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_rating(self, value):
        """Valida se o rating está dentro do range válido"""
        if value not in [choice.value for choice in Review.Rating]:
            raise ValidationError("Rating deve estar entre 1 e 5 estrelas.")
        return value


class ReviewDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detalhado para visualização de avaliações.
    """

    barbershop_customer_details = serializers.SerializerMethodField()
    barber_details = serializers.SerializerMethodField()
    service_details = serializers.SerializerMethodField()
    barbershop_details = serializers.SerializerMethodField()

    # Campos calculados
    rating_stars = serializers.CharField(source="get_rating_stars", read_only=True)
    rating_display_with_stars = serializers.CharField(
        source="get_rating_display_with_stars", read_only=True
    )
    customer_name = serializers.CharField(source="get_customer_name", read_only=True)
    barber_name = serializers.CharField(source="get_barber_name", read_only=True)
    service_name = serializers.CharField(source="get_service_name", read_only=True)
    barbershop_name = serializers.CharField(
        source="get_barbershop_name", read_only=True
    )
    short_comment = serializers.CharField(source="get_short_comment", read_only=True)
    review_age_days = serializers.IntegerField(
        source="get_review_age_days", read_only=True
    )
    is_positive_review = serializers.BooleanField(read_only=True)
    is_negative_review = serializers.BooleanField(read_only=True)
    is_neutral_review = serializers.BooleanField(read_only=True)
    is_recent_review = serializers.BooleanField(read_only=True)
    has_comment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "barbershop_customer",
            "barbershop_customer_details",
            "barber",
            "barber_details",
            "service",
            "service_details",
            "barbershop",
            "barbershop_details",
            "rating",
            "rating_stars",
            "rating_display_with_stars",
            "comment",
            "short_comment",
            "customer_name",
            "barber_name",
            "service_name",
            "barbershop_name",
            "review_age_days",
            "is_positive_review",
            "is_negative_review",
            "is_neutral_review",
            "is_recent_review",
            "has_comment",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.DictField)
    def get_barbershop_customer_details(self, obj) -> dict:
        """Retorna detalhes do cliente da barbearia"""
        return {
            "id": obj.barbershop_customer.id,
            "customer_name": (
                obj.barbershop_customer.customer.get_display_name()
                if obj.barbershop_customer.customer
                else "Cliente desconhecido"
            ),
            "last_visit": obj.barbershop_customer.last_visit,
        }

    @extend_schema_field(serializers.DictField)
    def get_barber_details(self, obj) -> dict:
        """Retorna detalhes do barbeiro"""
        return {
            "id": obj.barber.id,
            "name": obj.barber.get_display_name(),
            "username": obj.barber.username,
        }

    @extend_schema_field(serializers.DictField)
    def get_service_details(self, obj) -> dict:
        """Retorna detalhes do serviço"""
        return {
            "id": obj.service.id,
            "name": obj.service.name,
            "price": str(obj.service.price),
            "formatted_price": obj.service.get_formatted_price(),
            "duration_minutes": obj.service.get_duration_in_minutes(),
            "formatted_duration": obj.service.get_formatted_duration(),
        }

    @extend_schema_field(serializers.DictField)
    def get_barbershop_details(self, obj) -> dict:
        """Retorna detalhes da barbearia"""
        return {
            "id": obj.barbershop.id,
            "name": obj.barbershop.name,
            "address": obj.barbershop.address,
            "phone": obj.barbershop.get_formatted_phone(),
        }


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer otimizado para listagem de avaliações.
    """

    # Campos básicos de relacionamento
    customer_name = serializers.CharField(source="get_customer_name", read_only=True)
    barber_name = serializers.CharField(source="get_barber_name", read_only=True)
    service_name = serializers.CharField(source="get_service_name", read_only=True)
    barbershop_name = serializers.CharField(
        source="get_barbershop_name", read_only=True
    )

    # Campos calculados
    rating_stars = serializers.CharField(source="get_rating_stars", read_only=True)
    rating_display_with_stars = serializers.CharField(
        source="get_rating_display_with_stars", read_only=True
    )
    short_comment = serializers.CharField(source="get_short_comment", read_only=True)
    review_age_days = serializers.IntegerField(
        source="get_review_age_days", read_only=True
    )
    is_positive_review = serializers.BooleanField(read_only=True)
    is_negative_review = serializers.BooleanField(read_only=True)
    is_recent_review = serializers.BooleanField(read_only=True)
    has_comment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "barbershop_customer",
            "barber",
            "service",
            "barbershop",
            "rating",
            "rating_stars",
            "rating_display_with_stars",
            "comment",
            "short_comment",
            "customer_name",
            "barber_name",
            "service_name",
            "barbershop_name",
            "review_age_days",
            "is_positive_review",
            "is_negative_review",
            "is_recent_review",
            "has_comment",
            "created_at",
        ]


class ReviewStatisticsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de avaliações.
    """

    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_distribution = serializers.DictField()
    positive_reviews = serializers.IntegerField()
    negative_reviews = serializers.IntegerField()
    neutral_reviews = serializers.IntegerField()
    reviews_with_comments = serializers.IntegerField()
    recent_reviews = serializers.IntegerField()


# Serializer padrão (usa o DetailSerializer)
ReviewSerializer = ReviewDetailSerializer
