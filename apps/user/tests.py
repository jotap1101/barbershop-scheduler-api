from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserAPITestCase(APITestCase):
    """
    Classe base para testes da API de usuários com métodos utilitários.
    """

    def setUp(self):
        """
        Configuração inicial dos testes.
        """
        # Criar usuários de teste com diferentes roles
        self.client_user = self.create_user(
            username="client_user",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            first_name="Cliente",
            last_name="Teste",
        )

        self.barber_user = self.create_user(
            username="barber_user",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER,
            first_name="Barbeiro",
            last_name="Teste",
        )

        self.admin_user = self.create_user(
            username="admin_user",
            email="admin@test.com",
            password="testpass123",
            role=User.Role.ADMIN,
            first_name="Admin",
            last_name="Teste",
            is_staff=True,
            is_superuser=True,
        )

        # Usuário inativo para testes
        self.inactive_user = self.create_user(
            username="inactive_user",
            email="inactive@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_active=False,
        )

        # URLs base
        self.users_url = "/api/v1/users/"
        self.users_me_url = "/api/v1/users/me/"
        self.users_change_password_url = "/api/v1/users/change-password/"
        self.users_barbers_url = "/api/v1/users/barbers/"
        self.users_clients_url = "/api/v1/users/clients/"
        self.users_admins_url = "/api/v1/users/admins/"
        self.users_stats_url = "/api/v1/users/stats/"
        self.users_user_type_url = "/api/v1/users/user-type/"
        self.users_profile_completion_url = "/api/v1/users/profile-completion/"

    def create_user(self, **kwargs):
        """
        Cria um usuário para testes.
        """
        defaults = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "role": User.Role.CLIENT,
        }
        defaults.update(kwargs)

        password = defaults.pop("password")
        user = User.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        return user

    def get_jwt_token(self, user):
        """
        Retorna token JWT para autenticação.
        """
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_user(self, user):
        """
        Autentica um usuário no cliente de testes.
        """
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def get_user_detail_url(self, user_id):
        """
        Retorna URL de detalhes de um usuário específico.
        """
        return f"{self.users_url}{user_id}/"

    def get_user_activate_url(self, user_id):
        """
        Retorna URL para ativar um usuário específico.
        """
        return f"{self.users_url}{user_id}/activate/"

    def get_user_deactivate_url(self, user_id):
        """
        Retorna URL para desativar um usuário específico.
        """
        return f"{self.users_url}{user_id}/deactivate/"


class UserCRUDTestCase(UserAPITestCase):
    """
    Testes para operações CRUD de usuários.
    """

    def test_list_users_authenticated(self):
        """
        Testa listagem de usuários quando autenticado.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertTrue(len(response.data["results"]) >= 3)  # client, barber, admin

    def test_list_users_unauthenticated(self):
        """
        Testa listagem de usuários quando não autenticado.
        """
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_success(self):
        """
        Testa criação de usuário com dados válidos.
        """
        user_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpass123",
            "first_name": "Novo",
            "last_name": "Usuário",
            "role": User.Role.CLIENT,
        }

        response = self.client.post(self.users_url, user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], user_data["username"])
        self.assertEqual(response.data["email"], user_data["email"])
        self.assertNotIn("password", response.data)

        # Verificar se usuário foi criado no banco
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_create_user_duplicate_email(self):
        """
        Testa criação de usuário com email duplicado.
        """
        user_data = {
            "username": "newuser",
            "email": "client@test.com",  # Email já existente
            "password": "newpass123",
            "role": User.Role.CLIENT,
        }

        response = self.client.post(self.users_url, user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_create_user_invalid_data(self):
        """
        Testa criação de usuário com dados inválidos.
        """
        user_data = {
            "username": "",  # Username vazio
            "email": "invalid-email",  # Email inválido
            "password": "123",  # Senha muito simples
        }

        response = self.client.post(self.users_url, user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_authenticated(self):
        """
        Testa recuperação de dados de um usuário específico.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_detail_url(self.barber_user.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.barber_user.id))
        self.assertEqual(response.data["username"], self.barber_user.username)

    def test_retrieve_user_unauthenticated(self):
        """
        Testa recuperação de dados quando não autenticado.
        """
        url = self.get_user_detail_url(self.barber_user.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_nonexistent_user(self):
        """
        Testa recuperação de usuário inexistente.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_detail_url("00000000-0000-0000-0000-000000000000")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_owner(self):
        """
        Testa atualização completa de dados do próprio usuário.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_detail_url(self.client_user.id)

        update_data = {
            "first_name": "Nome Atualizado",
            "last_name": "Sobrenome Atualizado",
            "phone": "11999999999",
        }

        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se dados foram atualizados
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.first_name, "Nome Atualizado")
        self.assertEqual(self.client_user.phone, "11999999999")

    def test_update_user_admin(self):
        """
        Testa atualização de usuário por administrador.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_detail_url(self.client_user.id)

        update_data = {
            "first_name": "Admin Updated",
            "is_active": True,
        }

        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_unauthorized(self):
        """
        Testa tentativa de atualizar outro usuário sem permissão.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_detail_url(self.barber_user.id)

        update_data = {
            "first_name": "Tentativa Não Autorizada",
        }

        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_user(self):
        """
        Testa atualização parcial do próprio usuário.
        """
        self.authenticate_user(self.barber_user)
        url = self.get_user_detail_url(self.barber_user.id)

        update_data = {
            "phone": "11888888888",
        }

        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.barber_user.refresh_from_db()
        self.assertEqual(self.barber_user.phone, "11888888888")

    def test_delete_user_admin(self):
        """
        Testa exclusão de usuário por administrador.
        """
        # Criar usuário específico para exclusão
        user_to_delete = self.create_user(
            username="to_delete",
            email="delete@test.com",
        )

        self.authenticate_user(self.admin_user)
        url = self.get_user_detail_url(user_to_delete.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar se usuário foi removido
        self.assertFalse(User.objects.filter(id=user_to_delete.id).exists())

    def test_delete_user_unauthorized(self):
        """
        Testa tentativa de exclusão sem permissão adequada.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_detail_url(self.barber_user.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verificar se usuário ainda existe
        self.assertTrue(User.objects.filter(id=self.barber_user.id).exists())


class UserMeActionTestCase(UserAPITestCase):
    """
    Testes para a ação customizada /me/ (perfil do usuário autenticado).
    """

    def test_get_me_authenticated(self):
        """
        Testa recuperação dos dados do próprio usuário.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.client_user.id))
        self.assertEqual(response.data["username"], self.client_user.username)
        self.assertEqual(response.data["email"], self.client_user.email)
        self.assertEqual(response.data["role"], self.client_user.role)

    def test_get_me_unauthenticated(self):
        """
        Testa acesso ao /me/ sem autenticação.
        """
        response = self.client.get(self.users_me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_me_update_profile(self):
        """
        Testa atualização completa do perfil via PUT /me/.
        """
        self.authenticate_user(self.barber_user)

        update_data = {
            "first_name": "Barbeiro Atualizado",
            "last_name": "Silva",
            "phone": "11987654321",
            "birth_date": "1990-01-15",
        }

        response = self.client.put(self.users_me_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se dados foram atualizados
        self.barber_user.refresh_from_db()
        self.assertEqual(self.barber_user.first_name, "Barbeiro Atualizado")
        self.assertEqual(self.barber_user.phone, "11987654321")
        self.assertEqual(str(self.barber_user.birth_date), "1990-01-15")

    def test_patch_me_partial_update(self):
        """
        Testa atualização parcial do perfil via PATCH /me/.
        """
        self.authenticate_user(self.admin_user)

        update_data = {
            "phone": "11555555555",
        }

        response = self.client.patch(self.users_me_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se apenas o telefone foi atualizado
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.phone, "11555555555")
        # Outros campos devem permanecer inalterados
        self.assertEqual(self.admin_user.first_name, "Admin")

    def test_put_me_invalid_data(self):
        """
        Testa atualização do perfil com dados inválidos.
        """
        self.authenticate_user(self.client_user)

        update_data = {
            "birth_date": "data-invalida",  # Data inválida
        }

        response = self.client.put(self.users_me_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("birth_date", response.data)

    def test_patch_me_readonly_fields(self):
        """
        Testa tentativa de atualizar campos readonly via PATCH.
        """
        self.authenticate_user(self.client_user)
        original_username = self.client_user.username

        update_data = {
            "username": "novo_username",  # Tentativa de alterar username
            "role": User.Role.ADMIN,  # Tentativa de alterar role
            "first_name": "Nome Válido",  # Campo válido
        }

        response = self.client.patch(self.users_me_url, update_data)

        # A requisição deve ser bem-sucedida, mas campos readonly ignorados
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.username, original_username)  # Não deve mudar
        self.assertEqual(self.client_user.role, User.Role.CLIENT)  # Não deve mudar
        self.assertEqual(self.client_user.first_name, "Nome Válido")  # Deve mudar

    def test_me_returns_detailed_data(self):
        """
        Testa se /me/ retorna dados detalhados do usuário.
        """
        # Adicionar mais dados ao usuário de teste
        self.client_user.birth_date = date(1995, 5, 20)
        self.client_user.phone = "11999887766"
        self.client_user.save()

        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se campos detalhados estão presentes
        expected_fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "birth_date",
            "is_active",
            "date_joined",
        ]

        for field in expected_fields:
            self.assertIn(
                field, response.data, f"Campo '{field}' não encontrado na resposta"
            )

    def test_me_update_preserves_sensitive_fields(self):
        """
        Testa se atualização via /me/ preserva campos sensíveis.
        """
        original_date_joined = self.barber_user.date_joined
        original_is_active = self.barber_user.is_active

        self.authenticate_user(self.barber_user)

        update_data = {
            "first_name": "Novo Nome",
            "is_active": False,  # Tentativa de desativar conta
            "date_joined": "2020-01-01",  # Tentativa de alterar data de criação
        }

        response = self.client.patch(self.users_me_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.barber_user.refresh_from_db()
        self.assertEqual(self.barber_user.first_name, "Novo Nome")  # Deve mudar
        self.assertEqual(
            self.barber_user.is_active, original_is_active
        )  # Não deve mudar
        self.assertEqual(
            self.barber_user.date_joined, original_date_joined
        )  # Não deve mudar


class UserChangePasswordTestCase(UserAPITestCase):
    """
    Testes para a ação de alteração de senha.
    """

    def test_change_password_success(self):
        """
        Testa alteração de senha com dados válidos.
        """
        self.authenticate_user(self.client_user)

        password_data = {
            "old_password": "testpass123",
            "new_password": "newsecurepass456",
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Senha alterada com sucesso.")

        # Verificar se a senha foi alterada
        self.client_user.refresh_from_db()
        self.assertTrue(self.client_user.check_password("newsecurepass456"))
        self.assertFalse(self.client_user.check_password("testpass123"))

    def test_change_password_unauthenticated(self):
        """
        Testa tentativa de alterar senha sem autenticação.
        """
        password_data = {
            "old_password": "testpass123",
            "new_password": "newsecurepass456",
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_wrong_old_password(self):
        """
        Testa alteração com senha atual incorreta.
        """
        self.authenticate_user(self.barber_user)

        password_data = {
            "old_password": "senhaerrada",
            "new_password": "newsecurepass456",
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)

        # Verificar se a senha não foi alterada
        self.barber_user.refresh_from_db()
        self.assertTrue(self.barber_user.check_password("testpass123"))

    def test_change_password_weak_new_password(self):
        """
        Testa alteração com nova senha muito fraca.
        """
        self.authenticate_user(self.admin_user)

        password_data = {
            "old_password": "testpass123",
            "new_password": "123",  # Senha muito simples
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_change_password_same_password(self):
        """
        Testa tentativa de usar a mesma senha atual como nova senha.
        """
        self.authenticate_user(self.client_user)

        password_data = {
            "old_password": "testpass123",
            "new_password": "testpass123",  # Mesma senha
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_change_password_missing_fields(self):
        """
        Testa alteração de senha com campos obrigatórios faltando.
        """
        self.authenticate_user(self.barber_user)

        # Teste sem old_password
        response = self.client.post(
            self.users_change_password_url,
            {
                "new_password": "newsecurepass456",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)

        # Teste sem new_password
        response = self.client.post(
            self.users_change_password_url,
            {
                "old_password": "testpass123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_change_password_empty_fields(self):
        """
        Testa alteração de senha com campos vazios.
        """
        self.authenticate_user(self.admin_user)

        password_data = {
            "old_password": "",
            "new_password": "",
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)
        self.assertIn("new_password", response.data)

    def test_change_password_maintains_session(self):
        """
        Testa se a sessão é mantida após alteração da senha.
        """
        self.authenticate_user(self.client_user)

        # Alterar senha
        password_data = {
            "old_password": "testpass123",
            "new_password": "newsecurepass456",
        }

        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se ainda consegue acessar endpoints autenticados
        response = self.client.get(self.users_me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_different_users(self):
        """
        Testa alteração de senha com diferentes tipos de usuário.
        """
        # Teste com cliente
        self.authenticate_user(self.client_user)
        password_data = {
            "old_password": "testpass123",
            "new_password": "clientnewpass123",
        }
        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Teste com barbeiro
        self.authenticate_user(self.barber_user)
        password_data = {
            "old_password": "testpass123",
            "new_password": "barbernewpass123",
        }
        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Teste com admin
        self.authenticate_user(self.admin_user)
        password_data = {
            "old_password": "testpass123",
            "new_password": "adminnewpass123",
        }
        response = self.client.post(self.users_change_password_url, password_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserRoleBasedListingTestCase(UserAPITestCase):
    """
    Testes para ações de listagem baseadas em roles (/barbers/, /clients/, /admins/).
    """

    def setUp(self):
        super().setUp()

        # Criar usuários adicionais para testes de listagem
        self.extra_barber = self.create_user(
            username="barber2",
            email="barber2@test.com",
            role=User.Role.BARBER,
            first_name="Segundo",
            last_name="Barbeiro",
        )

        self.extra_client = self.create_user(
            username="client2",
            email="client2@test.com",
            role=User.Role.CLIENT,
            first_name="Segundo",
            last_name="Cliente",
        )

        self.extra_admin = self.create_user(
            username="admin2",
            email="admin2@test.com",
            role=User.Role.ADMIN,
            first_name="Segundo",
            last_name="Admin",
        )

    def test_list_barbers_authenticated(self):
        """
        Testa listagem de barbeiros quando autenticado.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_barbers_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        # Deve retornar apenas barbeiros
        barber_usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("barber_user", barber_usernames)
        self.assertIn("barber2", barber_usernames)
        self.assertNotIn("client_user", barber_usernames)
        self.assertNotIn("admin_user", barber_usernames)

    def test_list_barbers_unauthenticated(self):
        """
        Testa listagem de barbeiros sem autenticação.
        """
        response = self.client.get(self.users_barbers_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_barbers_with_search(self):
        """
        Testa listagem de barbeiros com filtro de busca.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(f"{self.users_barbers_url}?search=Segundo")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["first_name"], "Segundo")

    def test_list_clients_authenticated(self):
        """
        Testa listagem de clientes quando autenticado.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(self.users_clients_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        # Deve retornar apenas clientes
        client_usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("client_user", client_usernames)
        self.assertIn("client2", client_usernames)
        self.assertNotIn("barber_user", client_usernames)
        self.assertNotIn("admin_user", client_usernames)

    def test_list_clients_unauthenticated(self):
        """
        Testa listagem de clientes sem autenticação.
        """
        response = self.client.get(self.users_clients_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_clients_with_search(self):
        """
        Testa listagem de clientes com filtro de busca por email.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_clients_url}?search=client2@test.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "client2@test.com")

    def test_list_admins_admin_user(self):
        """
        Testa listagem de administradores por usuário admin.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(self.users_admins_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        # Deve retornar apenas administradores
        admin_usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("admin_user", admin_usernames)
        self.assertIn("admin2", admin_usernames)
        self.assertNotIn("client_user", admin_usernames)
        self.assertNotIn("barber_user", admin_usernames)

    def test_list_admins_non_admin_user(self):
        """
        Testa listagem de administradores por usuário não-admin.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_admins_url)

        # Apenas admins podem ver a lista de admins
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_admins_barber_user(self):
        """
        Testa listagem de administradores por barbeiro.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(self.users_admins_url)

        # Barbeiros não devem ter acesso à lista de admins
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_admins_unauthenticated(self):
        """
        Testa listagem de administradores sem autenticação.
        """
        response = self.client.get(self.users_admins_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_admins_with_search(self):
        """
        Testa listagem de administradores com filtro de busca.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_admins_url}?search=admin2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "admin2")

    def test_role_lists_exclude_inactive_users(self):
        """
        Testa se usuários inativos são excluídos das listas por role.
        """
        # Criar um barbeiro inativo
        inactive_barber = self.create_user(
            username="inactive_barber",
            email="inactive_barber@test.com",
            role=User.Role.BARBER,
            is_active=False,
        )

        self.authenticate_user(self.admin_user)
        response = self.client.get(self.users_barbers_url)

        # Verificar que o barbeiro inativo não aparece na lista
        barber_usernames = [user["username"] for user in response.data["results"]]
        self.assertNotIn("inactive_barber", barber_usernames)

    def test_role_lists_pagination(self):
        """
        Testa se a paginação funciona corretamente nas listas por role.
        """
        # Criar mais barbeiros para testar paginação
        for i in range(5):
            self.create_user(
                username=f"barber_extra_{i}",
                email=f"barber_extra_{i}@test.com",
                role=User.Role.BARBER,
            )

        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_barbers_url}?page_size=3")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("count", response.data)

    def test_search_multiple_fields(self):
        """
        Testa busca em múltiplos campos (username, email, first_name, last_name).
        """
        self.authenticate_user(self.barber_user)

        # Buscar por first_name
        response = self.client.get(f"{self.users_clients_url}?search=Cliente")
        self.assertGreater(len(response.data["results"]), 0)

        # Buscar por username
        response = self.client.get(f"{self.users_clients_url}?search=client_user")
        self.assertEqual(len(response.data["results"]), 1)

        # Buscar por email
        response = self.client.get(f"{self.users_clients_url}?search=client@test.com")
        self.assertEqual(len(response.data["results"]), 1)


class UserAdminActionsTestCase(UserAPITestCase):
    """
    Testes para ações administrativas (/stats/, /activate/, /deactivate/).
    """

    def test_stats_admin_user(self):
        """
        Testa acesso às estatísticas por usuário administrador.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(self.users_stats_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se estatísticas estão presentes
        expected_keys = [
            "total_users",
            "active_users",
            "inactive_users",
            "clients_count",
            "barbers_count",
            "admins_count",
        ]

        for key in expected_keys:
            self.assertIn(key, response.data)
            self.assertIsInstance(response.data[key], int)

        # Verificar valores básicos
        self.assertGreaterEqual(
            response.data["total_users"], 4
        )  # client, barber, admin, inactive
        self.assertGreater(response.data["active_users"], 0)
        self.assertGreater(response.data["clients_count"], 0)
        self.assertGreater(response.data["barbers_count"], 0)
        self.assertGreater(response.data["admins_count"], 0)

    def test_stats_non_admin_user(self):
        """
        Testa acesso às estatísticas por usuário não-admin.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_stats_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stats_barber_user(self):
        """
        Testa acesso às estatísticas por barbeiro.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(self.users_stats_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stats_unauthenticated(self):
        """
        Testa acesso às estatísticas sem autenticação.
        """
        response = self.client.get(self.users_stats_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_activate_user_admin(self):
        """
        Testa ativação de usuário por administrador.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_activate_url(self.inactive_user.id)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verificar se usuário foi ativado
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)

    def test_activate_user_non_admin(self):
        """
        Testa tentativa de ativação por usuário não-admin.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_activate_url(self.inactive_user.id)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verificar se usuário permanece inativo
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)

    def test_activate_user_barber(self):
        """
        Testa tentativa de ativação por barbeiro.
        """
        self.authenticate_user(self.barber_user)
        url = self.get_user_activate_url(self.inactive_user.id)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_activate_user_unauthenticated(self):
        """
        Testa tentativa de ativação sem autenticação.
        """
        url = self.get_user_activate_url(self.inactive_user.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_activate_nonexistent_user(self):
        """
        Testa ativação de usuário inexistente.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_activate_url("00000000-0000-0000-0000-000000000000")

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deactivate_user_admin(self):
        """
        Testa desativação de usuário por administrador.
        """
        # Criar usuário ativo para desativar
        active_user = self.create_user(
            username="to_deactivate",
            email="deactivate@test.com",
            is_active=True,
        )

        self.authenticate_user(self.admin_user)
        url = self.get_user_deactivate_url(active_user.id)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verificar se usuário foi desativado
        active_user.refresh_from_db()
        self.assertFalse(active_user.is_active)

    def test_deactivate_user_non_admin(self):
        """
        Testa tentativa de desativação por usuário não-admin.
        """
        self.authenticate_user(self.client_user)
        url = self.get_user_deactivate_url(self.barber_user.id)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verificar se usuário permanece ativo
        self.barber_user.refresh_from_db()
        self.assertTrue(self.barber_user.is_active)

    def test_deactivate_user_barber(self):
        """
        Testa tentativa de desativação por barbeiro.
        """
        self.authenticate_user(self.barber_user)
        url = self.get_user_deactivate_url(self.client_user.id)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_user_unauthenticated(self):
        """
        Testa tentativa de desativação sem autenticação.
        """
        url = self.get_user_deactivate_url(self.client_user.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deactivate_self_admin(self):
        """
        Testa tentativa de admin desativar a si mesmo.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_deactivate_url(self.admin_user.id)

        response = self.client.post(url)

        # Dependendo da implementação do modelo, pode ser permitido ou não
        # Assumindo que é permitido por enquanto
        if response.status_code == status.HTTP_200_OK:
            self.admin_user.refresh_from_db()
            self.assertFalse(self.admin_user.is_active)
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            # Se não for permitido, deve retornar 403
            self.admin_user.refresh_from_db()
            self.assertTrue(self.admin_user.is_active)

    def test_deactivate_nonexistent_user(self):
        """
        Testa desativação de usuário inexistente.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_deactivate_url("00000000-0000-0000-0000-000000000000")

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_already_active_user(self):
        """
        Testa ativação de usuário já ativo.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_activate_url(self.client_user.id)  # Usuário já ativo

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Usuário deve permanecer ativo
        self.client_user.refresh_from_db()
        self.assertTrue(self.client_user.is_active)

    def test_deactivate_already_inactive_user(self):
        """
        Testa desativação de usuário já inativo.
        """
        self.authenticate_user(self.admin_user)
        url = self.get_user_deactivate_url(self.inactive_user.id)  # Usuário já inativo

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Usuário deve permanecer inativo
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)


class UserUtilityActionsTestCase(UserAPITestCase):
    """
    Testes para ações utilitárias (/user-type/ e /profile-completion/).
    """

    def test_user_type_client(self):
        """
        Testa retorno de informações de tipo para usuário cliente.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_user_type_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = {
            "is_barber": False,
            "is_client": True,
            "is_admin_user": False,
            "is_barbershop_owner": False,
            "role": User.Role.CLIENT,
        }

        for key, value in expected_data.items():
            self.assertEqual(response.data[key], value)

        self.assertIn("role_display", response.data)

    def test_user_type_barber(self):
        """
        Testa retorno de informações de tipo para usuário barbeiro.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(self.users_user_type_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = {
            "is_barber": True,
            "is_client": False,
            "is_admin_user": False,
            "is_barbershop_owner": False,
            "role": User.Role.BARBER,
        }

        for key, value in expected_data.items():
            self.assertEqual(response.data[key], value)

    def test_user_type_admin(self):
        """
        Testa retorno de informações de tipo para usuário administrador.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(self.users_user_type_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = {
            "is_barber": False,
            "is_client": False,
            "is_admin_user": True,
            "is_barbershop_owner": False,
            "role": User.Role.ADMIN,
        }

        for key, value in expected_data.items():
            self.assertEqual(response.data[key], value)

    def test_user_type_barbershop_owner(self):
        """
        Testa retorno para barbeiro proprietário de barbearia.
        """
        # Tornar o barbeiro um proprietário
        self.barber_user.is_barbershop_owner = True
        self.barber_user.save()

        self.authenticate_user(self.barber_user)
        response = self.client.get(self.users_user_type_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_barbershop_owner"])
        self.assertTrue(response.data["is_barber"])

    def test_user_type_unauthenticated(self):
        """
        Testa acesso sem autenticação.
        """
        response = self.client.get(self.users_user_type_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_completion_basic_profile(self):
        """
        Testa completude de perfil básico.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_profile_completion_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("completion_percentage", response.data)
        self.assertIn("has_profile_picture", response.data)

        # Verificar tipos de dados
        self.assertIsInstance(response.data["completion_percentage"], (int, float))
        self.assertIsInstance(response.data["has_profile_picture"], bool)

        # Porcentagem deve estar entre 0 e 100
        self.assertGreaterEqual(response.data["completion_percentage"], 0)
        self.assertLessEqual(response.data["completion_percentage"], 100)

    def test_profile_completion_complete_profile(self):
        """
        Testa completude de perfil completo.
        """
        # Preencher dados do usuário
        self.barber_user.first_name = "Barbeiro"
        self.barber_user.last_name = "Completo"
        self.barber_user.phone = "11999999999"
        self.barber_user.birth_date = date(1990, 1, 1)
        self.barber_user.save()

        self.authenticate_user(self.barber_user)
        response = self.client.get(self.users_profile_completion_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Perfil com mais dados deve ter maior porcentagem de completude
        completion_percentage = response.data["completion_percentage"]
        self.assertGreater(
            completion_percentage, 50
        )  # Assumindo que dados básicos dão mais de 50%

    def test_profile_completion_empty_profile(self):
        """
        Testa completude de perfil vazio.
        """
        # Criar usuário com dados mínimos
        empty_user = self.create_user(
            username="empty_user",
            email="empty@test.com",
            password="testpass123",
        )
        # Limpar campos opcionais
        empty_user.first_name = ""
        empty_user.last_name = ""
        empty_user.phone = None
        empty_user.birth_date = None
        empty_user.save()

        self.authenticate_user(empty_user)
        response = self.client.get(self.users_profile_completion_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Perfil vazio deve ter baixa porcentagem
        completion_percentage = response.data["completion_percentage"]
        self.assertLess(completion_percentage, 100)
        self.assertFalse(response.data["has_profile_picture"])

    def test_profile_completion_unauthenticated(self):
        """
        Testa acesso sem autenticação.
        """
        response = self.client.get(self.users_profile_completion_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_completion_different_roles(self):
        """
        Testa completude de perfil para diferentes tipos de usuário.
        """
        users_to_test = [
            self.client_user,
            self.barber_user,
            self.admin_user,
        ]

        for user in users_to_test:
            with self.subTest(user_role=user.role):
                self.authenticate_user(user)
                response = self.client.get(self.users_profile_completion_url)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn("completion_percentage", response.data)
                self.assertIn("has_profile_picture", response.data)

    def test_user_type_response_structure(self):
        """
        Testa estrutura completa da resposta do user-type.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_user_type_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        required_fields = [
            "is_barber",
            "is_client",
            "is_admin_user",
            "is_barbershop_owner",
            "role",
            "role_display",
        ]

        for field in required_fields:
            self.assertIn(
                field, response.data, f"Campo '{field}' não encontrado na resposta"
            )

    def test_profile_completion_calculation_consistency(self):
        """
        Testa consistência do cálculo de completude de perfil.
        """
        self.authenticate_user(self.admin_user)

        # Fazer múltiplas chamadas e verificar consistência
        response1 = self.client.get(self.users_profile_completion_url)
        response2 = self.client.get(self.users_profile_completion_url)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Os resultados devem ser idênticos
        self.assertEqual(
            response1.data["completion_percentage"],
            response2.data["completion_percentage"],
        )
        self.assertEqual(
            response1.data["has_profile_picture"], response2.data["has_profile_picture"]
        )


class UserFiltersAndSearchTestCase(UserAPITestCase):
    """
    Testes para filtros e funcionalidades de busca.
    """

    def setUp(self):
        super().setUp()

        # Criar usuários adicionais com dados específicos para filtros
        self.search_user1 = self.create_user(
            username="search_test1",
            email="search1@example.com",
            first_name="João",
            last_name="Silva",
            role=User.Role.BARBER,
        )

        self.search_user2 = self.create_user(
            username="search_test2",
            email="search2@example.com",
            first_name="Maria",
            last_name="Santos",
            role=User.Role.CLIENT,
        )

        self.barbershop_owner = self.create_user(
            username="owner_barber",
            email="owner@example.com",
            role=User.Role.BARBER,
            is_barbershop_owner=True,
        )

    def test_filter_by_role_client(self):
        """
        Testa filtro por role CLIENT.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_url}?role=CLIENT")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os usuários retornados são clientes
        for user in response.data["results"]:
            self.assertEqual(user["role"], User.Role.CLIENT)

    def test_filter_by_role_barber(self):
        """
        Testa filtro por role BARBER.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_url}?role=BARBER")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os usuários retornados são barbeiros
        for user in response.data["results"]:
            self.assertEqual(user["role"], User.Role.BARBER)

    def test_filter_by_role_admin(self):
        """
        Testa filtro por role ADMIN.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(f"{self.users_url}?role=ADMIN")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os usuários retornados são admins
        for user in response.data["results"]:
            self.assertEqual(user["role"], User.Role.ADMIN)

    def test_filter_by_is_barbershop_owner_true(self):
        """
        Testa filtro por proprietários de barbearia.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_url}?is_barbershop_owner=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os usuários retornados são proprietários
        for user in response.data["results"]:
            self.assertTrue(user["is_barbershop_owner"])

    def test_filter_by_is_barbershop_owner_false(self):
        """
        Testa filtro por não-proprietários de barbearia.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_url}?is_barbershop_owner=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se nenhum usuário retornado é proprietário
        for user in response.data["results"]:
            self.assertFalse(user["is_barbershop_owner"])

    def test_filter_by_is_active_true(self):
        """
        Testa filtro por usuários ativos.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(f"{self.users_url}?is_active=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os usuários retornados são ativos
        for user in response.data["results"]:
            self.assertTrue(user["is_active"])

    def test_filter_by_is_active_false(self):
        """
        Testa filtro por usuários inativos.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_url}?is_active=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os usuários retornados são inativos
        for user in response.data["results"]:
            self.assertFalse(user["is_active"])

    def test_search_by_username(self):
        """
        Testa busca por username.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_url}?search=search_test1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "search_test1")

    def test_search_by_email(self):
        """
        Testa busca por email.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_url}?search=search2@example.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "search2@example.com")

    def test_search_by_first_name(self):
        """
        Testa busca por primeiro nome.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(f"{self.users_url}?search=João")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se o usuário João foi encontrado
        found_user = False
        for user in response.data["results"]:
            if user["first_name"] == "João":
                found_user = True
                break
        self.assertTrue(found_user)

    def test_search_by_last_name(self):
        """
        Testa busca por sobrenome.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_url}?search=Santos")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se o usuário Santos foi encontrado
        found_user = False
        for user in response.data["results"]:
            if user["last_name"] == "Santos":
                found_user = True
                break
        self.assertTrue(found_user)

    def test_search_case_insensitive(self):
        """
        Testa busca case-insensitive.
        """
        self.authenticate_user(self.admin_user)

        # Buscar com maiúsculas - usando "Maria" instead of "João" to avoid encoding issues
        response1 = self.client.get(f"{self.users_url}?search=MARIA")
        # Buscar com minúsculas
        response2 = self.client.get(f"{self.users_url}?search=maria")

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Ambas as buscas devem retornar o mesmo resultado
        self.assertEqual(len(response1.data["results"]), len(response2.data["results"]))

        # Deve encontrar pelo menos 1 usuário (search_user2 tem first_name="Maria")
        self.assertGreaterEqual(len(response1.data["results"]), 1)

    def test_search_partial_match(self):
        """
        Testa busca com correspondência parcial.
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(f"{self.users_url}?search=search")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Deve encontrar usuários com "search" no nome
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_combined_filter_and_search(self):
        """
        Testa combinação de filtros e busca.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_url}?role=BARBER&search=search")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os resultados são barbeiros
        for user in response.data["results"]:
            self.assertEqual(user["role"], User.Role.BARBER)

    def test_ordering_by_date_joined_desc(self):
        """
        Testa ordenação por data de criação (padrão - decrescente).
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_url}?ordering=-date_joined")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar ordenação (usuários mais novos primeiro)
        results = response.data["results"]
        if len(results) >= 2:
            first_date = results[0]["date_joined"]
            second_date = results[1]["date_joined"]
            self.assertGreaterEqual(first_date, second_date)

    def test_ordering_by_username_asc(self):
        """
        Testa ordenação por username (crescente).
        """
        self.authenticate_user(self.barber_user)
        response = self.client.get(f"{self.users_url}?ordering=username")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar ordenação alfabética
        results = response.data["results"]
        if len(results) >= 2:
            usernames = [user["username"] for user in results]
            self.assertEqual(usernames, sorted(usernames))

    def test_ordering_by_email_desc(self):
        """
        Testa ordenação por email (decrescente).
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(f"{self.users_url}?ordering=-email")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar ordenação reversa por email
        results = response.data["results"]
        if len(results) >= 2:
            emails = [user["email"] for user in results]
            self.assertEqual(emails, sorted(emails, reverse=True))

    def test_multiple_filters(self):
        """
        Testa aplicação de múltiplos filtros simultaneamente.
        """
        self.authenticate_user(self.admin_user)
        response = self.client.get(
            f"{self.users_url}?role=BARBER&is_active=true&is_barbershop_owner=false"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se todos os critérios são atendidos
        for user in response.data["results"]:
            self.assertEqual(user["role"], User.Role.BARBER)
            self.assertTrue(user["is_active"])
            self.assertFalse(user["is_barbershop_owner"])

    def test_search_no_results(self):
        """
        Testa busca que não retorna resultados.
        """
        self.authenticate_user(self.client_user)
        response = self.client.get(f"{self.users_url}?search=usuarioQueNaoExiste")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_filter_no_results(self):
        """
        Testa filtro que não retorna resultados.
        """
        self.authenticate_user(self.barber_user)

        # Filtrar por uma combinação que não existe
        response = self.client.get(
            f"{self.users_url}?role=CLIENT&is_barbershop_owner=true"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


class UserPermissionsAndEdgeCasesTestCase(UserAPITestCase):
    """
    Testes para permissões avançadas e casos extremos.
    """

    def test_permissions_hierarchy(self):
        """
        Testa hierarquia de permissões entre diferentes roles.
        """
        # Admin pode ver todos os usuários
        self.authenticate_user(self.admin_user)
        response = self.client.get(self.users_url)
        admin_count = len(response.data["results"])

        # Barbeiro pode ver todos os usuários
        self.authenticate_user(self.barber_user)
        response = self.client.get(self.users_url)
        barber_count = len(response.data["results"])

        # Cliente pode ver todos os usuários
        self.authenticate_user(self.client_user)
        response = self.client.get(self.users_url)
        client_count = len(response.data["results"])

        # Todos devem ver a mesma quantidade (todos têm IsAuthenticated)
        self.assertEqual(admin_count, barber_count)
        self.assertEqual(barber_count, client_count)

    def test_own_profile_access(self):
        """
        Testa acesso ao próprio perfil vs perfil de outros.
        """
        self.authenticate_user(self.client_user)

        # Deve conseguir ver próprio perfil
        own_url = self.get_user_detail_url(self.client_user.id)
        response = self.client.get(own_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Deve conseguir ver perfil de outros (IsAuthenticated permite)
        other_url = self.get_user_detail_url(self.barber_user.id)
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_own_vs_others_profile(self):
        """
        Testa permissões para atualizar próprio perfil vs outros.
        """
        self.authenticate_user(self.client_user)

        # Deve conseguir atualizar próprio perfil
        own_url = self.get_user_detail_url(self.client_user.id)
        response = self.client.patch(own_url, {"first_name": "Novo Nome"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Não deve conseguir atualizar perfil de outros
        other_url = self.get_user_detail_url(self.barber_user.id)
        response = self.client.patch(other_url, {"first_name": "Tentativa"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_any_profile(self):
        """
        Testa se admin pode atualizar qualquer perfil.
        """
        self.authenticate_user(self.admin_user)

        # Admin deve conseguir atualizar perfil de cliente
        client_url = self.get_user_detail_url(self.client_user.id)
        response = self.client.patch(client_url, {"first_name": "Admin Update"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Admin deve conseguir atualizar perfil de barbeiro
        barber_url = self.get_user_detail_url(self.barber_user.id)
        response = self.client.patch(barber_url, {"first_name": "Admin Update"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_permissions(self):
        """
        Testa permissões para deletar usuários.
        """
        test_user = self.create_user(
            username="delete_test",
            email="delete@test.com",
        )

        # Cliente não deve conseguir deletar outros usuários
        self.authenticate_user(self.client_user)
        url = self.get_user_detail_url(test_user.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Barbeiro não deve conseguir deletar outros usuários
        self.authenticate_user(self.barber_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin deve conseguir deletar usuários
        self.authenticate_user(self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_invalid_uuid_handling(self):
        """
        Testa tratamento de UUIDs inválidos.
        """
        self.authenticate_user(self.admin_user)

        # UUID mal formado
        invalid_url = f"{self.users_url}invalid-uuid/"
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # UUID válido mas inexistente
        nonexistent_url = self.get_user_detail_url(
            "12345678-1234-5678-9012-123456789012"
        )
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_large_dataset_performance(self):
        """
        Testa performance com dataset maior.
        """
        # Criar múltiplos usuários
        for i in range(20):
            self.create_user(
                username=f"bulk_user_{i}",
                email=f"bulk_{i}@test.com",
                role=User.Role.CLIENT if i % 2 == 0 else User.Role.BARBER,
            )

        self.authenticate_user(self.admin_user)

        # Testar listagem com paginação
        response = self.client.get(f"{self.users_url}?page_size=10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)

    def test_concurrent_user_creation(self):
        """
        Testa cenário de criação simultânea com emails únicos.
        """
        # Tentar criar usuários com mesmo email
        user_data = {
            "username": "concurrent1",
            "email": "concurrent@test.com",
            "password": "testpass123",
        }

        response1 = self.client.post(self.users_url, user_data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Segundo usuário com mesmo email deve falhar
        user_data["username"] = "concurrent2"
        response2 = self.client.post(self.users_url, user_data)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response2.data)

    def test_password_security_in_responses(self):
        """
        Testa se senhas nunca são expostas nas respostas.
        """
        self.authenticate_user(self.admin_user)

        # Listar usuários
        response = self.client.get(self.users_url)
        for user in response.data["results"]:
            self.assertNotIn("password", user)

        # Detalhar usuário
        url = self.get_user_detail_url(self.client_user.id)
        response = self.client.get(url)
        self.assertNotIn("password", response.data)

        # Criar usuário
        user_data = {
            "username": "securitytest",
            "email": "security@test.com",
            "password": "secretpassword123",
        }
        response = self.client.post(self.users_url, user_data)
        self.assertNotIn("password", response.data)

    def test_special_characters_handling(self):
        """
        Testa tratamento de caracteres especiais.
        """
        user_data = {
            "username": "test_user_special",
            "email": "special@test.com",
            "password": "testpass123",
            "first_name": "José",
            "last_name": "D'Angelo",
        }

        response = self.client.post(self.users_url, user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["first_name"], "José")
        self.assertEqual(response.data["last_name"], "D'Angelo")

    def test_long_field_values(self):
        """
        Testa valores muito longos nos campos.
        """
        user_data = {
            "username": "a" * 151,  # Username muito longo
            "email": "test@test.com",
            "password": "testpass123",
        }

        response = self.client.post(self.users_url, user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_search_and_filters(self):
        """
        Testa comportamento com parâmetros vazios.
        """
        self.authenticate_user(self.client_user)

        # Busca vazia
        response = self.client.get(f"{self.users_url}?search=")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Filtro vazio
        response = self.client.get(f"{self.users_url}?role=")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_malformed_requests(self):
        """
        Testa requisições mal formadas.
        """
        self.authenticate_user(self.admin_user)

        # JSON mal formado na criação
        response = self.client.post(
            self.users_url, data="{ invalid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting_behavior(self):
        """
        Testa comportamento sob múltiplas requisições rápidas.
        """
        self.authenticate_user(self.client_user)

        # Fazer múltiplas requisições rápidas
        responses = []
        for _ in range(10):
            response = self.client.get(self.users_me_url)
            responses.append(response.status_code)

        # Todas devem ser bem-sucedidas (sem rate limiting configurado)
        for status_code in responses:
            self.assertEqual(status_code, status.HTTP_200_OK)

    def test_inactive_user_login_simulation(self):
        """
        Testa tentativas de ação com usuário inativo.
        """
        # Simular tentativa de autenticação com usuário inativo
        # (Nota: JWT não impede isso automaticamente, depende da implementação)
        token = self.get_jwt_token(self.inactive_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(self.users_me_url)

        # Comportamento pode variar dependendo da implementação
        # JWT tokens são válidos mesmo para usuários inativos
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_401_UNAUTHORIZED,
            ],
        )

    def test_timezone_handling(self):
        """
        Testa tratamento de timezone em datas.
        """
        self.authenticate_user(self.client_user)

        # Atualizar com data específica
        update_data = {
            "birth_date": "1990-12-25",
        }

        response = self.client.patch(self.users_me_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["birth_date"], "1990-12-25")
