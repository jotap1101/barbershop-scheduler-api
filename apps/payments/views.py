from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Payment
from .serializers import PaymentSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from apps.users.permissions import IsOwner, IsBarber, IsClient

@extend_schema_view(
    list=extend_schema(
        description='List payments. Clients see their own, barbers see theirs, owners see all from their barbershop.',
        tags=['Payments']
    ),
    create=extend_schema(
        description='Create a new payment record. Only accessible by barbershop owners.',
        tags=['Payments']
    ),
    retrieve=extend_schema(
        description='Get details of a specific payment.',
        tags=['Payments']
    ),
    update=extend_schema(
        description='Update a payment record. Only accessible by barbershop owners.',
        tags=['Payments']
    ),
    partial_update=extend_schema(
        description='Partially update a payment record. Only accessible by barbershop owners.',
        tags=['Payments']
    ),
    destroy=extend_schema(
        description='Delete a payment record. Only accessible by barbershop owners.',
        tags=['Payments']
    ),
    summary=extend_schema(
        description='Get a summary of payments including totals and method distribution.',
        tags=['Payments']
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing payment instances.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_fields = ['status', 'method']
    ordering_fields = ['created_at', 'payment_date', 'amount']
    
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'summary']:
            permission_classes = [IsAuthenticated()]
            # Check if user is owner after authentication
            if self.request.user.is_authenticated and self.request.user.role != 'OWNER':
                raise PermissionDenied("Only owners can manage payments")
            return permission_classes
        return [IsAuthenticated()]  # Must be authenticated to view payments

    def get_queryset(self):
        cache_key = f'payment_queryset_{self.request.user.id}_{self.action}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = super().get_queryset()
            user = self.request.user
            
            if not user.is_staff:
                if user.role == 'CLIENT':
                    queryset = queryset.filter(
                        appointment__customer__customer=user
                    )
                elif user.role == 'BARBER':
                    queryset = queryset.filter(
                        appointment__barber=user
                    )
                elif user.role == 'OWNER':
                    queryset = queryset.filter(
                        appointment__barbershop__owner=user
                    )
            
            cache.set(cache_key, queryset, 300)
        
        return queryset

    def perform_create(self, serializer):
        appointment = serializer.validated_data['appointment']
        if appointment.barbershop.owner != self.request.user:
            raise PermissionDenied("You can only manage payments for your own barbershops")
        
        if serializer.validated_data.get('status') == Payment.Status.PAID:
            serializer.validated_data['payment_date'] = timezone.now()
        
        serializer.save()

    @action(detail=False, methods=['get'])
    def summary(self, request):
        payments = self.get_queryset()
        today = timezone.now().date()
        
        # Calculate payment summaries
        daily_total = payments.filter(
            created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_total = payments.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Get payment methods distribution
        method_distribution = payments.filter(
            status=Payment.Status.PAID
        ).values('method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        return Response({
            'daily_total': daily_total,
            'monthly_total': monthly_total,
            'method_distribution': method_distribution
        })
