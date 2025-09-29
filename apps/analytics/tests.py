from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.user.models import User
from apps.barbershop.models import Barbershop, Service
from apps.appointment.models import Appointment
from apps.payment.models import Payment


class AnalyticsTestCase(APITestCase):
    """
    Classe base para testes de analytics.
    """
    
    def setUp(self):
        """
        Configuração inicial dos testes.
        """
        # Criar usuários de teste
        self.admin_user = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="testpass123",
            role=User.Role.ADMIN,
            first_name="Admin",
            last_name="User"
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True,
            first_name="Owner",
            last_name="User"
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER,
            first_name="Barber",
            last_name="User"
        )
        
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            first_name="Client",
            last_name="User"
        )
        
        # Criar barbearia de teste
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        # Criar serviço de teste
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=25.00,
            duration=30
        )
    
    def authenticate_user(self, user):
        """
        Autentica um usuário para os testes.
        """
        self.client.force_authenticate(user=user)


class DashboardOverviewTestCase(AnalyticsTestCase):
    """
    Testes para o endpoint de dashboard overview.
    """
    
    def test_dashboard_overview_admin_access(self):
        """
        Testa se apenas admins podem acessar dashboard overview.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_barbershops', response.data)
        self.assertIn('total_users', response.data)
    
    def test_dashboard_overview_non_admin_denied(self):
        """
        Testa se não-admins são negados acesso ao dashboard.
        """
        self.authenticate_user(self.client_user)
        url = reverse('dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BarbershopAnalyticsTestCase(AnalyticsTestCase):
    """
    Testes para analytics de barbearia.
    """
    
    def test_barbershop_analytics_owner_access(self):
        """
        Testa se o proprietário pode acessar analytics da sua barbearia.
        """
        self.authenticate_user(self.owner_user)
        url = reverse('barbershop-analytics', kwargs={'barbershop_id': self.barbershop.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barbershop_name'], 'Test Barbershop')
    
    def test_barbershop_analytics_invalid_id(self):
        """
        Testa resposta para ID de barbearia inválido.
        """
        self.authenticate_user(self.admin_user)
        invalid_id = '00000000-0000-0000-0000-000000000000'
        url = reverse('barbershop-analytics', kwargs={'barbershop_id': invalid_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BarberPerformanceTestCase(AnalyticsTestCase):
    """
    Testes para performance de barbeiros.
    """
    
    def test_barber_performance_data(self):
        """
        Testa se a performance do barbeiro é retornada corretamente.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('barber-performance', kwargs={'barber_id': self.barber_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barber_name'], 'Barber User')
        self.assertIn('total_appointments', response.data)
        self.assertIn('total_revenue', response.data)


class MyAnalyticsTestCase(AnalyticsTestCase):
    """
    Testes para analytics personalizadas.
    """
    
    def test_my_analytics_admin(self):
        """
        Testa se admin recebe dashboard overview nas suas analytics.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('my-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_barbershops', response.data)
    
    def test_my_analytics_owner(self):
        """
        Testa se proprietário recebe analytics da sua barbearia.
        """
        self.authenticate_user(self.owner_user)
        url = reverse('my-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barbershop_name'], 'Test Barbershop')
    
    def test_my_analytics_barber(self):
        """
        Testa se barbeiro recebe sua performance.
        """
        self.authenticate_user(self.barber_user)
        url = reverse('my-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barber_name'], 'Barber User')
    
    def test_my_analytics_client_no_access(self):
        """
        Testa se cliente comum não tem acesso a analytics.
        """
        self.authenticate_user(self.client_user)
        url = reverse('my-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RevenueAnalyticsTestCase(AnalyticsTestCase):
    """
    Testes para analytics de receita.
    """
    
    def test_revenue_analytics_default_params(self):
        """
        Testa analytics de receita com parâmetros padrão.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('revenue-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_revenue_analytics_custom_params(self):
        """
        Testa analytics de receita com parâmetros customizados.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('revenue-analytics')
        response = self.client.get(url, {'period': 'daily', 'days': 7})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class ServicePopularityTestCase(AnalyticsTestCase):
    """
    Testes para popularidade de serviços.
    """
    
    def test_service_popularity(self):
        """
        Testa endpoint de popularidade de serviços.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('service-popularity')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_service_popularity_filtered(self):
        """
        Testa popularidade filtrada por barbearia.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('service-popularity')
        response = self.client.get(url, {'barbershop_id': str(self.barbershop.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class CustomerInsightsTestCase(AnalyticsTestCase):
    """
    Testes para insights de clientes.
    """
    
    def test_customer_insights(self):
        """
        Testa endpoint de insights de clientes.
        """
        self.authenticate_user(self.admin_user)
        url = reverse('customer-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_customers', response.data)
        self.assertIn('customer_retention_rate', response.data)