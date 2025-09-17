from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AuthenticationTests(APITestCase):
    """
    Test suite for all authentication endpoints.
    Tests cover token acquisition, refresh, verification and logout functionality.
    """
    def setUp(self):
        """Set up test data and URLs."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='client'
        )
        
        # URLs for authentication endpoints
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.verify_url = reverse('token_verify')
        self.logout_url = reverse('auth_logout')
        
        # Valid credentials
        self.valid_credentials = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        # Invalid credentials
        self.invalid_credentials = {
            'username': 'testuser',
            'password': 'wrongpass'
        }

    def get_tokens(self):
        """Helper method to get valid tokens."""
        response = self.client.post(self.token_url, self.valid_credentials)
        return response.data['access'], response.data['refresh']

    def test_obtain_token_pair_success(self):
        """
        Test successful token pair acquisition with valid credentials.
        Should return access token, refresh token and user info.
        """
        response = self.client.post(self.token_url, self.valid_credentials)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verify user info
        user_data = response.data['user']
        self.assertEqual(user_data['username'], self.user.username)
        self.assertEqual(user_data['email'], self.user.email)
        self.assertEqual(user_data['first_name'], self.user.first_name)
        self.assertEqual(user_data['last_name'], self.user.last_name)
        self.assertEqual(user_data['role'], self.user.role)

    def test_obtain_token_pair_invalid_credentials(self):
        """Test token acquisition fails with invalid credentials."""
        response = self.client.post(self.token_url, self.invalid_credentials)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        """
        Test successful access token refresh using valid refresh token.
        Should return new access token.
        """
        # First get valid tokens
        _, refresh = self.get_tokens()
        
        # Try to refresh
        response = self.client.post(self.refresh_url, {'refresh': refresh})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalid(self):
        """Test token refresh fails with invalid refresh token."""
        response = self.client.post(self.refresh_url, {'refresh': 'invalid-token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_token_success(self):
        """Test successful token verification with valid token."""
        # Get valid tokens
        access, _ = self.get_tokens()
        
        # Verify the access token
        response = self.client.post(self.verify_url, {'token': access})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_token_invalid(self):
        """Test token verification fails with invalid token."""
        response = self.client.post(self.verify_url, {'token': 'invalid-token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        """
        Test successful logout using valid refresh token.
        Should blacklist the refresh token.
        """
        # Get valid tokens
        access, refresh = self.get_tokens()
        
        # Setup access token auth
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        
        # Try to logout
        response = self.client.post(self.logout_url, {'refresh_token': refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify token is blacklisted by trying to use it for refresh
        refresh_response = self.client.post(self.refresh_url, {'refresh': refresh})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_no_token(self):
        """Test logout fails when no refresh token is provided."""
        # Get access token and set authorization
        access, _ = self.get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        
        # Try to logout without refresh token
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_token(self):
        """Test logout fails with invalid refresh token."""
        # Get access token for authorization
        access, _ = self.get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        
        # Try to logout with invalid refresh token
        response = self.client.post(self.logout_url, {'refresh_token': 'invalid-token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh_token', response.data)  # Deve conter mensagem de erro sobre o token

    def test_obtain_token_missing_fields(self):
        """Test token acquisition fails when required fields are missing."""
        response = self.client.post(self.token_url, {'username': 'testuser'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.post(self.token_url, {'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_missing_field(self):
        """Test token refresh fails when refresh token is not provided."""
        response = self.client.post(self.refresh_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_token_missing_field(self):
        """Test token verification fails when token is not provided."""
        response = self.client.post(self.verify_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserManagementTests(APITestCase):
    """Test suite for user management endpoints."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
        # Clean up all users
        User.objects.all().delete()
        
        # Create admin user
        cls.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Create normal user
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='client'
        )
        
        # Create another user for testing list/bulk operations
        cls.another_user = User.objects.create_user(
            username='another',
            email='another@example.com',
            password='anotherpass123',
            first_name='Another',
            last_name='User',
            role='client'
        )
        
    def setUp(self):
        """Set up test-specific data"""
        # URLs
        self.users_url = reverse('users:user-list')
        self.user_detail_url = reverse('users:user-detail', kwargs={'pk': self.user.pk})
        self.change_password_url = reverse('users:user-change-password', kwargs={'pk': self.user.pk})
        
        # Valid data for testing
        self.valid_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'CLIENT'  # Usar o valor correto do enum
        }
        
        self.valid_update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        
        self.valid_password_data = {
            'old_password': 'testpass123',
            'new_password': 'newtestpass123'
        }

    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user."""
        self.client.force_authenticate(user=user)

    def test_list_users_as_admin(self):
        """Test admin can list all users."""
        self.authenticate_as(self.admin)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), User.objects.count())

    def test_list_users_as_non_admin(self):
        """Test non-admin cannot list all users."""
        self.authenticate_as(self.user)
        response = self.client.get(self.users_url)
        
    def test_create_user_success(self):
        """Test successful user creation."""
        # Authenticate as admin if required for user creation
        self.authenticate_as(self.admin)
        response = self.client.post(self.users_url, self.valid_user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], self.valid_user_data['username'])
        self.assertEqual(response.data['email'], self.valid_user_data['email'])
        self.assertEqual(response.data['first_name'], self.valid_user_data['first_name'])
        self.assertEqual(response.data['email'], self.valid_user_data['email'])
        self.assertEqual(response.data['first_name'], self.valid_user_data['first_name'])

    def test_create_user_invalid_data(self):
        """Test user creation fails with invalid data."""
        invalid_data = self.valid_user_data.copy()
        invalid_data.pop('username')  # Username is required
        
        response = self.client.post(self.users_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_as_owner(self):
        """Test user can retrieve their own details."""
        self.authenticate_as(self.user)
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_retrieve_user_as_admin(self):
        """Test admin can retrieve any user's details."""
        self.authenticate_as(self.admin)
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_retrieve_user_as_other(self):
        """Test user cannot retrieve other user's details."""
        self.authenticate_as(self.another_user)
        response = self.client.get(self.user_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_as_owner(self):
        """Test user can update their own details."""
        self.authenticate_as(self.user)
        response = self.client.patch(
            self.user_detail_url,
            self.valid_update_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], self.valid_update_data['first_name'])
        self.assertEqual(response.data['email'], self.valid_update_data['email'])

    def test_partial_update_user_as_owner(self):
        """Test user can partially update their own details."""
        self.authenticate_as(self.user)
        response = self.client.patch(
            self.user_detail_url,
            {'first_name': 'NewName'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'NewName')

    def test_delete_user_as_owner(self):
        """Test user can delete their own account."""
        self.authenticate_as(self.user)
        response = self.client.delete(self.user_detail_url)

    def test_bulk_delete_as_admin(self):
        """Test admin can bulk delete users."""
        self.authenticate_as(self.admin)
        
        # Pegar contagem inicial (3 usuários do setup)
        initial_count = User.objects.count()
        
        # Criar usuários específicos para o teste
        test_user1 = User.objects.create_user(
            username='testdelete1',
            email='testdelete1@example.com',
            password='testpass123',
            role='CLIENT'
        )
        test_user2 = User.objects.create_user(
            username='testdelete2',
            email='testdelete2@example.com',
            password='testpass123',
            role='CLIENT'
        )
        
        # Verificar se os usuários foram criados
        self.assertEqual(User.objects.count(), initial_count + 2)
        
        # Tentar deletar os usuários de teste
        user_ids = [test_user1.id, test_user2.id]
        response = self.client.post(
            reverse('users:user-bulk-delete'),
            {'ids': user_ids},
            format='json'
        )
        
        # Verificar resposta e deleção
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), initial_count)  # Deve voltar à contagem inicial
        self.assertFalse(User.objects.filter(id__in=user_ids).exists())

    def test_bulk_delete_as_non_admin(self):
        """Test non-admin cannot bulk delete users."""
        self.authenticate_as(self.user)
        user_ids = [self.user.id, self.another_user.id]
        response = self.client.post(reverse('users:user-bulk-delete'), {'ids': user_ids})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password_success(self):
        """Test successful password change."""
        self.authenticate_as(self.user)
        response = self.client.post(self.change_password_url, self.valid_password_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify can login with new password
        self.client.logout()
        login_response = self.client.post(reverse('token_obtain_pair'), {
            'username': self.user.username,
            'password': self.valid_password_data['new_password']
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_old_password(self):
        """Test password change fails with wrong old password."""
        self.authenticate_as(self.user)
        invalid_data = {
            'old_password': 'wrongpass',
            'new_password': 'newtestpass123'
        }
        response = self.client.post(self.change_password_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_as_other_user(self):
        """Test user cannot change another user's password."""
        self.authenticate_as(self.another_user)
        response = self.client.post(self.change_password_url, self.valid_password_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)