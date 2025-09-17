from django.urls import reverse
from rest_framework import status
from apps.utils.test_utils import BaseAPITestCase
from django.core.cache import cache
from .models import Barbershop, Service, Barber

class BarbershopTests(BaseAPITestCase):
    """
    Test suite for barbershop endpoints.
    """
    def setUp(self):
        super().setUp()
        self.barbershops_url = '/api/v1/barbershops/'

    def test_list_barbershops_no_auth(self):
        """Test anyone can list barbershops without authentication."""
        response = self.client.get(self.barbershops_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_barbershop_as_owner(self):
        """Test owner can create a barbershop."""
        self.authenticate_as(self.owner)
        data = {
            'name': 'New Barbershop',
            'address': '456 Shop St',
            'phone': '9876543210',
            'description': 'New test barbershop'
        }
        response = self.client.post(self.barbershops_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Barbershop.objects.count(), 2)

    def test_create_barbershop_as_non_owner(self):
        """Test non-owners cannot create barbershops."""
        self.authenticate_as(self.client_user)
        data = {
            'name': 'New Barbershop',
            'address': '456 Shop St',
            'phone': '9876543210',
            'description': 'New test barbershop'
        }
        response = self.client.post(self.barbershops_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_barbershop(self):
        """Test owner can update their own barbershop."""
        self.authenticate_as(self.owner)
        url = reverse('barbershops:barbershop-detail', args=[self.barbershop.id])
        data = {'name': 'Updated Barbershop'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Barbershop.objects.get(id=self.barbershop.id).name,
            'Updated Barbershop'
        )

    def test_update_other_barbershop(self):
        """Test owner cannot update other's barbershop."""
        other_owner = self._create_user(
            username='other_owner',
            password='testpass123',
            role='OWNER',
            email='other@test.com'
        )
        self.authenticate_as(other_owner)
        url = reverse('barbershops:barbershop-detail', args=[self.barbershop.id])
        data = {'name': 'Hacked Barbershop'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_barbershop_statistics_cached(self):
        """Test barbershop statistics are cached."""
        self.authenticate_as(self.owner)
        url = reverse('barbershops:barbershop-statistics', args=[self.barbershop.id])
        
        # First request - cache miss
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        initial_stats = response1.data
        
        # Create new data that would affect statistics
        Service.objects.create(
            barbershop=self.barbershop,
            name='New Service',
            price=50,
            duration=45
        )
        
        # Second request - should get cached response
        response2 = self.client.get(url)
        self.assertEqual(response2.data, initial_stats)

class ServiceTests(BaseAPITestCase):
    """
    Test suite for service endpoints.
    """
    def setUp(self):
        super().setUp()
        self.services_url = '/api/v1/barbershops/services/'

    def test_list_services_no_auth(self):
        """Test anyone can list services without authentication."""
        response = self.client.get(self.services_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_service_as_owner(self):
        """Test owner can create a service."""
        self.authenticate_as(self.owner)
        data = {
            'barbershop': self.barbershop.id,
            'name': 'New Service',
            'description': 'New test service',
            'price': 40.00,
            'duration': 45
        }
        response = self.client.post(self.services_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_service_as_non_owner(self):
        """Test non-owners cannot create services."""
        self.authenticate_as(self.barber)
        data = {
            'barbershop': self.barbershop.id,
            'name': 'New Service',
            'description': 'New test service',
            'price': 40.00,
            'duration': 45
        }
        response = self.client.post(self.services_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class BarberTests(BaseAPITestCase):
    """
    Test suite for barber endpoints.
    """
    def setUp(self):
        super().setUp()
        self.barbers_url = '/api/v1/barbershops/barbers/'

    def test_list_barbers(self):
        """Test listing barbers is public."""
        response = self.client.get(self.barbers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_barber_profile(self):
        """Test barber can create their profile."""
        new_barber = self._create_user(
            username='newbarber',
            password='testpass123',
            role='BARBER',
            email='newbarber@test.com'
        )
        self.authenticate_as(new_barber)
        data = {
            'specialties': 'Haircuts, Coloring',
            'experience_years': 3,
            'barbershops': [self.barbershop.id]
        }
        response = self.client.post(self.barbers_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_own_profile(self):
        """Test barber can update their own profile."""
        self.authenticate_as(self.barber)
        url = reverse('barbershops:barber-detail', args=[self.barber_profile.id])
        data = {'experience_years': 6}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Barber.objects.get(id=self.barber_profile.id).experience_years,
            6
        )

    def test_update_other_profile(self):
        """Test barber cannot update other's profile."""
        other_barber = self._create_user(
            username='other_barber',
            password='testpass123',
            role='BARBER',
            email='other@test.com'
        )
        self.authenticate_as(other_barber)
        url = reverse('barbershops:barber-detail', args=[self.barber_profile.id])
        data = {'experience_years': 1}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
