from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.barbershop.models import Barbershop, BarbershopCustomer, Service
from apps.barbershop.serializers import (BarbershopCustomerListSerializer,
                                         BarbershopListSerializer,
                                         ServiceListSerializer)
from apps.user.serializers import UserListSerializer

from .models import Appointment, BarberSchedule

User = get_user_model()


class BarberScheduleSerializer(serializers.ModelSerializer):
    """Serializer for BarberSchedule model with all fields"""

    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)
    work_duration_hours = serializers.FloatField(source="get_work_duration_hours", read_only=True)
    work_duration_minutes = serializers.IntegerField(source="get_work_duration_minutes", read_only=True)
    is_working_now = serializers.BooleanField(read_only=True)
    appointments_count_today = serializers.IntegerField(source="get_appointments_count_today", read_only=True)

    class Meta:
        model = BarberSchedule
        fields = [
            "id",
            "barber",
            "barber_name",
            "barbershop",
            "barbershop_name",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_available",
            "work_duration_hours",
            "work_duration_minutes",
            "is_working_now",
            "appointments_count_today",
        ]
        read_only_fields = ["id"]


class BarberScheduleListSerializer(serializers.ModelSerializer):
    """Serializer for listing barber schedules with essential fields"""

    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)
    work_duration_minutes = serializers.IntegerField(source="get_work_duration_minutes", read_only=True)

    class Meta:
        model = BarberSchedule
        fields = [
            "id",
            "barber",
            "barber_name",
            "barbershop",
            "barbershop_name",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_available",
            "work_duration_minutes",
        ]


class BarberScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating barber schedules"""

    class Meta:
        model = BarberSchedule
        fields = [
            "barber",
            "barbershop",
            "weekday",
            "start_time",
            "end_time",
            "is_available",
        ]

    def validate(self, data):
        """Validate schedule data"""
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError(
                "A hora de início deve ser antes da hora de término"
            )
        return data


class BarberScheduleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating barber schedules"""

    class Meta:
        model = BarberSchedule
        fields = [
            "weekday",
            "start_time",
            "end_time",
            "is_available",
        ]

    def validate(self, data):
        """Validate schedule data"""
        instance = getattr(self, "instance", None)
        start_time = data.get("start_time", instance.start_time if instance else None)
        end_time = data.get("end_time", instance.end_time if instance else None)
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                "A hora de início deve ser antes da hora de término"
            )
        return data


class BarberScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed barber schedule view"""

    barber = UserListSerializer(read_only=True)
    barbershop = BarbershopListSerializer(read_only=True)
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)
    work_duration_hours = serializers.FloatField(source="get_work_duration_hours", read_only=True)
    work_duration_minutes = serializers.IntegerField(source="get_work_duration_minutes", read_only=True)
    is_working_now = serializers.BooleanField(read_only=True)
    appointments_count_today = serializers.IntegerField(source="get_appointments_count_today", read_only=True)

    class Meta:
        model = BarberSchedule
        fields = [
            "id",
            "barber",
            "barbershop",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_available",
            "work_duration_hours",
            "work_duration_minutes",
            "is_working_now",
            "appointments_count_today",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model with all fields"""

    customer_name = serializers.CharField(source="customer.customer.get_full_name", read_only=True)
    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_minutes = serializers.IntegerField(source="get_duration_minutes", read_only=True)
    duration_hours = serializers.FloatField(source="get_duration_hours", read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_in_progress = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    can_be_confirmed = serializers.BooleanField(read_only=True)
    can_be_completed = serializers.BooleanField(read_only=True)
    formatted_datetime = serializers.CharField(source="get_formatted_datetime", read_only=True)
    formatted_date = serializers.CharField(source="get_formatted_date", read_only=True)
    formatted_time = serializers.CharField(source="get_formatted_time", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer",
            "customer_name",
            "barber",
            "barber_name",
            "service",
            "service_name",
            "barbershop",
            "barbershop_name",
            "start_datetime",
            "end_datetime",
            "status",
            "status_display",
            "final_price",
            "created_at",
            "updated_at",
            "duration_minutes",
            "duration_hours",
            "is_today",
            "is_past",
            "is_upcoming",
            "is_in_progress",
            "can_be_cancelled",
            "can_be_confirmed",
            "can_be_completed",
            "formatted_datetime",
            "formatted_date",
            "formatted_time",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing appointments with essential fields"""

    customer_name = serializers.CharField(source="customer.customer.get_full_name", read_only=True)
    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    formatted_datetime = serializers.CharField(source="get_formatted_datetime", read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer",
            "customer_name",
            "barber",
            "barber_name",
            "service",
            "service_name",
            "barbershop",
            "barbershop_name",
            "start_datetime",
            "end_datetime",
            "status",
            "status_display",
            "final_price",
            "formatted_datetime",
            "is_today",
            "is_upcoming",
        ]


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating appointments"""

    class Meta:
        model = Appointment
        fields = [
            "customer",
            "barber",
            "service",
            "barbershop",
            "start_datetime",
            "end_datetime",
            "final_price",
        ]

    def validate(self, data):
        """Validate appointment data"""
        if data["start_datetime"] >= data["end_datetime"]:
            raise serializers.ValidationError(
                "A data e hora de início devem ser antes da data e hora de término"
            )
        
        # Validate that customer is registered at the barbershop
        if data["customer"].barbershop != data["barbershop"]:
            raise serializers.ValidationError(
                "O cliente não está registrado nesta barbearia"
            )
        
        # Validate that service belongs to the barbershop
        if data["service"].barbershop != data["barbershop"]:
            raise serializers.ValidationError(
                "O serviço não pertence a esta barbearia"
            )
        
        return data

    def create(self, validated_data):
        """Create appointment with automatic final price if not provided"""
        if not validated_data.get("final_price"):
            validated_data["final_price"] = validated_data["service"].price
        return super().create(validated_data)


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointments"""

    class Meta:
        model = Appointment
        fields = [
            "start_datetime",
            "end_datetime",
            "status",
            "final_price",
        ]

    def validate(self, data):
        """Validate appointment data"""
        instance = getattr(self, "instance", None)
        start_datetime = data.get("start_datetime", instance.start_datetime if instance else None)
        end_datetime = data.get("end_datetime", instance.end_datetime if instance else None)
        
        if start_datetime and end_datetime and start_datetime >= end_datetime:
            raise serializers.ValidationError(
                "A data e hora de início devem ser antes da data e hora de término"
            )
        return data


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed appointment view"""

    customer = BarbershopCustomerListSerializer(read_only=True)
    barber = UserListSerializer(read_only=True)
    service = ServiceListSerializer(read_only=True)
    barbershop = BarbershopListSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_minutes = serializers.IntegerField(source="get_duration_minutes", read_only=True)
    duration_hours = serializers.FloatField(source="get_duration_hours", read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_in_progress = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    can_be_confirmed = serializers.BooleanField(read_only=True)
    can_be_completed = serializers.BooleanField(read_only=True)
    formatted_datetime = serializers.CharField(source="get_formatted_datetime", read_only=True)
    formatted_date = serializers.CharField(source="get_formatted_date", read_only=True)
    formatted_time = serializers.CharField(source="get_formatted_time", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer",
            "barber",
            "service",
            "barbershop",
            "start_datetime",
            "end_datetime",
            "status",
            "status_display",
            "final_price",
            "created_at",
            "updated_at",
            "duration_minutes",
            "duration_hours",
            "is_today",
            "is_past",
            "is_upcoming",
            "is_in_progress",
            "can_be_cancelled",
            "can_be_confirmed",
            "can_be_completed",
            "formatted_datetime",
            "formatted_date",
            "formatted_time",
        ]