from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import Appointment, BarberSchedule
from apps.barbershops.models import Barbershop, Service, BarbershopCustomer, Barber

User = get_user_model()

class TestMixin:
    """Mixin class with common test utilities."""
    
    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def _create_user(self, **kwargs):
        """Helper method to create a user."""
        return User.objects.create_user(**kwargs)

class AppointmentAPITests(APITestCase, TestMixin):
    """Test suite for appointment endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.owner = self._create_user(
            username='owner',
            password='testpass123',
            email='owner@test.com',
            role='OWNER',
            first_name='Test Owner',
            last_name='User',
            phone='1234567890'
        )
        
        self.barber = self._create_user(
            username='barber',
            password='testpass123',
            email='barber@test.com',
            role='BARBER',
            first_name='Test Barber',
            last_name='User',
            phone='1234567891'
        )
        
        self.client_user = self._create_user(
            username='client',
            password='testpass123',
            email='client@test.com',
            role='CLIENT',
            first_name='Test Client',
            last_name='User',
            phone='1234567892'
        )
        
        # Create barbershop
        self.barbershop = Barbershop.objects.create(
            name='Test Barbershop',
            owner=self.owner,
            address='123 Test St',
            phone='1234567890',
            description='Test barbershop description'
        )
        
        # Create barber profile
        self.barber_profile = Barber.objects.create(
            user=self.barber,
            specialties='Haircuts, Beard Trimming',
            experience_years=5
        )
        
        # Create service
        self.service = Service.objects.create(
            barbershop=self.barbershop,
            name='Test Haircut',
            description='Test haircut service',
            price=30.00,
            duration=30
        )
        
        # Create customer
        self.barbershop_customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Set up test datetime with timezone awareness
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.tomorrow = self.tomorrow.replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        
        # Create test barber schedule
        self.schedule = BarberSchedule.objects.create(
            barber=self.barber,
            barbershop=self.barbershop,
            weekday=self.tomorrow.weekday(),
            start_time='09:00',
            end_time='17:00',
            is_available=True
        )
        
        # Create test appointment with timezone-aware datetimes
        self.appointment = Appointment.objects.create(
            customer=self.barbershop_customer,
            barber=self.barber,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.make_aware(self.tomorrow),
            end_datetime=timezone.make_aware(self.tomorrow + timedelta(minutes=30)),
            status='PENDING'
        )
        
        # Set up URLs
        self.appointments_url = reverse('appointments:appointment-list')
        self.appointment_detail_url = reverse(
            'appointments:appointment-detail',
            args=[self.appointment.id]
        )
        self.upcoming_url = reverse('appointments:appointment-upcoming')
        self.available_slots_url = reverse('appointments:appointment-available-slots')

    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def test_list_appointments_as_client(self):
        """Test client can only see their own appointments."""
        self.authenticate_as(self.client_user)
        response = self.client.get(self.appointments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_list_appointments_as_barber(self):
        """Test barber can see their assigned appointments."""
        self.authenticate_as(self.barber)
        response = self.client.get(self.appointments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_list_appointments_as_owner(self):
        """Test owner can see all appointments in their barbershop."""
        self.authenticate_as(self.owner)
        response = self.client.get(self.appointments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_create_appointment_as_client(self):
        """Test client can create an appointment."""
        self.authenticate_as(self.client_user)
        data = {
            'barber': self.barber.id,
            'service': self.service.id,
            'barbershop': self.barbershop.id,
            'start_datetime': (self.tomorrow + timedelta(days=1)).isoformat(),
            'end_datetime': (self.tomorrow + timedelta(days=1, minutes=30)).isoformat(),
        }
        response = self.client.post(self.appointments_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 2)

    def test_create_appointment_as_non_client(self):
        """Test non-clients cannot create appointments."""
        self.authenticate_as(self.barber)
        data = {
            'barber': self.barber.id,
            'service': self.service.id,
            'barbershop': self.barbershop.id,
            'start_datetime': (self.tomorrow + timedelta(days=1)).isoformat(),
            'end_datetime': (self.tomorrow + timedelta(days=1, minutes=30)).isoformat(),
        }
        response = self.client.post(self.appointments_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_update_appointment_status_as_barber(self):
        """Test barber can update appointment status."""
        self.authenticate_as(self.barber)
        data = {'status': 'COMPLETED'}
        response = self.client.patch(self.appointment_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Appointment.objects.get(id=self.appointment.id).status,
            'COMPLETED'
        )

    def test_cancel_appointment_as_client(self):
        """Test client can cancel their appointment."""
        self.authenticate_as(self.client_user)
        data = {'status': 'CANCELLED'}
        response = self.client.patch(self.appointment_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Appointment.objects.get(id=self.appointment.id).status,
            'CANCELLED'
        )

    def test_list_upcoming_appointments(self):
        """Test listing upcoming appointments."""
        self.authenticate_as(self.client_user)
        response = self.client.get(self.upcoming_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_available_slots(self):
        """Test getting available appointment slots."""
        self.authenticate_as(self.client_user)
        params = {
            'date': self.tomorrow.date().isoformat(),
            'barber': self.barber.id,
            'barbershop': self.barbershop.id
        }
        response = self.client.get(self.available_slots_url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, list))


class BarberScheduleAPITests(APITestCase):
    """Test suite for barber schedule endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123',
            email='owner@test.com',
            role='OWNER',
            first_name='Test Owner',
            last_name='User',
            phone='1234567890'
        )
        
        self.barber = User.objects.create_user(
            username='barber',
            password='testpass123',
            email='barber@test.com',
            role='BARBER',
            first_name='Test Barber',
            last_name='User',
            phone='1234567891'
        )
        
        self.client_user = User.objects.create_user(
            username='client',
            password='testpass123',
            email='client@test.com',
            role='CLIENT',
            first_name='Test Client',
            last_name='User',
            phone='1234567892'
        )
        
        # Create barbershop
        self.barbershop = Barbershop.objects.create(
            name='Test Barbershop',
            owner=self.owner,
            address='123 Test St',
            phone='1234567890',
            description='Test barbershop description'
        )
        
        # Create barber profile
        self.barber_profile = Barber.objects.create(
            user=self.barber,
            specialties='Haircuts, Beard Trimming',
            experience_years=5
        )
        
        # Set up URLs
        self.schedules_url = reverse('appointments:barberschedule-list')
        
        # Create test schedule for Tuesday (weekday=1)
        self.schedule = BarberSchedule.objects.create(
            barber=self.barber,
            barbershop=self.barbershop,
            weekday=1,  # Tuesday
            start_time='09:00',
            end_time='17:00',
            is_available=True
        )
        
        # Set up detail URL
        self.schedule_detail_url = reverse(
            'appointments:barberschedule-detail',
            args=[self.schedule.id]
        )

    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def test_list_schedules(self):
        """Test anyone can list barber schedules."""
        response = self.client.get(self.schedules_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_schedule_as_barber(self):
        """Test barber can create their schedule."""
        self.authenticate_as(self.barber)
        data = {
            'barbershop': self.barbershop.id,
            'weekday': 2,  # Wednesday
            'start_time': '09:00',
            'end_time': '17:00',
            'is_available': True
        }
        response = self.client.post(self.schedules_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BarberSchedule.objects.count(), 2)

    def test_create_schedule_as_non_barber(self):
        """Test non-barber cannot create schedule."""
        self.authenticate_as(self.client_user)
        data = {
            'barbershop': self.barbershop.id,
            'weekday': 2,  # Wednesday
            'start_time': '09:00',
            'end_time': '17:00',
            'is_available': True
        }
        response = self.client.post(self.schedules_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(BarberSchedule.objects.count(), 1)

    def test_update_own_schedule(self):
        """Test barber can update their own schedule."""
        self.authenticate_as(self.barber)
        data = {'is_available': False}
        response = self.client.patch(self.schedule_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            BarberSchedule.objects.get(id=self.schedule.id).is_available,
            False
        )

    def test_update_other_schedule(self):
        """Test barber cannot update other's schedule."""
        other_barber = User.objects.create_user(
            username='other_barber',
            password='testpass123',
            email='other@test.com',
            role='BARBER',
            first_name='Other',
            last_name='Barber'
        )
        self.authenticate_as(other_barber)
        data = {'is_available': False}
        response = self.client.patch(self.schedule_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(BarberSchedule.objects.get(id=self.schedule.id).is_available)

    def test_owner_can_manage_schedules(self):
        """Test barbershop owner can manage all schedules."""
        self.authenticate_as(self.owner)
        data = {'is_available': False}
        response = self.client.patch(self.schedule_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            BarberSchedule.objects.get(id=self.schedule.id).is_available,
            False
        )

    def test_delete_schedule_as_barber(self):
        """Test barber can delete their schedule."""
        self.authenticate_as(self.barber)
        response = self.client.delete(self.schedule_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BarberSchedule.objects.count(), 0)

    def test_delete_schedule_as_non_barber(self):
        """Test non-barbers cannot delete schedules."""
        self.authenticate_as(self.client_user)
        response = self.client.delete(self.schedule_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(BarberSchedule.objects.count(), 1)
    """
    Test suite for appointment endpoints.
    """
    def setUp(self):
        super().setUp()
        
        # Set up URLs using reverse for better maintainability
        self.appointments_url = reverse('appointments:appointment-list')
        self.upcoming_url = reverse('appointments:appointment-upcoming')
        self.available_slots_url = reverse('appointments:appointment-available-slots')
        
        # Set up test datetime
        self.tomorrow = timezone.now() + timedelta(days=1)
        self.tomorrow = self.tomorrow.replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        
        # Create test appointment
        self.appointment = Appointment.objects.create(
            customer=self.barbershop_customer,
            barber=self.barber,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=self.tomorrow,
            end_datetime=self.tomorrow + timedelta(minutes=30),
            status='PENDING'
        )
        
        # Set up detail URL
        self.appointment_detail_url = reverse(
            'appointments:appointment-detail',
            args=[self.appointment.id]
        )

    def test_list_appointments_as_client(self):
        """Test client can only see their own appointments."""
        self.authenticate_as(self.client_user)
        response = self.client.get(self.appointments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_appointment_as_client(self):
        """Test client can create an appointment."""
        self.authenticate_as(self.client_user)
        data = {
            'barber': self.barber.id,
            'service': self.service.id,
            'barbershop': self.barbershop.id,
            'start_datetime': self.tomorrow.isoformat(),
            'end_datetime': (self.tomorrow + timedelta(minutes=30)).isoformat(),
        }
        response = self.client.post(self.appointments_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 2)

    def test_create_conflicting_appointment(self):
        """Test cannot create overlapping appointments."""
        self.authenticate_as(self.client_user)
        # Create first appointment
        data1 = {
            'barber': self.barber.id,
            'service': self.service.id,
            'barbershop': self.barbershop.id,
            'start_datetime': self.tomorrow.isoformat(),
            'end_datetime': (self.tomorrow + timedelta(minutes=30)).isoformat(),
        }
        self.client.post(self.appointments_url, data1)
        
        # Try to create overlapping appointment
        data2 = {
            'barber': self.barber.id,
            'service': self.service.id,
            'barbershop': self.barbershop.id,
            'start_datetime': (self.tomorrow + timedelta(minutes=15)).isoformat(),
            'end_datetime': (self.tomorrow + timedelta(minutes=45)).isoformat(),
        }
        response = self.client.post(self.appointments_url, data2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_appointment_status_as_barber(self):
        """Test barber can update appointment status."""
        self.authenticate_as(self.barber)
        url = reverse('appointments:appointment-detail', args=[self.appointment.id])
        data = {'status': 'COMPLETED'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Appointment.objects.get(id=self.appointment.id).status,
            'COMPLETED'
        )

    def test_cancel_appointment_as_client(self):
        """Test client can cancel their appointment."""
        self.authenticate_as(self.client_user)
        url = reverse('appointments:appointment-detail', args=[self.appointment.id])
        data = {'status': 'CANCELLED'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Appointment.objects.get(id=self.appointment.id).status,
            'CANCELLED'
        )

    def test_update_other_client_appointment(self):
        """Test client cannot update other's appointment."""
        other_client = self._create_user(
            username='other_client',
            password='testpass123',
            role='CLIENT',
            email='other@test.com'
        )
        self.authenticate_as(other_client)
        data = {'status': 'CANCELLED'}
        response = self.client.patch(self.appointment_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_appointments_as_barber(self):
        """Test barber can see their assigned appointments."""
        self.authenticate_as(self.barber)
        response = self.client.get(self.appointments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_list_appointments_as_owner(self):
        """Test owner can see all appointments in their barbershop."""
        self.authenticate_as(self.owner)
        response = self.client.get(self.appointments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.appointment.id)

    def test_list_upcoming_appointments(self):
        """Test listing upcoming appointments."""
        self.authenticate_as(self.client_user)
        response = self.client.get(self.upcoming_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_available_slots(self):
        """Test getting available appointment slots."""
        self.authenticate_as(self.client_user)
        params = {
            'date': self.tomorrow.date().isoformat(),
            'barber': self.barber.id,
            'barbershop': self.barbershop.id
        }
        response = self.client.get(self.available_slots_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, list))

    def test_delete_appointment_as_barber(self):
        """Test barber can delete/cancel appointment."""
        self.authenticate_as(self.barber)
        response = self.client.delete(self.appointment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_delete_appointment_as_client(self):
        """Test client cannot delete appointment."""
        self.authenticate_as(self.client_user)
        response = self.client.delete(self.appointment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_retrieve_appointment_as_client(self):
        """Test client can retrieve their own appointment."""
        self.authenticate_as(self.client_user)
        response = self.client.get(self.appointment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.appointment.id)

    def test_retrieve_appointment_as_barber(self):
        """Test barber can retrieve appointments assigned to them."""
        self.authenticate_as(self.barber)
        response = self.client.get(self.appointment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.appointment.id)

class BarberScheduleAPITests(APITestCase, TestMixin):
    """Test suite for barber schedule endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.owner = self._create_user(
            username='owner',
            password='testpass123',
            email='owner@test.com',
            role='OWNER',
            first_name='Test Owner',
            last_name='User',
            phone='1234567890'
        )
        
        self.barber = self._create_user(
            username='barber',
            password='testpass123',
            email='barber@test.com',
            role='BARBER',
            first_name='Test Barber',
            last_name='User',
            phone='1234567891'
        )
        
        self.client_user = self._create_user(
            username='client',
            password='testpass123',
            email='client@test.com',
            role='CLIENT',
            first_name='Test Client',
            last_name='User',
            phone='1234567892'
        )
        
        # Create barbershop
        self.barbershop = Barbershop.objects.create(
            name='Test Barbershop',
            owner=self.owner,
            address='123 Test St',
            phone='1234567890',
            description='Test barbershop description'
        )
        
        # Create barber profile
        self.barber_profile = Barber.objects.create(
            user=self.barber,
            specialties='Haircuts, Beard Trimming',
            experience_years=5
        )
        
        # Set up URLs
        self.schedules_url = reverse('appointments:barberschedule-list')
        
        # Create test schedule
        self.schedule = BarberSchedule.objects.create(
            barber=self.barber,
            barbershop=self.barbershop,
            weekday=1,  # Monday
            start_time='09:00',
            end_time='17:00',
            is_available=True
        )
        
        # Set up detail URL
        self.schedule_detail_url = reverse(
            'appointments:barberschedule-detail',
            args=[self.schedule.id]
        )

    def test_list_schedules(self):
        """Test anyone can list barber schedules."""
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_schedule_as_barber(self):
        """Test barber can create their schedule."""
        self.authenticate_as(self.barber)
        data = {
            'barbershop': self.barbershop.id,
            'weekday': 2,  # Tuesday
            'start_time': '09:00',
            'end_time': '17:00',
            'is_available': True
        }
        response = self.client.post(self.schedules_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BarberSchedule.objects.count(), 2)

    def test_create_schedule_as_non_barber(self):
        """Test non-barber cannot create schedule."""
        self.authenticate_as(self.client_user)
        data = {
            'barbershop': self.barbershop.id,
            'weekday': 2,
            'start_time': '09:00',
            'end_time': '17:00',
            'is_available': True
        }
        response = self.client.post(self.schedules_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_schedule(self):
        """Test barber can update their own schedule."""
        self.authenticate_as(self.barber)
        data = {'is_available': False}
        response = self.client.patch(self.schedule_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            BarberSchedule.objects.get(id=self.schedule.id).is_available,
            False
        )

    def test_update_other_schedule(self):
        """Test barber cannot update other's schedule."""
        other_barber = self._create_user(
            username='other_barber',
            password='testpass123',
            role='BARBER',
            email='other@test.com'
        )
        self.authenticate_as(other_barber)
        data = {'is_available': False}
        response = self.client.patch(self.schedule_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(BarberSchedule.objects.get(id=self.schedule.id).is_available)

    def test_owner_can_manage_schedules(self):
        """Test barbershop owner can manage all schedules."""
        self.authenticate_as(self.owner)
        data = {'is_available': False}
        response = self.client.patch(self.schedule_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            BarberSchedule.objects.get(id=self.schedule.id).is_available,
            False
        )

    def test_overlapping_schedules(self):
        """Test cannot create overlapping schedules for same barber and weekday."""
        self.authenticate_as(self.barber)
        data = {
            'barbershop': self.barbershop.id,
            'weekday': 1,  # Monday (same as existing)
            'start_time': '08:00',
            'end_time': '16:00',
            'is_available': True
        }
        response = self.client.post(self.schedules_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(BarberSchedule.objects.count(), 1)

    def test_invalid_time_range(self):
        """Test cannot create schedule with end time before start time."""
        self.authenticate_as(self.barber)
        data = {
            'barbershop': self.barbershop.id,
            'weekday': 2,
            'start_time': '17:00',
            'end_time': '09:00',
            'is_available': True
        }
        response = self.client.post(self.schedules_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(BarberSchedule.objects.count(), 1)

    def test_delete_schedule_as_barber(self):
        """Test barber can delete their schedule."""
        self.authenticate_as(self.barber)
        response = self.client.delete(self.schedule_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BarberSchedule.objects.count(), 0)

    def test_delete_schedule_as_non_barber(self):
        """Test non-barbers cannot delete schedules."""
        self.authenticate_as(self.client_user)
        response = self.client.delete(self.schedule_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(BarberSchedule.objects.count(), 1)
