from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    BarberPerformanceSerializer,
    BarbershopAnalyticsSerializer,
    CustomerInsightsSerializer,
    DashboardOverviewSerializer,
    RevenueAnalyticsSerializer,
    ServicePopularitySerializer,
)
from .utils import (
    get_barber_performance,
    get_barbershop_analytics,
    get_customer_insights,
    get_dashboard_overview,
    get_revenue_analytics,
    get_service_popularity,
)
from apps.user.permissions import IsAdminOnly, IsOwnerOrAdmin
from utils.throttles.custom_throttles import AdminThrottle


class DashboardOverviewView(APIView):
    """
    View para overview geral do dashboard administrativo.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOnly]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Dashboard Overview",
        description="Retorna métricas gerais do sistema para administradores.",
        responses={200: DashboardOverviewSerializer},
        tags=["analytics"]
    )
    def get(self, request):
        """
        Retorna dados gerais para o dashboard administrativo.
        """
        overview_data = get_dashboard_overview()
        serializer = DashboardOverviewSerializer(data=overview_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class BarbershopAnalyticsView(APIView):
    """
    View para analytics específicas de uma barbearia.
    """
    
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Analytics de Barbearia",
        description="Retorna analytics específicas de uma barbearia.",
        responses={200: BarbershopAnalyticsSerializer},
        tags=["analytics"]
    )
    def get(self, request, barbershop_id):
        """
        Retorna analytics de uma barbearia específica.
        """
        analytics_data = get_barbershop_analytics(str(barbershop_id))
        
        if not analytics_data:
            return Response(
                {"error": "Barbearia não encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar permissão para proprietários de barbearia
        user = request.user
        if (hasattr(user, 'role') and user.role != 'ADMIN' and 
            hasattr(user, 'is_barbershop_owner') and user.is_barbershop_owner):
            # Verificar se o usuário é dono desta barbearia
            from apps.barbershop.models import Barbershop
            try:
                barbershop = Barbershop.objects.get(id=barbershop_id, owner=user)
            except Barbershop.DoesNotExist:
                return Response(
                    {"error": "Acesso negado a esta barbearia."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = BarbershopAnalyticsSerializer(data=analytics_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class BarberPerformanceView(APIView):
    """
    View para performance de barbeiros.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Performance de Barbeiro",
        description="Retorna métricas de performance de um barbeiro específico.",
        responses={200: BarberPerformanceSerializer},
        tags=["analytics"]
    )
    def get(self, request, barber_id):
        """
        Retorna métricas de performance de um barbeiro.
        """
        performance_data = get_barber_performance(str(barber_id))
        
        if not performance_data:
            return Response(
                {"error": "Barbeiro não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = BarberPerformanceSerializer(data=performance_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class RevenueAnalyticsView(APIView):
    """
    View para analytics de receita.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Analytics de Receita",
        description="Retorna analytics de receita por período.",
        responses={200: RevenueAnalyticsSerializer(many=True)},
        tags=["analytics"]
    )
    def get(self, request):
        """
        Retorna analytics de receita.
        """
        period = request.query_params.get('period', 'daily')
        try:
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError):
            days = 30
        
        # Limitar dias para evitar consultas muito pesadas
        days = min(days, 365)
        
        analytics_data = get_revenue_analytics(period=period, days=days)
        serializer = RevenueAnalyticsSerializer(data=analytics_data, many=True)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class ServicePopularityView(APIView):
    """
    View para popularidade de serviços.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Popularidade de Serviços",
        description="Retorna analytics de popularidade dos serviços.",
        responses={200: ServicePopularitySerializer(many=True)},
        tags=["analytics"]
    )
    def get(self, request):
        """
        Retorna popularidade dos serviços.
        """
        barbershop_id = request.query_params.get('barbershop_id')
        popularity_data = get_service_popularity(barbershop_id=barbershop_id)
        
        serializer = ServicePopularitySerializer(data=popularity_data, many=True)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class CustomerInsightsView(APIView):
    """
    View para insights de clientes.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Insights de Clientes",
        description="Retorna insights sobre o comportamento dos clientes.",
        responses={200: CustomerInsightsSerializer},
        tags=["analytics"]
    )
    def get(self, request):
        """
        Retorna insights sobre clientes.
        """
        barbershop_id = request.query_params.get('barbershop_id')
        insights_data = get_customer_insights(barbershop_id=barbershop_id)
        
        if not insights_data:
            return Response(
                {"error": "Dados não encontrados."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CustomerInsightsSerializer(data=insights_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class MyAnalyticsView(APIView):
    """
    View para analytics personalizadas do usuário.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminThrottle]
    
    @extend_schema(
        summary="Minhas Analytics",
        description="Retorna analytics personalizadas baseadas no tipo de usuário.",
        responses={200: DashboardOverviewSerializer},
        tags=["analytics"]
    )
    def get(self, request):
        """
        Retorna analytics personalizadas baseadas no tipo de usuário.
        """
        user = request.user
        
        if hasattr(user, 'role') and user.role == 'ADMIN':
            # Admin vê overview geral
            overview_data = get_dashboard_overview()
            serializer = DashboardOverviewSerializer(data=overview_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
        
        elif hasattr(user, 'is_barbershop_owner') and user.is_barbershop_owner:
            # Proprietário vê analytics das suas barbearias
            from apps.barbershop.models import Barbershop
            barbershops = Barbershop.objects.filter(owner=user)
            
            if not barbershops.exists():
                return Response(
                    {"message": "Nenhuma barbearia encontrada."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Retornar analytics da primeira barbearia
            barbershop = barbershops.first()
            analytics_data = get_barbershop_analytics(str(barbershop.id))
            
            if analytics_data:
                serializer = BarbershopAnalyticsSerializer(data=analytics_data)
                serializer.is_valid(raise_exception=True)
                return Response(serializer.data)
        
        elif hasattr(user, 'role') and user.role == 'BARBER':
            # Barbeiro vê sua performance
            performance_data = get_barber_performance(str(user.id))
            
            if performance_data:
                serializer = BarberPerformanceSerializer(data=performance_data)
                serializer.is_valid(raise_exception=True)
                return Response(serializer.data)
        
        return Response(
            {"message": "Analytics não disponíveis para este tipo de usuário."},
            status=status.HTTP_404_NOT_FOUND
        )