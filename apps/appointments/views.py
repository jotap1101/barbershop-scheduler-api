from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from .models import Appointment, BarberSchedule
from .serializers import AppointmentSerializer, BarberScheduleSerializer
from .utils import check_barber_availability
from apps.barbershops.models import BarbershopCustomer
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.users.permissions import IsBarber, IsBarberOrOwner, IsClient
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta

@extend_schema_view(
    list=extend_schema(
        description='List all barber schedules. Accessible by anyone.',
        tags=['Barbers']
    ),
    create=extend_schema(
        description='Create a new schedule. Only accessible by barbers.',
        tags=['Barbers']
    ),
    retrieve=extend_schema(
        description='Get details of a specific schedule.',
        tags=['Barbers']
    ),
    update=extend_schema(
        description='Update a schedule. Only accessible by the barber or barbershop owner.',
        tags=['Barbers']
    ),
    partial_update=extend_schema(
        description='Partially update a schedule. Only accessible by the barber or barbershop owner.',
        tags=['Barbers']
    ),
    destroy=extend_schema(
        description='Delete a schedule. Only accessible by the barber or barbershop owner.',
        tags=['Barbers']
    )
)
class BarberScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing barber schedule instances.
    """
    queryset = BarberSchedule.objects.all()
    serializer_class = BarberScheduleSerializer
    filterset_fields = ['barber', 'barbershop', 'weekday', 'is_available']
    ordering_fields = ['weekday', 'start_time']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsBarberOrOwner()]  # First check auth, then role
        return [AllowAny()]  # Anyone can view schedules

    def get_queryset(self):
        """Filter schedules based on user role"""
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            return queryset
        if not self.request.user.is_staff:
            if self.request.user.role == 'BARBER':
                return queryset.filter(barber=self.request.user)
            elif self.request.user.role == 'OWNER':
                return queryset.filter(barbershop__owner=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Assign current authenticated user as the barber"""
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'barber_profile'):
            raise permissions.PermissionDenied("Only barbers can create schedules")
        serializer.save(barber=self.request.user)
        
    def perform_update(self, serializer):
        """Ensure barber can only update their own schedule"""
        instance = self.get_object()
        if instance.barber != self.request.user and not self.request.user.is_staff:
            if self.request.user.role != 'OWNER' or instance.barbershop.owner != self.request.user:
                raise permissions.PermissionDenied("You don't have permission to update this schedule")
        serializer.save()

@extend_schema_view(
    list=extend_schema(
        description='List appointments. Clients see their own, barbers see theirs, owners see all from their barbershop.',
        tags=['Appointments']
    ),
    create=extend_schema(
        description='Create a new appointment. Only accessible by clients.',
        tags=['Appointments']
    ),
    retrieve=extend_schema(
        description='Get details of a specific appointment.',
        tags=['Appointments']
    ),
    update=extend_schema(
        description='Update an appointment. Only accessible by barbers or barbershop owners.',
        tags=['Appointments']
    ),
    partial_update=extend_schema(
        description='Partially update an appointment. Only accessible by barbers or barbershop owners.',
        tags=['Appointments']
    ),
    destroy=extend_schema(
        description='Cancel/delete an appointment. Only accessible by barbers or barbershop owners.',
        tags=['Appointments']
    ),
    upcoming=extend_schema(
        description='Get list of upcoming appointments.',
        tags=['Appointments']
    ),
    available_slots=extend_schema(
        description='Get available appointment slots for a specific barber and date.',
        tags=['Appointments']
    )
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing appointment instances.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filterset_fields = ['status', 'barbershop', 'barber', 'customer']
    search_fields = ['notes']
    ordering_fields = ['start_datetime', 'created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsClient()]  # Must be authenticated and a client
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsBarberOrOwner()]  # Must be authenticated and barber/owner
        return [IsAuthenticated()]  # Must be authenticated to view appointments
        
    def get_queryset(self):
        cache_key = f'appointment_queryset_{self.request.user.id}_{self.action}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = super().get_queryset()
            user = self.request.user
            
            if not user.is_staff:
                if user.role == 'CLIENT':
                    queryset = queryset.filter(customer__customer=user)
                elif user.role == 'BARBER':
                    queryset = queryset.filter(barber=user)
                elif user.role == 'OWNER':
                    queryset = queryset.filter(barbershop__owner=user)
            
            cache.set(cache_key, queryset, 300)
        
        return queryset

    def perform_create(self, serializer):
        # Get the customer record - this will 404 if not found
        customer = get_object_or_404(
            BarbershopCustomer,
            customer=self.request.user,
            barbershop=serializer.validated_data['barbershop']
        )
        
        # Check barber availability
        is_available, message = check_barber_availability(
            serializer.validated_data['barber'],
            serializer.validated_data['barbershop'],
            serializer.validated_data['start_datetime'],
            serializer.validated_data['end_datetime']
        )
        
        if not is_available:
            raise serializers.ValidationError({'non_field_errors': [message]})
        
        # Set the customer and save
        serializer.save(customer=customer)

    def get_queryset(self):
        cache_key = f'appointment_queryset_{self.request.user.id}_{self.action}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = super().get_queryset()
            user = self.request.user
            
            if not user.is_staff:
                if user.role == 'CLIENT':
                    queryset = queryset.filter(customer__customer=user)
                elif user.role == 'BARBER':
                    queryset = queryset.filter(barber=user)
                elif user.role == 'OWNER':
                    queryset = queryset.filter(barbershop__owner=user)
            
            cache.set(cache_key, queryset, 300)
        
        return queryset

    def perform_create(self, serializer):
        # Get or create BarbershopCustomer instance
        customer = get_object_or_404(
            BarbershopCustomer,
            customer=self.request.user,
            barbershop=serializer.validated_data['barbershop']
        )
        
        # Check barber availability
        is_available, message = check_barber_availability(
            serializer.validated_data['barber'],
            serializer.validated_data['barbershop'],
            serializer.validated_data['start_datetime'],
            serializer.validated_data['end_datetime']
        )
        
        if not is_available:
            raise serializer.ValidationError(message)
        
        serializer.save(customer=customer)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        now = timezone.now()
        appointments = self.get_queryset().filter(
            start_datetime__gte=now,
            status__in=['PENDING', 'CONFIRMED']
        ).order_by('start_datetime')[:10]
        
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        date = request.query_params.get('date')
        barber_id = request.query_params.get('barber')
        barbershop_id = request.query_params.get('barbershop')
        
        if not all([date, barber_id, barbershop_id]):
            return Response(
                {'error': 'Missing required parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get barber's schedule for the day
        schedule = BarberSchedule.objects.filter(
            barber_id=barber_id,
            barbershop_id=barbershop_id,
            weekday=date.weekday(),
            is_available=True
        ).first()
        
        if not schedule:
            return Response([])
        
        # Get all appointments for that day
        appointments = Appointment.objects.filter(
            barber_id=barber_id,
            barbershop_id=barbershop_id,
            start_datetime__date=date,
            status__in=['PENDING', 'CONFIRMED']
        ).order_by('start_datetime')
        
        # Generate available time slots
        available_slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=30)
            is_available = not appointments.filter(
                start_datetime__lt=slot_end,
                end_datetime__gt=current_time
            ).exists()
            
            if is_available:
                available_slots.append({
                    'start_time': current_time.time().isoformat(),
                    'end_time': slot_end.time().isoformat()
                })
            
            current_time = slot_end
        
        return Response(available_slots)
