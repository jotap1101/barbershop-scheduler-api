from rest_framework import serializers
from .models import Barbershop, Service, Barber, BarbershopCustomer
from django.contrib.auth import get_user_model

User = get_user_model()

class BarbershopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barbershop
        fields = ['id', 'name', 'address', 'phone', 'owner', 'description',
                'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'barbershop', 'name', 'description', 'price', 'duration',
                'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BarberSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    barbershops = BarbershopSerializer(many=True, read_only=True)

    class Meta:
        model = Barber
        fields = ['id', 'user', 'user_details', 'barbershops', 'specialties',
                'experience_years', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_user_details(self, obj):
        return {
            'name': obj.user.get_full_name(),
            'email': obj.user.email,
            'phone': obj.user.phone
        }

class BarbershopCustomerSerializer(serializers.ModelSerializer):
    customer_details = serializers.SerializerMethodField()
    barbershop_details = BarbershopSerializer(source='barbershop', read_only=True)

    class Meta:
        model = BarbershopCustomer
        fields = ['id', 'customer', 'customer_details', 'barbershop',
                'barbershop_details', 'loyalty_points', 'date_joined',
                'last_visit', 'notes']
        read_only_fields = ['date_joined', 'last_visit']

    def get_customer_details(self, obj):
        return {
            'name': obj.customer.get_full_name(),
            'email': obj.customer.email,
            'phone': obj.customer.phone
        }