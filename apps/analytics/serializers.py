from rest_framework import serializers


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer para overview geral do dashboard"""
    
    total_barbershops = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_appointments_today = serializers.IntegerField()
    total_revenue_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_appointments_this_month = serializers.IntegerField()
    total_revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    active_barbers = serializers.IntegerField()
    pending_appointments = serializers.IntegerField()


class BarbershopAnalyticsSerializer(serializers.Serializer):
    """Serializer para analytics específicas de uma barbearia"""
    
    barbershop_id = serializers.UUIDField()
    barbershop_name = serializers.CharField()
    total_customers = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    appointments_this_month = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_service = serializers.CharField(allow_null=True)
    most_popular_barber = serializers.CharField(allow_null=True)


class BarberPerformanceSerializer(serializers.Serializer):
    """Serializer para performance de barbeiros"""
    
    barber_id = serializers.UUIDField()
    barber_name = serializers.CharField()
    total_appointments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    appointments_this_month = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class RevenueAnalyticsSerializer(serializers.Serializer):
    """Serializer para analytics de receita"""
    
    period = serializers.CharField()  # 'daily', 'weekly', 'monthly'
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    appointments_count = serializers.IntegerField()
    average_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)


class ServicePopularitySerializer(serializers.Serializer):
    """Serializer para popularidade de serviços"""
    
    service_id = serializers.UUIDField()
    service_name = serializers.CharField()
    barbershop_name = serializers.CharField()
    appointments_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    booking_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class CustomerInsightsSerializer(serializers.Serializer):
    """Serializer para insights de clientes"""
    
    total_customers = serializers.IntegerField()
    new_customers_this_month = serializers.IntegerField()
    returning_customers = serializers.IntegerField()
    average_appointments_per_customer = serializers.DecimalField(max_digits=5, decimal_places=2)
    customer_retention_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    most_frequent_customer = serializers.CharField(allow_null=True)