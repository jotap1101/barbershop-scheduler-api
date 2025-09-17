from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Appointment, BarberSchedule
from apps.barbershops.serializers import BarbershopSerializer, ServiceSerializer

class BarberScheduleSerializer(serializers.ModelSerializer):
    barber_name = serializers.SerializerMethodField()
    barbershop_details = BarbershopSerializer(source='barbershop', read_only=True)

    class Meta:
        model = BarberSchedule
        fields = ['id', 'barber', 'barber_name', 'barbershop', 'barbershop_details',
                'weekday', 'start_time', 'end_time', 'is_available']

    @extend_schema_field(str)
    def get_barber_name(self, obj: BarberSchedule) -> str:
        return obj.barber.get_full_name()

    def validate(self, data: dict) -> dict:
        if 'start_time' in data and 'end_time' in data and data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data

class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    barber_name = serializers.SerializerMethodField()
    service_details = ServiceSerializer(source='service', read_only=True)
    barbershop_details = BarbershopSerializer(source='barbershop', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'customer', 'customer_name', 'barber', 'barber_name',
                'service', 'service_details', 'barbershop', 'barbershop_details',
                'start_datetime', 'end_datetime', 'status', 'final_price',
                'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(str)
    def get_customer_name(self, obj: Appointment) -> str:
        return obj.customer.customer.get_full_name()

    @extend_schema_field(str)
    def get_barber_name(self, obj: Appointment) -> str:
        return obj.barber.get_full_name()

    def validate(self, data: dict) -> dict:
        if 'start_datetime' in data and 'end_datetime' in data and data['start_datetime'] >= data['end_datetime']:
            raise serializers.ValidationError("End time must be after start time")
        return data