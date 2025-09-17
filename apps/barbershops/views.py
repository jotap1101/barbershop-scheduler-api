from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.core.cache import cache
from django.db.models import Avg
from rest_framework.exceptions import PermissionDenied
from .models import Barbershop, Service, Barber, BarbershopCustomer
from .serializers import (
    BarbershopSerializer, ServiceSerializer,
    BarberSerializer, BarbershopCustomerSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.users.permissions import IsOwner, IsBarber, IsBarberOrOwner

@extend_schema_view(
    list=extend_schema(
        description='List all barbershops. Accessible by anyone.',
        tags=['Barbershops']
    ),
    create=extend_schema(
        description='Create a new barbershop. Only accessible by owners.',
        tags=['Barbershops']
    ),
    retrieve=extend_schema(
        description='Get details of a specific barbershop.',
        tags=['Barbershops']
    ),
    update=extend_schema(
        description='Update a barbershop. Only accessible by the owner.',
        tags=['Barbershops']
    ),
    partial_update=extend_schema(
        description='Partially update a barbershop. Only accessible by the owner.',
        tags=['Barbershops']
    ),
    destroy=extend_schema(
        description='Delete a barbershop. Only accessible by the owner.',
        tags=['Barbershops']
    ),
    statistics=extend_schema(
        description='Get statistics for a specific barbershop. Only accessible by the owner.',
        tags=['Barbershops']
    ),

)
class BarbershopViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing barbershop instances.
    """
    queryset = Barbershop.objects.all()
    serializer_class = BarbershopSerializer
    filterset_fields = ['owner']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']

    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated()]
            # Check role only if user is authenticated
            if self.request.user.is_authenticated and self.request.user.role != 'OWNER':
                raise PermissionDenied("Only owners can create barbershops")
            return permission_classes
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwner()]  # Check authentication and ownership
        return [AllowAny()]  # Allow anyone to view barbershops

    def get_queryset(self):
        if self.action in ['update', 'partial_update', 'destroy'] and self.request.user.is_authenticated:
            if not self.request.user.is_staff:
                try:
                    barbershop_id = int(self.kwargs.get('pk'))
                    barbershop = Barbershop.objects.filter(id=barbershop_id).first()
                    if barbershop and barbershop.owner != self.request.user:
                        raise permissions.PermissionDenied("You don't have permission to modify this barbershop")
                except (TypeError, ValueError):
                    pass

        # Cache queryset for 5 minutes
        cache_key = f'barbershop_queryset_{self.action}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = super().get_queryset()
            if self.request.user.is_authenticated:
                if not self.request.user.is_staff and self.request.user.role == 'OWNER':
                    queryset = queryset.filter(owner=self.request.user)
            cache.set(cache_key, queryset, 300)
        
        return queryset
    @action(detail=True)
    def statistics(self, *args, **kwargs):
        self.permission_classes = [IsOwner]  # Only owners can see statistics
        barbershop = self.get_object()
        cache_key = f'barbershop_stats_{barbershop.id}'
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = {
                'total_customers': BarbershopCustomer.objects.filter(barbershop=barbershop).count(),
                'total_barbers': Barber.objects.filter(barbershops=barbershop).count(),
                'total_services': Service.objects.filter(barbershop=barbershop).count(),
                'avg_service_price': Service.objects.filter(barbershop=barbershop).aggregate(
                    Avg('price')
                )['price__avg']
            }
            cache.set(cache_key, stats, 3600)  # Cache for 1 hour
        
        return Response(stats)
        return Response(stats)

@extend_schema_view(
    list=extend_schema(
        description='List all services. Accessible by anyone.',
        tags=['Services']
    ),
    create=extend_schema(
        description='Create a new service. Only accessible by barbershop owners.',
        tags=['Services']
    ),
    retrieve=extend_schema(
        description='Get details of a specific service.',
        tags=['Services']
    ),
    update=extend_schema(
        description='Update a service. Only accessible by the barbershop owner.',
        tags=['Services']
    ),
    partial_update=extend_schema(
        description='Partially update a service. Only accessible by the barbershop owner.',
        tags=['Services']
    ),
    destroy=extend_schema(
        description='Delete a service. Only accessible by the barbershop owner.',
        tags=['Services']
    )
)
class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing service instances.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filterset_fields = ['barbershop', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'duration']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated()]
            # Verify owner role only if user is authenticated
            if self.request.user.is_authenticated and self.request.user.role != 'OWNER':
                raise permissions.PermissionDenied("Only owners can manage services")
            return permission_classes
        return [AllowAny()]  # Allow anyone to view services

    def get_queryset(self):
        # Filter by barbershop owner for write actions
        if self.action in ['update', 'partial_update', 'destroy'] and not self.request.user.is_staff:
            try:
                service_id = int(self.kwargs.get('pk'))
                service = Service.objects.filter(id=service_id).first()
                if service and service.barbershop.owner != self.request.user:
                    raise permissions.PermissionDenied("You don't have permission to modify this service")
            except (TypeError, ValueError):
                pass
        return super().get_queryset()
        
    def perform_create(self, serializer):
        """Ensure owner owns the barbershop they're adding service to"""
        barbershop = serializer.validated_data['barbershop']
        if barbershop.owner != self.request.user:
            raise permissions.PermissionDenied("You can only add services to your own barbershops")

@extend_schema_view(
    list=extend_schema(
        description='List all barbers. Accessible by anyone.',
        tags=['Barbers']
    ),
    create=extend_schema(
        description='Create a new barber profile. Only accessible by authenticated barbers.',
        tags=['Barbers']
    ),
    retrieve=extend_schema(
        description='Get details of a specific barber.',
        tags=['Barbers']
    ),
    update=extend_schema(
        description='Update a barber profile. Only accessible by the barber themselves or barbershop owner.',
        tags=['Barbers']
    ),
    partial_update=extend_schema(
        description='Partially update a barber profile. Only accessible by the barber themselves or barbershop owner.',
        tags=['Barbers']
    ),
    destroy=extend_schema(
        description='Delete a barber profile. Only accessible by the barber themselves or barbershop owner.',
        tags=['Barbers']
    )
)
class BarberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing barber instances.
    """
    queryset = Barber.objects.all()
    serializer_class = BarberSerializer
    filterset_fields = ['barbershops', 'experience_years']
    search_fields = ['user__first_name', 'user__last_name', 'specialties']
    ordering_fields = ['experience_years', 'user__first_name']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'create':
            # Only authenticated barbers can create profiles
            return [IsAuthenticated(), IsBarber()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsBarberOrOwner()]  # Only barber themselves or owner can modify
        return [AllowAny()]  # Anyone can view barber profiles

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            if self.request.user.role == 'BARBER':
                return queryset.filter(user=self.request.user)
            elif self.request.user.role == 'OWNER':
                barbershops = Barbershop.objects.filter(owner=self.request.user)
                return queryset.filter(barbershops__in=barbershops)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema_view(
    list=extend_schema(
        description='List barbershop customers. Accessible by authenticated users.',
        tags=['Barbershops']
    ),
    create=extend_schema(
        description='Create a new barbershop customer. Only accessible by barbershop owners.',
        tags=['Barbershops']
    ),
    retrieve=extend_schema(
        description='Get details of a specific barbershop customer.',
        tags=['Barbershops']
    ),
    update=extend_schema(
        description='Update a barbershop customer. Only accessible by barbershop owners.',
        tags=['Barbershops']
    ),
    partial_update=extend_schema(
        description='Partially update a barbershop customer. Only accessible by barbershop owners.',
        tags=['Barbershops']
    ),
    destroy=extend_schema(
        description='Delete a barbershop customer. Only accessible by barbershop owners.',
        tags=['Barbershops']
    )
)
class BarbershopCustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing barbershop customer instances.
    """
    queryset = BarbershopCustomer.objects.all()
    serializer_class = BarbershopCustomerSerializer
    filterset_fields = ['barbershop', 'loyalty_points']
    search_fields = ['customer__first_name', 'customer__last_name']
    ordering_fields = ['date_joined', 'loyalty_points']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwner()]  # Only barbershop owners can manage customers
        return [IsAuthenticated()]  # Must be authenticated to view customer info

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            if self.request.user.role == 'CLIENT':
                return queryset.filter(customer=self.request.user)
            elif self.request.user.role == 'OWNER':
                return queryset.filter(barbershop__owner=self.request.user)
        return queryset

    def add_loyalty_points(self, request, *args, **kwargs):
        customer = self.get_object()
        points = request.data.get('points', 0)
        
        if request.user != customer.barbershop.owner:
            return Response(
                {'error': 'Only barbershop owner can add loyalty points'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        customer.loyalty_points += points
        customer.save()
        
        return Response({
            'message': f'{points} points added successfully',
            'total_points': customer.loyalty_points
        })
