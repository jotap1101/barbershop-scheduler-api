from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.appointment.models import Appointment
from apps.barbershop.models import Barbershop, BarbershopCustomer, Service

from .models import Payment
from .serializers import (PaymentConfirmSerializer, PaymentCreateSerializer,
                          PaymentRefundSerializer, PaymentSerializer,
                          PaymentUpdateSerializer)
from .utils import (calculate_payment_statistics,
                    create_payment_from_appointment,
                    validate_payment_confirmation, validate_payment_creation,
                    validate_payment_refund)

User = get_user_model()


class PaymentModelTests(TestCase):
    """Testes para o modelo Payment"""
    
    def setUp(self):
        """Configura dados de teste"""
        # Criar usuários
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        # Criar barbearia
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        # Criar serviço
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        # Criar customer relationship
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
    
    def test_payment_creation(self):
        """Testa a criação de um pagamento"""
        payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PENDING
        )
        
        self.assertIsNotNone(payment.id)
        self.assertEqual(payment.appointment, self.appointment)
        self.assertEqual(payment.amount, Decimal('30.00'))
        self.assertEqual(payment.method, Payment.Method.PIX)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertIsNotNone(payment.transaction_id)
    
    def test_payment_str(self):
        """Testa a representação em string do pagamento"""
        payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PENDING
        )
        
        expected_str = f"Pagamento {payment.id} - Pendente"
        self.assertEqual(str(payment), expected_str)
    
    def test_payment_status_methods(self):
        """Testa os métodos de verificação de status"""
        payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PENDING
        )
        
        self.assertTrue(payment.is_pending())
        self.assertFalse(payment.is_paid())
        self.assertFalse(payment.is_refunded())
        
        payment.status = Payment.Status.PAID
        payment.save()
        
        self.assertFalse(payment.is_pending())
        self.assertTrue(payment.is_paid())
        self.assertFalse(payment.is_refunded())
    
    def test_payment_type_methods(self):
        """Testa os métodos de verificação de tipo de pagamento"""
        # Pagamento PIX
        pix_payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX
        )
        
        self.assertTrue(pix_payment.is_digital_payment())
        self.assertFalse(pix_payment.is_card_payment())
        self.assertFalse(pix_payment.is_cash_payment())
        
        # Criar outro agendamento para testar outro pagamento
        appointment2 = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=2),
            end_datetime=timezone.now() + timedelta(hours=2, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        # Pagamento em dinheiro
        cash_payment = Payment.objects.create(
            appointment=appointment2,
            amount=Decimal('30.00'),
            method=Payment.Method.CASH
        )
        
        self.assertFalse(cash_payment.is_digital_payment())
        self.assertFalse(cash_payment.is_card_payment())
        self.assertTrue(cash_payment.is_cash_payment())
    
    def test_mark_as_paid(self):
        """Testa marcar pagamento como pago"""
        payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PENDING
        )
        
        payment.mark_as_paid()
        payment.refresh_from_db()
        
        self.assertTrue(payment.is_paid())
        self.assertIsNotNone(payment.payment_date)
    
    def test_mark_as_refunded(self):
        """Testa marcar pagamento como reembolsado"""
        payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PAID,
            payment_date=timezone.now()
        )
        
        payment.mark_as_refunded()
        payment.refresh_from_db()
        
        self.assertTrue(payment.is_refunded())
    
    def test_get_formatted_amount(self):
        """Testa formatação do valor"""
        payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('1250.50'),
            method=Payment.Method.PIX
        )
        
        formatted = payment.get_formatted_amount()
        self.assertIn("R$", formatted)
        self.assertIn("1.250,50", formatted)


class PaymentSerializerTests(TestCase):
    """Testes para os serializers de pagamento"""
    
    def setUp(self):
        """Configura dados de teste"""
        # Criar usuários
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        # Criar barbearia
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        # Criar serviço
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        # Criar customer relationship
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
    
    def test_payment_create_serializer_valid(self):
        """Testa criação de pagamento com dados válidos"""
        data = {
            'appointment': self.appointment.id,
            'amount': '30.00',
            'method': Payment.Method.PIX,
            'notes': 'Test payment'
        }
        
        serializer = PaymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        payment = serializer.save()
        self.assertEqual(payment.appointment, self.appointment)
        self.assertEqual(payment.amount, Decimal('30.00'))
    
    def test_payment_create_serializer_invalid_amount(self):
        """Testa validação de valor inválido"""
        data = {
            'appointment': self.appointment.id,
            'amount': '0.00',
            'method': Payment.Method.PIX
        }
        
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_payment_create_serializer_duplicate_appointment(self):
        """Testa validação de agendamento duplicado"""
        # Criar primeiro pagamento
        Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX
        )
        
        # Tentar criar segundo pagamento para mesmo agendamento
        data = {
            'appointment': self.appointment.id,
            'amount': '30.00',
            'method': Payment.Method.PIX
        }
        
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('appointment', serializer.errors)


class PaymentViewSetTests(APITestCase):
    """Testes para o ViewSet de pagamentos"""
    
    def setUp(self):
        """Configura dados de teste"""
        # Criar usuários
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        # Criar barbearia
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        # Criar serviço
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        # Criar customer relationship
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        # Criar pagamento
        self.payment = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PENDING
        )
        
        self.client = APIClient()
    
    def test_list_payments_as_client(self):
        """Testa listagem de pagamentos como cliente"""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/v1/payments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_list_payments_unauthenticated(self):
        """Testa listagem de pagamentos sem autenticação"""
        response = self.client.get('/api/v1/payments/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_payment_as_owner(self):
        """Testa criação de pagamento como dono da barbearia"""
        # Criar novo agendamento
        appointment2 = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=2),
            end_datetime=timezone.now() + timedelta(hours=2, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        self.client.force_authenticate(user=self.owner_user)
        data = {
            'appointment': appointment2.id,
            'amount': '30.00',
            'method': Payment.Method.PIX,
            'notes': 'Test payment'
        }
        
        response = self.client.post('/api/v1/payments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.filter(appointment=appointment2).count(), 1)
    
    def test_confirm_payment(self):
        """Testa confirmação de pagamento"""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.patch(f'/api/v1/payments/{self.payment.id}/confirm/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertTrue(self.payment.is_paid())
    
    def test_refund_payment(self):
        """Testa reembolso de pagamento"""
        # Marcar como pago primeiro
        self.payment.mark_as_paid()
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.patch(f'/api/v1/payments/{self.payment.id}/refund/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertTrue(self.payment.is_refunded())
    
    def test_my_payments_action(self):
        """Testa ação my-payments"""
        self.client.force_authenticate(user=self.client_user)
        
        response = self.client.get('/api/v1/payments/my_payments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_statistics_action(self):
        """Testa ação statistics"""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/v1/payments/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_payments', response.data)
        self.assertIn('total_revenue', response.data)


class PaymentUtilsTests(TestCase):
    """Testes para as funções utilitárias"""
    
    def setUp(self):
        """Configura dados de teste"""
        # Criar usuários
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        # Criar barbearia
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        # Criar serviço
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        # Criar customer relationship
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
    
    def test_validate_payment_creation_valid(self):
        """Testa validação de criação de pagamento válida"""
        is_valid, message = validate_payment_creation(self.appointment)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
    
    def test_validate_payment_creation_duplicate(self):
        """Testa validação com agendamento já tendo pagamento"""
        # Criar pagamento existente
        Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX
        )
        
        is_valid, message = validate_payment_creation(self.appointment)
        
        self.assertFalse(is_valid)
        self.assertIn("já possui um pagamento", message)
    
    def test_create_payment_from_appointment(self):
        """Testa criação de pagamento a partir de agendamento"""
        payment, error = create_payment_from_appointment(
            self.appointment,
            method=Payment.Method.PIX,
            notes="Test payment"
        )
        
        self.assertIsNotNone(payment)
        self.assertEqual(error, "")
        self.assertEqual(payment.appointment, self.appointment)
        self.assertEqual(payment.amount, self.appointment.final_price)
    
    def test_calculate_payment_statistics(self):
        """Testa cálculo de estatísticas de pagamentos"""
        # Criar alguns pagamentos
        payment1 = Payment.objects.create(
            appointment=self.appointment,
            amount=Decimal('30.00'),
            method=Payment.Method.PIX,
            status=Payment.Status.PAID
        )
        
        stats = calculate_payment_statistics()
        
        self.assertIn('total_payments', stats)
        self.assertIn('total_revenue', stats)
        self.assertIn('paid_count', stats)
        self.assertGreater(stats['total_payments'], 0)
