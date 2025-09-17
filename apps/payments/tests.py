from django.urls import reverse
from rest_framework import status
from apps.utils.test_utils import BaseAPITestCase
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Payment
from apps.barbershops.models import BarbershopCustomer
from apps.appointments.models import Appointment

class PaymentTests(BaseAPITestCase):
    """
    Test suite for payment endpoints.
    """
    def setUp(self):
        super().setUp()
        self.payments_url = '/api/v1/payments/'
        self.summary_url = '/api/v1/payments/summary/'

    def test_list_payments_as_owner(self):
        """Test barbershop owner can list payments."""
        self.authenticate_as(self.owner)
        response = self.client.get(self.payments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_payments_as_client(self):
        """Test client can only see their own payments."""
        self.authenticate_as(self.client_user)
        response = self.client.get(self.payments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['appointment_details']['customer'],
            self.client_user.id
        )

    def test_create_payment_as_owner(self):
        """Test owner can create payment."""
        # Create a new client user for this test
        new_client = self._create_user(
            username='test_client2',
            password='testpass123',
            role='CLIENT',
            email='client2@test.com'
        )
        
        # Create barbershop customer for the new client
        new_customer = BarbershopCustomer.objects.create(
            customer=new_client,
            barbershop=self.barbershop
        )
        
        # Create a new appointment using the customer relationship
        # Modify _create_appointment to use the new customer
        new_appointment = Appointment.objects.create(
            customer=new_customer,
            barber=self.barber,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, minutes=30),
            status='CONFIRMED'
        )
        
        self.authenticate_as(self.owner)
        data = {
            'appointment': new_appointment.id,
            'amount': self.service.price,
            'method': 'PIX',
            'status': 'PAID'
        }
        response = self.client.post(self.payments_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 2)

    def test_create_payment_as_non_owner(self):
        """Test non-owner cannot create payment."""
        self.authenticate_as(self.client_user)
        data = {
            'appointment': self.appointment.id,
            'amount': self.service.price,
            'method': 'PIX',
            'status': 'PAID'
        }
        response = self.client.post(self.payments_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_payment_as_owner(self):
        """Test owner can update payment."""
        self.authenticate_as(self.owner)
        url = reverse('payments:payment-detail', args=[self.payment.id])
        data = {'status': 'REFUNDED'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Payment.objects.get(id=self.payment.id).status,
            'REFUNDED'
        )

    def test_payment_summary_cached(self):
        """Test payment summary is cached."""
        self.authenticate_as(self.owner)
        
        # First request - cache miss
        response1 = self.client.get(self.summary_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        initial_summary = response1.data

        # Create new client user, barbershop customer and appointment
        new_client = self._create_user(
            username='test_client3',
            password='testpass123',
            role='CLIENT',
            email='client3@test.com'
        )
        new_customer = BarbershopCustomer.objects.create(
            customer=new_client,
            barbershop=self.barbershop
        )
        new_appointment = Appointment.objects.create(
            customer=new_customer,
            barber=self.barber,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, minutes=30),
            status='CONFIRMED'
        )
        Payment.objects.create(
            appointment=new_appointment,
            amount=50.00,
            method='CARD',
            status='PAID'
        )
        
        # Second request - should get cached response
        response2 = self.client.get(self.summary_url)
        self.assertEqual(response2.data, initial_summary)

        # Clear cache and verify the new data is reflected
        cache.clear()
        response3 = self.client.get(self.summary_url)
        self.assertNotEqual(response3.data, initial_summary)
        self.assertGreater(
            response3.data['monthly_total'],
            initial_summary['monthly_total']
        )

    def test_payment_summary_permissions(self):
        """Test only owners can access payment summary."""
        # Test as non-owner
        self.authenticate_as(self.client_user)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as owner
        self.authenticate_as(self.owner)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_method_validation(self):
        """Test payment method validation."""
        self.authenticate_as(self.owner)
        data = {
            'appointment': self.appointment.id,
            'amount': self.service.price,
            'method': 'INVALID_METHOD',  # Invalid payment method
            'status': 'PAID'
        }
        response = self.client.post(self.payments_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
