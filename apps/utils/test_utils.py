from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.barbershops.models import Barbershop, Service, Barber, BarbershopCustomer
from apps.appointments.models import Appointment, BarberSchedule
from apps.payments.models import Payment
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache

User = get_user_model()

class BaseAPITestCase(APITestCase):
    """
    Base test class with common setup and utility methods.
    """
    def setUp(self):
        # Clear cache before each test
        cache.clear()
        
        # Create test users with different roles
        self.owner = self._create_user(
            username='owner',
            password='testpass123',
            role='OWNER',
            email='owner@test.com'
        )
        self.barber = self._create_user(
            username='barber',
            password='testpass123',
            role='BARBER',
            email='barber@test.com'
        )
        self.client_user = self._create_user(
            username='client',
            password='testpass123',
            role='CLIENT',
            email='client@test.com'
        )
        
        # Create test barbershop
        self.barbershop = self._create_barbershop()
        
        # Create test service
        self.service = self._create_service()
        
        # Create barber profile
        self.barber_profile = self._create_barber_profile()
        
        # Create barber schedule
        self.schedule = self._create_barber_schedule()
        
        # Create barbershop customer
        self.customer = self._create_barbershop_customer()
        
        # Create test appointment
        self.appointment = self._create_appointment()
        
        # Create test payment
        self.payment = self._create_payment()

    def _create_user(self, username, password, role, email):
        """Create a test user with given role."""
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            first_name=f'Test {role.title()}',
            last_name='User',
            phone='1234567890'
        )
        return user

    def _create_barbershop(self):
        """Create a test barbershop."""
        return Barbershop.objects.create(
            name='Test Barbershop',
            owner=self.owner,
            address='123 Test St',
            phone='1234567890',
            description='Test barbershop description'
        )

    def _create_service(self):
        """Create a test service."""
        return Service.objects.create(
            barbershop=self.barbershop,
            name='Test Haircut',
            description='Test haircut service',
            price=30.00,
            duration=30
        )

    def _create_barber_profile(self):
        """Create a test barber profile."""
        barber = Barber.objects.create(
            user=self.barber,
            specialties='Haircuts, Beard Trimming',
            experience_years=5
        )
        barber.barbershops.add(self.barbershop)
        return barber

    def _create_barber_schedule(self):
        """Create a test barber schedule."""
        return BarberSchedule.objects.create(
            barber=self.barber,
            barbershop=self.barbershop,
            weekday=1,  # Monday
            start_time='09:00',
            end_time='17:00',
            is_available=True
        )

    def _create_barbershop_customer(self):
        """Create a barbershop customer for testing."""
        return BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )

    def _create_appointment(self):
        """Create a test appointment."""
        return Appointment.objects.create(
            customer=self.customer,
            barber=self.barber,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, minutes=30),
            status='CONFIRMED'
        )

    def _create_payment(self):
        """Create a test payment."""
        return Payment.objects.create(
            appointment=self.appointment,
            amount=self.service.price,
            method='PIX',
            status='PAID',
            payment_date=timezone.now()
        )

    def authenticate_as(self, user):
        """Authenticate as the given user."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )

    def remove_authentication(self):
        """Remove authentication credentials."""
        self.client.credentials()