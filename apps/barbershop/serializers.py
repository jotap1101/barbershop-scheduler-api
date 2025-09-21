from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Barbershop, BarbershopCustomer, Service

User = get_user_model()


class BarbershopSerializer(serializers.ModelSerializer):
    """Serializer for Barbershop model with all fields"""

    formatted_cnpj = serializers.CharField(source="get_formatted_cnpj", read_only=True)
    formatted_phone = serializers.CharField(
        source="get_formatted_phone", read_only=True
    )
    total_services = serializers.IntegerField(read_only=True)
    available_services_count = serializers.IntegerField(read_only=True)
    average_service_price = serializers.DecimalField(
        source="get_average_service_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    total_customers = serializers.IntegerField(read_only=True)
    total_appointments = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        source="get_total_revenue", max_digits=15, decimal_places=2, read_only=True
    )
    has_logo = serializers.BooleanField(read_only=True)
    has_contact_info = serializers.BooleanField(read_only=True)

    class Meta:
        model = Barbershop
        fields = [
            "id",
            "name",
            "description",
            "cnpj",
            "formatted_cnpj",
            "address",
            "email",
            "phone",
            "formatted_phone",
            "website",
            "logo",
            "owner",
            "created_at",
            "updated_at",
            "total_services",
            "available_services_count",
            "average_service_price",
            "total_customers",
            "total_appointments",
            "total_revenue",
            "has_logo",
            "has_contact_info",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BarbershopCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating barbershops"""

    class Meta:
        model = Barbershop
        fields = [
            "name",
            "description",
            "cnpj",
            "address",
            "email",
            "phone",
            "website",
            "logo",
        ]

    def validate_cnpj(self, value):
        """Validate CNPJ format"""
        if value:
            # Remove formatting characters
            cnpj = "".join(filter(str.isdigit, value))
            if len(cnpj) != 14:
                raise serializers.ValidationError("CNPJ deve ter 14 dígitos.")
        return value

    def validate_email(self, value):
        """Validate unique email for barbershops"""
        if Barbershop.objects.filter(email=value).exists():
            raise serializers.ValidationError("Já existe uma barbearia com este email.")
        return value

    def create(self, validated_data):
        """Create barbershop with current user as owner"""
        request = self.context.get("request")
        validated_data["owner"] = request.user

        # Set user as barbershop owner if not already
        if not request.user.is_barbershop_owner:
            request.user.is_barbershop_owner = True
            request.user.save(update_fields=["is_barbershop_owner"])

        return Barbershop.objects.create(**validated_data)


class BarbershopUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating barbershops"""

    class Meta:
        model = Barbershop
        fields = [
            "name",
            "description",
            "cnpj",
            "address",
            "email",
            "phone",
            "website",
            "logo",
        ]

    def validate_cnpj(self, value):
        """Validate CNPJ format"""
        if value:
            # Remove formatting characters
            cnpj = "".join(filter(str.isdigit, value))
            if len(cnpj) != 14:
                raise serializers.ValidationError("CNPJ deve ter 14 dígitos.")
        return value

    def validate_email(self, value):
        """Validate unique email for barbershops (excluding current instance)"""
        if (
            value
            and Barbershop.objects.filter(email=value)
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError("Já existe uma barbearia com este email.")
        return value


class BarbershopDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for barbershop profile"""

    formatted_cnpj = serializers.CharField(source="get_formatted_cnpj", read_only=True)
    formatted_phone = serializers.CharField(
        source="get_formatted_phone", read_only=True
    )
    total_services = serializers.IntegerField(read_only=True)
    available_services_count = serializers.IntegerField(read_only=True)
    average_service_price = serializers.DecimalField(
        source="get_average_service_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    total_customers = serializers.IntegerField(read_only=True)
    total_appointments = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        source="get_total_revenue", max_digits=15, decimal_places=2, read_only=True
    )
    has_logo = serializers.BooleanField(read_only=True)
    has_contact_info = serializers.BooleanField(read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = Barbershop
        fields = [
            "id",
            "name",
            "description",
            "cnpj",
            "formatted_cnpj",
            "address",
            "email",
            "phone",
            "formatted_phone",
            "website",
            "logo",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
            "total_services",
            "available_services_count",
            "average_service_price",
            "total_customers",
            "total_appointments",
            "total_revenue",
            "has_logo",
            "has_contact_info",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class BarbershopListSerializer(serializers.ModelSerializer):
    """Simplified serializer for barbershop lists"""

    formatted_phone = serializers.CharField(
        source="get_formatted_phone", read_only=True
    )
    total_services = serializers.IntegerField(read_only=True)
    average_service_price = serializers.DecimalField(
        source="get_average_service_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    has_logo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Barbershop
        fields = [
            "id",
            "name",
            "description",
            "address",
            "email",
            "phone",
            "formatted_phone",
            "website",
            "logo",
            "owner_name",
            "total_services",
            "average_service_price",
            "has_logo",
        ]


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model with all fields"""

    formatted_price = serializers.CharField(
        source="get_formatted_price", read_only=True
    )
    duration_in_minutes = serializers.IntegerField(read_only=True)
    formatted_duration = serializers.CharField(
        source="get_formatted_duration", read_only=True
    )
    total_appointments = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        source="get_total_revenue", max_digits=15, decimal_places=2, read_only=True
    )
    average_rating = serializers.DecimalField(
        source="get_average_rating", max_digits=3, decimal_places=2, read_only=True
    )
    is_popular = serializers.BooleanField(read_only=True)
    has_description = serializers.BooleanField(read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "barbershop",
            "barbershop_name",
            "name",
            "description",
            "image",
            "price",
            "formatted_price",
            "duration",
            "duration_in_minutes",
            "formatted_duration",
            "available",
            "created_at",
            "updated_at",
            "total_appointments",
            "total_revenue",
            "average_rating",
            "is_popular",
            "has_description",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating services"""

    class Meta:
        model = Service
        fields = [
            "barbershop",
            "name",
            "description",
            "image",
            "price",
            "duration",
            "available",
        ]

    def validate_barbershop(self, value):
        """Validate user owns the barbershop"""
        request = self.context.get("request")
        if value.owner != request.user and request.user.role != "ADMIN":
            raise serializers.ValidationError(
                "Você só pode criar serviços para suas próprias barbearias."
            )
        return value

    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating services"""

    class Meta:
        model = Service
        fields = [
            "name",
            "description",
            "image",
            "price",
            "duration",
            "available",
        ]

    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for service profile"""

    formatted_price = serializers.CharField(
        source="get_formatted_price", read_only=True
    )
    duration_in_minutes = serializers.IntegerField(read_only=True)
    formatted_duration = serializers.CharField(
        source="get_formatted_duration", read_only=True
    )
    total_appointments = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        source="get_total_revenue", max_digits=15, decimal_places=2, read_only=True
    )
    average_rating = serializers.DecimalField(
        source="get_average_rating", max_digits=3, decimal_places=2, read_only=True
    )
    is_popular = serializers.BooleanField(read_only=True)
    has_description = serializers.BooleanField(read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    barbershop_owner = serializers.CharField(
        source="barbershop.owner.get_full_name", read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "barbershop",
            "barbershop_name",
            "barbershop_owner",
            "name",
            "description",
            "image",
            "price",
            "formatted_price",
            "duration",
            "duration_in_minutes",
            "formatted_duration",
            "available",
            "created_at",
            "updated_at",
            "total_appointments",
            "total_revenue",
            "average_rating",
            "is_popular",
            "has_description",
        ]
        read_only_fields = ["id", "barbershop", "created_at", "updated_at"]


class ServiceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for service lists"""

    formatted_price = serializers.CharField(
        source="get_formatted_price", read_only=True
    )
    formatted_duration = serializers.CharField(
        source="get_formatted_duration", read_only=True
    )
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    is_popular = serializers.BooleanField(read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "barbershop",
            "barbershop_name",
            "name",
            "description",
            "image",
            "price",
            "formatted_price",
            "duration",
            "formatted_duration",
            "available",
            "is_popular",
        ]


class BarbershopCustomerSerializer(serializers.ModelSerializer):
    """Serializer for BarbershopCustomer model with all fields"""

    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )
    customer_username = serializers.CharField(
        source="customer.username", read_only=True
    )
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    total_appointments = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(
        source="get_total_spent", max_digits=15, decimal_places=2, read_only=True
    )
    average_rating_given = serializers.DecimalField(
        source="get_average_rating_given",
        max_digits=3,
        decimal_places=2,
        read_only=True,
    )
    is_frequent_customer = serializers.BooleanField(read_only=True)
    is_vip_customer = serializers.BooleanField(read_only=True)
    days_since_last_visit = serializers.IntegerField(read_only=True)
    is_active_customer = serializers.BooleanField(read_only=True)
    customer_tier = serializers.CharField(source="get_customer_tier", read_only=True)

    class Meta:
        model = BarbershopCustomer
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_username",
            "customer_email",
            "barbershop",
            "barbershop_name",
            "last_visit",
            "total_appointments",
            "total_spent",
            "average_rating_given",
            "is_frequent_customer",
            "is_vip_customer",
            "days_since_last_visit",
            "is_active_customer",
            "customer_tier",
        ]
        read_only_fields = ["id"]


class BarbershopCustomerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for barbershop customer relationship"""

    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )
    customer_username = serializers.CharField(
        source="customer.username", read_only=True
    )
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    total_appointments = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(
        source="get_total_spent", max_digits=15, decimal_places=2, read_only=True
    )
    average_rating_given = serializers.DecimalField(
        source="get_average_rating_given",
        max_digits=3,
        decimal_places=2,
        read_only=True,
    )
    is_frequent_customer = serializers.BooleanField(read_only=True)
    is_vip_customer = serializers.BooleanField(read_only=True)
    days_since_last_visit = serializers.IntegerField(read_only=True)
    is_active_customer = serializers.BooleanField(read_only=True)
    customer_tier = serializers.CharField(source="get_customer_tier", read_only=True)

    class Meta:
        model = BarbershopCustomer
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_username",
            "customer_email",
            "customer_phone",
            "barbershop",
            "barbershop_name",
            "last_visit",
            "total_appointments",
            "total_spent",
            "average_rating_given",
            "is_frequent_customer",
            "is_vip_customer",
            "days_since_last_visit",
            "is_active_customer",
            "customer_tier",
        ]
        read_only_fields = ["id", "customer", "barbershop"]


class BarbershopCustomerListSerializer(serializers.ModelSerializer):
    """Simplified serializer for barbershop customer lists"""

    customer_name = serializers.CharField(
        source="customer.get_full_name", read_only=True
    )
    customer_username = serializers.CharField(
        source="customer.username", read_only=True
    )
    total_appointments = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(
        source="get_total_spent", max_digits=15, decimal_places=2, read_only=True
    )
    customer_tier = serializers.CharField(source="get_customer_tier", read_only=True)
    is_active_customer = serializers.BooleanField(read_only=True)

    class Meta:
        model = BarbershopCustomer
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_username",
            "barbershop",
            "last_visit",
            "total_appointments",
            "total_spent",
            "customer_tier",
            "is_active_customer",
        ]
