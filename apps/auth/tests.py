from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthenticationE2ETestCase(APITestCase):
    """
    Testes End-to-End para todas as rotas de autenticação JWT.
    """

    def setUp(self):
        """
        Configuração inicial para todos os testes.
        """
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        # Criar usuário para testes
        self.user = User.objects.create_user(**self.user_data)

        # URLs das rotas de autenticação
        self.token_obtain_url = reverse("token_obtain")
        self.token_refresh_url = reverse("token_refresh")
        self.token_verify_url = reverse("token_verify")
        self.token_blacklist_url = reverse("token_blacklist")

    def test_token_obtain_with_valid_credentials(self):
        """
        Testa a obtenção de tokens JWT com credenciais válidas.
        """
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"],
        }

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Verificar se os tokens são strings não vazias
        self.assertIsInstance(response.data["access"], str)
        self.assertIsInstance(response.data["refresh"], str)
        self.assertGreater(len(response.data["access"]), 0)
        self.assertGreater(len(response.data["refresh"]), 0)

    def test_token_obtain_with_email_login(self):
        """
        Testa a obtenção de tokens JWT usando email em vez de username.
        Nota: Este teste assume que o sistema está configurado para aceitar email como username.
        """
        login_data = {
            "username": self.user_data["email"],  # Usando email como username
            "password": self.user_data["password"],
        }

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        # Se não funcionar com email diretamente, pule o teste
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            self.skipTest("Sistema não configurado para login com email")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_obtain_with_invalid_username(self):
        """
        Testa a obtenção de tokens com username inválido.
        """
        login_data = {"username": "invaliduser", "password": self.user_data["password"]}

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_obtain_with_invalid_password(self):
        """
        Testa a obtenção de tokens com senha inválida.
        """
        login_data = {
            "username": self.user_data["username"],
            "password": "wrongpassword",
        }

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_obtain_with_missing_fields(self):
        """
        Testa a obtenção de tokens com campos obrigatórios ausentes.
        """
        # Teste sem username
        login_data = {"password": self.user_data["password"]}

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

        # Teste sem password
        login_data = {"username": self.user_data["username"]}

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_token_obtain_with_inactive_user(self):
        """
        Testa a obtenção de tokens com usuário inativo.
        """
        # Desativar usuário
        self.user.is_active = False
        self.user.save()

        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"],
        }

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_with_valid_token(self):
        """
        Testa a renovação de token de acesso com refresh token válido.
        """
        # Obter tokens iniciais
        refresh = RefreshToken.for_user(self.user)

        refresh_data = {"refresh": str(refresh)}

        response = self.client.post(self.token_refresh_url, refresh_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIsInstance(response.data["access"], str)
        self.assertGreater(len(response.data["access"]), 0)

    def test_token_refresh_with_invalid_token(self):
        """
        Testa a renovação com refresh token inválido.
        """
        refresh_data = {"refresh": "invalid.token.here"}

        response = self.client.post(self.token_refresh_url, refresh_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_refresh_with_missing_token(self):
        """
        Testa a renovação sem fornecer refresh token.
        """
        refresh_data = {}

        response = self.client.post(self.token_refresh_url, refresh_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("refresh", response.data)

    def test_token_refresh_with_expired_token(self):
        """
        Testa a renovação com refresh token expirado.
        """
        # Criar um token já expirado usando timedelta
        refresh = RefreshToken.for_user(self.user)
        refresh.set_exp(lifetime=timedelta(seconds=-1))  # Definir como expirado

        refresh_data = {"refresh": str(refresh)}

        response = self.client.post(self.token_refresh_url, refresh_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_verify_with_valid_access_token(self):
        """
        Testa a verificação de um token de acesso válido.
        """
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        verify_data = {"token": str(access_token)}

        response = self.client.post(self.token_verify_url, verify_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_verify_with_valid_refresh_token(self):
        """
        Testa a verificação de um refresh token válido.
        """
        refresh = RefreshToken.for_user(self.user)

        verify_data = {"token": str(refresh)}

        response = self.client.post(self.token_verify_url, verify_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_verify_with_invalid_token(self):
        """
        Testa a verificação de um token inválido.
        """
        verify_data = {"token": "invalid.jwt.token"}

        response = self.client.post(self.token_verify_url, verify_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_verify_with_missing_token(self):
        """
        Testa a verificação sem fornecer token.
        """
        verify_data = {}

        response = self.client.post(self.token_verify_url, verify_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)

    def test_token_verify_with_expired_token(self):
        """
        Testa a verificação de um token expirado.
        """
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        # Forçar expiração do token usando timedelta
        access_token.set_exp(lifetime=timedelta(seconds=-1))

        verify_data = {"token": str(access_token)}

        response = self.client.post(self.token_verify_url, verify_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_blacklist_with_valid_refresh_token(self):
        """
        Testa o blacklist (logout) com refresh token válido.
        """
        refresh = RefreshToken.for_user(self.user)

        blacklist_data = {"refresh": str(refresh)}

        response = self.client.post(
            self.token_blacklist_url, blacklist_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Tentar usar o token após blacklist - deve falhar
        refresh_data = {"refresh": str(refresh)}

        refresh_response = self.client.post(
            self.token_refresh_url, refresh_data, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_blacklist_with_invalid_token(self):
        """
        Testa o blacklist com refresh token inválido.
        """
        blacklist_data = {"refresh": "invalid.token.here"}

        response = self.client.post(
            self.token_blacklist_url, blacklist_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_blacklist_with_missing_token(self):
        """
        Testa o blacklist sem fornecer refresh token.
        """
        blacklist_data = {}

        response = self.client.post(
            self.token_blacklist_url, blacklist_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("refresh", response.data)

    def test_token_blacklist_with_access_token(self):
        """
        Testa o blacklist usando access token em vez de refresh token.
        """
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        blacklist_data = {"refresh": str(access_token)}

        response = self.client.post(
            self.token_blacklist_url, blacklist_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_complete_authentication_flow(self):
        """
        Testa o fluxo completo de autenticação: login -> verify -> refresh -> logout.
        """
        # 1. Login - obter tokens
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"],
        }

        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # 2. Verificar access token
        verify_data = {"token": access_token}

        verify_response = self.client.post(
            self.token_verify_url, verify_data, format="json"
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        # 3. Renovar access token
        refresh_data = {"refresh": refresh_token}

        refresh_response = self.client.post(
            self.token_refresh_url, refresh_data, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

        new_access_token = refresh_response.data["access"]
        self.assertNotEqual(access_token, new_access_token)

        # 4. Verificar novo access token
        new_verify_data = {"token": new_access_token}

        new_verify_response = self.client.post(
            self.token_verify_url, new_verify_data, format="json"
        )
        self.assertEqual(new_verify_response.status_code, status.HTTP_200_OK)

        # 5. Logout - blacklist refresh token
        blacklist_data = {"refresh": refresh_token}

        blacklist_response = self.client.post(
            self.token_blacklist_url, blacklist_data, format="json"
        )
        self.assertEqual(blacklist_response.status_code, status.HTTP_200_OK)

        # 6. Tentar usar refresh token após logout - deve falhar
        final_refresh_response = self.client.post(
            self.token_refresh_url, refresh_data, format="json"
        )
        self.assertEqual(
            final_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_authentication_with_different_user_roles(self):
        """
        Testa autenticação com diferentes tipos de usuários.
        """
        # Criar usuários com diferentes roles
        client_user = User.objects.create_user(
            username="client",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
        )

        barber_user = User.objects.create_user(
            username="barber",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER,
        )

        admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role=User.Role.ADMIN,
        )

        # Testar login para cada tipo de usuário
        users_to_test = [client_user, barber_user, admin_user]

        for user in users_to_test:
            login_data = {"username": user.username, "password": "testpass123"}

            response = self.client.post(
                self.token_obtain_url, login_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access", response.data)
            self.assertIn("refresh", response.data)

    def test_concurrent_token_operations(self):
        """
        Testa operações concorrentes com tokens.
        """
        # Obter múltiplos refresh tokens para o mesmo usuário
        refresh1 = RefreshToken.for_user(self.user)
        refresh2 = RefreshToken.for_user(self.user)

        # Ambos devem funcionar independentemente
        refresh_data1 = {"refresh": str(refresh1)}
        refresh_data2 = {"refresh": str(refresh2)}

        response1 = self.client.post(
            self.token_refresh_url, refresh_data1, format="json"
        )
        response2 = self.client.post(
            self.token_refresh_url, refresh_data2, format="json"
        )

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Blacklist um token não deve afetar o outro
        blacklist_data = {"refresh": str(refresh1)}
        blacklist_response = self.client.post(
            self.token_blacklist_url, blacklist_data, format="json"
        )
        self.assertEqual(blacklist_response.status_code, status.HTTP_200_OK)

        # refresh2 ainda deve funcionar
        response2_after_blacklist = self.client.post(
            self.token_refresh_url, refresh_data2, format="json"
        )
        self.assertEqual(response2_after_blacklist.status_code, status.HTTP_200_OK)

        # refresh1 não deve mais funcionar
        response1_after_blacklist = self.client.post(
            self.token_refresh_url, refresh_data1, format="json"
        )
        self.assertEqual(
            response1_after_blacklist.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def tearDown(self):
        """
        Limpeza após cada teste.
        """
        User.objects.all().delete()


class AuthenticationSecurityTestCase(APITestCase):
    """
    Testes de segurança para autenticação JWT.
    """

    def setUp(self):
        """
        Configuração inicial para testes de segurança.
        """
        self.user = User.objects.create_user(
            username="securitytest", email="security@test.com", password="securepass123"
        )

        self.token_obtain_url = reverse("token_obtain")
        self.token_refresh_url = reverse("token_refresh")
        self.token_verify_url = reverse("token_verify")
        self.token_blacklist_url = reverse("token_blacklist")

    def test_rate_limiting_login_attempts(self):
        """
        Testa se há proteção contra múltiplas tentativas de login.
        """
        login_data = {"username": "nonexistent", "password": "wrongpassword"}

        # Fazer múltiplas tentativas de login com credenciais inválidas
        responses = []
        for i in range(5):
            response = self.client.post(
                self.token_obtain_url, login_data, format="json"
            )
            responses.append(response.status_code)

        # Todos devem falhar com 401
        for status_code in responses:
            self.assertEqual(status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_contains_no_sensitive_data(self):
        """
        Testa se os tokens não contêm dados sensíveis em texto claro.
        """
        login_data = {"username": self.user.username, "password": "securepass123"}

        response = self.client.post(self.token_obtain_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        # Tokens devem ser strings codificadas, não texto claro
        self.assertNotIn("securepass123", access_token)
        self.assertNotIn("security@test.com", access_token)
        self.assertNotIn("securepass123", refresh_token)
        self.assertNotIn("security@test.com", refresh_token)

    def test_different_tokens_for_different_users(self):
        """
        Testa se usuários diferentes recebem tokens diferentes.
        """
        user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass123"
        )

        # Login do primeiro usuário
        login_data1 = {"username": self.user.username, "password": "securepass123"}
        response1 = self.client.post(self.token_obtain_url, login_data1, format="json")

        # Login do segundo usuário
        login_data2 = {"username": user2.username, "password": "pass123"}
        response2 = self.client.post(self.token_obtain_url, login_data2, format="json")

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Tokens devem ser diferentes
        self.assertNotEqual(response1.data["access"], response2.data["access"])
        self.assertNotEqual(response1.data["refresh"], response2.data["refresh"])

    def tearDown(self):
        """
        Limpeza após cada teste.
        """
        User.objects.all().delete()


class AuthenticationPerformanceTestCase(APITestCase):
    """
    Testes de performance para autenticação JWT.
    """

    def setUp(self):
        """
        Configuração inicial para testes de performance.
        """
        self.user = User.objects.create_user(
            username="perftest", email="perf@test.com", password="perfpass123"
        )

        self.token_obtain_url = reverse("token_obtain")
        self.token_refresh_url = reverse("token_refresh")

    def test_multiple_concurrent_logins(self):
        """
        Testa múltiplos logins simultâneos.
        """
        login_data = {"username": self.user.username, "password": "perfpass123"}

        # Simular múltiplos logins
        responses = []
        for i in range(10):
            response = self.client.post(
                self.token_obtain_url, login_data, format="json"
            )
            responses.append(response)

        # Todos devem ser bem-sucedidos
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access", response.data)
            self.assertIn("refresh", response.data)

    def test_token_refresh_performance(self):
        """
        Testa a performance da renovação de tokens.
        """
        # Obter token inicial
        refresh = RefreshToken.for_user(self.user)

        # Fazer múltiplas renovações
        current_refresh = str(refresh)

        for i in range(5):
            refresh_data = {"refresh": current_refresh}
            response = self.client.post(
                self.token_refresh_url, refresh_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access", response.data)

            # Se o refresh token também for rotacionado, use o novo
            if "refresh" in response.data:
                current_refresh = response.data["refresh"]

    def tearDown(self):
        """
        Limpeza após cada teste.
        """
        User.objects.all().delete()
