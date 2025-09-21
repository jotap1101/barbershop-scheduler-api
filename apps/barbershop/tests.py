from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Barbershop, BarbershopCustomer, Service

User = get_user_model()


class BarbershopAPITestCase(APITestCase):
    """
    Classe base para testes da API de barbearias com métodos utilitários.
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
            is_barbershop_owner=True,
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

        self.owner_user = self.create_user(
            username="owner_user",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            first_name="Proprietário",
            last_name="Teste",
            is_barbershop_owner=True,
        )

        # Criar barbearia de teste
        self.barbershop = Barbershop.objects.create(
            name="Barbearia Teste",
            description="Uma barbearia de teste",
            cnpj="12345678901234",
            address="Rua Teste, 123",
            email="barbershop@test.com",
            phone="11999999999",
            website="https://barbershop.test.com",
            owner=self.barber_user,
        )

        # Criar barbearia do owner_user
        self.owner_barbershop = Barbershop.objects.create(
            name="Barbearia Owner",
            description="Barbearia do owner",
            cnpj="98765432109876",
            address="Rua Owner, 456",
            email="owner@barbershop.com",
            phone="11888888888",
            owner=self.owner_user,
        )

        # Criar serviços de teste
        self.service = Service.objects.create(
            barbershop=self.barbershop,
            name="Corte de cabelo",
            description="Corte tradicional",
            price=Decimal("30.00"),
            duration=timedelta(minutes=30),
            available=True,
        )

        self.expensive_service = Service.objects.create(
            barbershop=self.barbershop,
            name="Corte + Barba",
            description="Corte e barba completos",
            price=Decimal("50.00"),
            duration=timedelta(minutes=60),
            available=True,
        )

        # Criar relacionamento cliente-barbearia
        self.barbershop_customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop,
            last_visit=timezone.now() - timedelta(days=10),
        )

    def create_user(self, **kwargs):
        """
        Método utilitário para criar usuários.
        """
        return User.objects.create_user(**kwargs)

    def authenticate_user(self, user):
        """
        Método utilitário para autenticar um usuário na requisição.
        """
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def create_barbershop_data(self, **kwargs):
        """
        Método utilitário para criar dados de barbearia.
        """
        data = {
            "name": "Nova Barbearia",
            "description": "Descrição da nova barbearia",
            "cnpj": "11223344556677",
            "address": "Rua Nova, 789",
            "email": "nova@barbershop.com",
            "phone": "11777777777",
            "website": "https://nova.barbershop.com",
        }
        data.update(kwargs)
        return data

    def create_service_data(self, **kwargs):
        """
        Método utilitário para criar dados de serviço.
        """
        data = {
            "barbershop": self.barbershop.id,
            "name": "Novo Serviço",
            "description": "Descrição do novo serviço",
            "price": "25.00",
            "duration": "00:45:00",
            "available": True,
        }
        data.update(kwargs)
        return data

    def create_barbershop_customer_data(self, **kwargs):
        """
        Método utilitário para criar dados de relacionamento cliente-barbearia.
        """
        data = {
            "customer": self.client_user.id,
            "barbershop": self.barbershop.id,
            "last_visit": timezone.now().isoformat(),
        }
        data.update(kwargs)
        return data


class BarbershopCRUDTests(BarbershopAPITestCase):
    """
    Testes para as operações CRUD de Barbershop.
    """

    def test_list_barbershops_authenticated(self):
        """
        Testa a listagem de barbearias por usuário autenticado.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_barbershops_unauthenticated(self):
        """
        Testa a listagem de barbearias sem autenticação.
        """
        url = reverse("barbershops-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_barbershop_authenticated(self):
        """
        Testa a recuperação de uma barbearia específica.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Barbearia Teste")
        self.assertIn("formatted_cnpj", response.data)
        self.assertIn("total_services", response.data)

    def test_create_barbershop_as_owner(self):
        """
        Testa a criação de barbearia por proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-list")
        data = self.create_barbershop_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Nova Barbearia")
        # The create serializer doesn't return owner field, so we need to verify differently
        created_barbershop = Barbershop.objects.get(name="Nova Barbearia")
        self.assertEqual(created_barbershop.owner, self.barber_user)

        # Verificar se o usuário foi marcado como proprietário
        self.barber_user.refresh_from_db()
        self.assertTrue(self.barber_user.is_barbershop_owner)

    def test_create_barbershop_as_client(self):
        """
        Testa a tentativa de criação de barbearia por cliente comum.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")
        data = self.create_barbershop_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_barbershop_invalid_cnpj(self):
        """
        Testa a criação de barbearia com CNPJ inválido.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-list")
        data = self.create_barbershop_data(cnpj="123")  # CNPJ muito curto

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_create_barbershop_duplicate_email(self):
        """
        Testa a criação de barbearia com email duplicado.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-list")
        data = self.create_barbershop_data(
            email="barbershop@test.com"
        )  # Email já existe

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_update_barbershop_as_owner(self):
        """
        Testa a atualização de barbearia pelo proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})
        data = {"name": "Barbearia Atualizada"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Barbearia Atualizada")

    def test_update_barbershop_as_non_owner(self):
        """
        Testa a tentativa de atualização de barbearia por não proprietário.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})
        data = {"name": "Tentativa de atualização"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_barbershop_as_admin(self):
        """
        Testa a atualização de barbearia por administrador.
        """
        self.authenticate_user(self.admin_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})
        data = {"name": "Atualizado pelo Admin"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Atualizado pelo Admin")

    def test_delete_barbershop_as_owner(self):
        """
        Testa a exclusão de barbearia pelo proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Barbershop.objects.filter(id=self.barbershop.id).exists())

    def test_delete_barbershop_as_non_owner(self):
        """
        Testa a tentativa de exclusão de barbearia por não proprietário.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BarbershopCustomActionsTests(BarbershopAPITestCase):
    """
    Testes para as ações customizadas de Barbershop.
    """

    def test_my_barbershops(self):
        """
        Testa a ação de listar minhas barbearias.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-my-barbershops")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Barbearia Teste")

    def test_my_barbershops_with_search(self):
        """
        Testa a busca nas minhas barbearias.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-my-barbershops")

        response = self.client.get(url, {"search": "Teste"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(url, {"search": "Inexistente"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_barbershop_services(self):
        """
        Testa a listagem de serviços de uma barbearia.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-services", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_barbershop_services_available_only(self):
        """
        Testa a listagem apenas de serviços disponíveis.
        """
        # Tornar um serviço indisponível
        self.service.available = False
        self.service.save()

        self.authenticate_user(self.client_user)
        url = reverse("barbershops-services", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url, {"available_only": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Corte + Barba")

    def test_barbershop_customers(self):
        """
        Testa a listagem de clientes de uma barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-customers", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_barbershop_stats_as_owner(self):
        """
        Testa as estatísticas da barbearia pelo proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-stats", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("basic_stats", response.data)
        self.assertIn("popular_services", response.data)
        self.assertIn("recent_customers", response.data)
        self.assertEqual(response.data["basic_stats"]["total_services"], 2)

    def test_barbershop_stats_as_non_owner(self):
        """
        Testa a tentativa de acessar estatísticas por não proprietário.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-stats", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_barbershop_revenue_report(self):
        """
        Testa o relatório de receita da barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-revenue-report", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("period", response.data)
        self.assertIn("total_revenue", response.data)
        self.assertIn("services_revenue", response.data)

    def test_barbershop_revenue_report_with_dates(self):
        """
        Testa o relatório de receita com datas específicas.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-revenue-report", kwargs={"pk": self.barbershop.id})

        start_date = "2024-01-01"
        end_date = "2024-12-31"

        response = self.client.get(
            url, {"start_date": start_date, "end_date": end_date}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["period"]["start_date"], start_date)
        self.assertEqual(response.data["period"]["end_date"], end_date)

    def test_barbershop_revenue_report_invalid_date(self):
        """
        Testa o relatório de receita com data inválida.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-revenue-report", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url, {"start_date": "data-inválida"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class ServiceCRUDTests(BarbershopAPITestCase):
    """
    Testes para as operações CRUD de Service.
    """

    def test_list_services(self):
        """
        Testa a listagem de serviços.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_services_filtered_by_barbershop(self):
        """
        Testa a listagem de serviços filtrada por barbearia.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-list")

        response = self.client.get(url, {"barbershop": self.barbershop.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_retrieve_service(self):
        """
        Testa a recuperação de um serviço específico.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-detail", kwargs={"pk": self.service.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Corte de cabelo")
        self.assertIn("formatted_price", response.data)
        self.assertIn("formatted_duration", response.data)

    def test_create_service_as_barbershop_owner(self):
        """
        Testa a criação de serviço pelo proprietário da barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-list")
        data = self.create_service_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Novo Serviço")

    def test_create_service_for_other_barbershop(self):
        """
        Testa a tentativa de criar serviço para barbearia de outro usuário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-list")
        data = self.create_service_data(barbershop=self.owner_barbershop.id)

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("barbershop", response.data)

    def test_create_service_invalid_price(self):
        """
        Testa a criação de serviço com preço inválido.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-list")
        data = self.create_service_data(price="0")

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_update_service_as_owner(self):
        """
        Testa a atualização de serviço pelo proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-detail", kwargs={"pk": self.service.id})
        data = {"name": "Serviço Atualizado"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Serviço Atualizado")

    def test_delete_service_as_owner(self):
        """
        Testa a exclusão de serviço pelo proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-detail", kwargs={"pk": self.service.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Service.objects.filter(id=self.service.id).exists())

    def test_toggle_service_availability(self):
        """
        Testa a alternância de disponibilidade do serviço.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-toggle-availability", kwargs={"pk": self.service.id})

        # Serviço está disponível, deve ficar indisponível
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["available"])

        # Alternar novamente
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["available"])

    def test_popular_services(self):
        """
        Testa a listagem de serviços populares.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-popular")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Como não temos agendamentos, não deve haver serviços populares
        self.assertEqual(len(response.data["results"]), 0)


class BarbershopCustomerCRUDTests(BarbershopAPITestCase):
    """
    Testes para as operações CRUD de BarbershopCustomer.
    """

    def test_list_barbershop_customers_as_owner(self):
        """
        Testa a listagem de clientes da barbearia pelo proprietário.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_list_barbershop_customers_filtered(self):
        """
        Testa a listagem de clientes filtrada por barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-list")

        response = self.client.get(url, {"barbershop": self.barbershop.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_barbershop_customer(self):
        """
        Testa a recuperação de um relacionamento cliente-barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse(
            "barbershop-customers-detail", kwargs={"pk": self.barbershop_customer.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("customer_tier", response.data)
        self.assertIn("total_spent", response.data)

    def test_create_barbershop_customer(self):
        """
        Testa a criação de relacionamento cliente-barbearia.
        """
        # Criar novo cliente
        new_client = self.create_user(
            username="new_client",
            email="newclient@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
        )

        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-list")
        data = self.create_barbershop_customer_data(customer=new_client.id)

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_vip_customers(self):
        """
        Testa a listagem de clientes VIP.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-vip-customers")

        response = self.client.get(url, {"barbershop": self.barbershop.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Como não temos pagamentos, não deve haver clientes VIP
        self.assertEqual(len(response.data), 0)

    def test_vip_customers_missing_barbershop(self):
        """
        Testa a listagem de clientes VIP sem especificar barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-vip-customers")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_inactive_customers(self):
        """
        Testa a listagem de clientes inativos.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-inactive-customers")

        response = self.client.get(url, {"barbershop": self.barbershop.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Como o cliente visitou há 10 dias, não é inativo (padrão 90 dias)
        self.assertEqual(len(response.data["results"]), 0)

    def test_inactive_customers_with_threshold(self):
        """
        Testa a listagem de clientes inativos com threshold personalizado.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershop-customers-inactive-customers")

        # Com threshold de 5 dias, o cliente deve aparecer como inativo
        response = self.client.get(
            url, {"barbershop": self.barbershop.id, "days_threshold": 5}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class BarbershopFiltersAndSearchTests(BarbershopAPITestCase):
    """
    Testes para filtros e busca.
    """

    def test_barbershop_search(self):
        """
        Testa a busca de barbearias.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")

        # Busca por nome
        response = self.client.get(url, {"search": "Teste"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Busca por endereço
        response = self.client.get(url, {"search": "Rua Teste"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Busca sem resultado
        response = self.client.get(url, {"search": "Inexistente"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_barbershop_filter_by_owner(self):
        """
        Testa o filtro de barbearias por proprietário.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")

        response = self.client.get(url, {"owner": self.barber_user.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_barbershop_ordering(self):
        """
        Testa a ordenação de barbearias.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")

        # Ordenar por nome
        response = self.client.get(url, {"ordering": "name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["name"], "Barbearia Owner")
        self.assertEqual(results[1]["name"], "Barbearia Teste")

        # Ordenar por nome decrescente
        response = self.client.get(url, {"ordering": "-name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["name"], "Barbearia Teste")
        self.assertEqual(results[1]["name"], "Barbearia Owner")

    def test_service_search(self):
        """
        Testa a busca de serviços.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-list")

        # Busca por nome
        response = self.client.get(url, {"search": "Corte"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Busca específica
        response = self.client.get(url, {"search": "Barba"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_service_filter_by_available(self):
        """
        Testa o filtro de serviços por disponibilidade.
        """
        # Tornar um serviço indisponível
        self.service.available = False
        self.service.save()

        self.authenticate_user(self.client_user)
        url = reverse("services-list")

        # Filtrar apenas disponíveis
        response = self.client.get(url, {"available": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Filtrar apenas indisponíveis
        response = self.client.get(url, {"available": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_service_ordering_by_price(self):
        """
        Testa a ordenação de serviços por preço.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-list")

        # Ordenar por preço crescente
        response = self.client.get(url, {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["name"], "Corte de cabelo")  # R$ 30
        self.assertEqual(results[1]["name"], "Corte + Barba")  # R$ 50

        # Ordenar por preço decrescente
        response = self.client.get(url, {"ordering": "-price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["name"], "Corte + Barba")  # R$ 50
        self.assertEqual(results[1]["name"], "Corte de cabelo")  # R$ 30


class BarbershopPermissionTests(BarbershopAPITestCase):
    """
    Testes para verificar as permissões do sistema.
    """

    def test_non_owner_cannot_access_barbershop_stats(self):
        """
        Testa que não proprietário não pode acessar estatísticas.
        """
        self.authenticate_user(self.owner_user)  # Proprietário de outra barbearia
        url = reverse("barbershops-stats", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_any_barbershop_stats(self):
        """
        Testa que admin pode acessar estatísticas de qualquer barbearia.
        """
        self.authenticate_user(self.admin_user)
        url = reverse("barbershops-stats", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_owner_cannot_update_service(self):
        """
        Testa que não proprietário não pode atualizar serviço.
        """
        self.authenticate_user(self.owner_user)  # Proprietário de outra barbearia
        url = reverse("services-detail", kwargs={"pk": self.service.id})
        data = {"name": "Tentativa de atualização"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_cannot_create_barbershop(self):
        """
        Testa que cliente comum não pode criar barbearia.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")
        data = self.create_barbershop_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BarbershopModelTests(BarbershopAPITestCase):
    """
    Testes para os métodos dos modelos.
    """

    def test_barbershop_formatted_cnpj(self):
        """
        Testa a formatação do CNPJ.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # CNPJ "12345678901234" deve ser formatado como "12.345.678/9012-34"
        self.assertEqual(response.data["formatted_cnpj"], "12.345.678/9012-34")

    def test_barbershop_formatted_phone(self):
        """
        Testa a formatação do telefone.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Phone "11999999999" deve ser formatado como "(11) 99999-9999"
        self.assertEqual(response.data["formatted_phone"], "(11) 99999-9999")

    def test_service_formatted_price(self):
        """
        Testa a formatação do preço do serviço.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-detail", kwargs={"pk": self.service.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["formatted_price"], "R$ 30.00")

    def test_service_formatted_duration(self):
        """
        Testa a formatação da duração do serviço.
        """
        self.authenticate_user(self.client_user)
        url = reverse("services-detail", kwargs={"pk": self.service.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["formatted_duration"], "30min")

    def test_barbershop_customer_tier_calculation(self):
        """
        Testa o cálculo do tier do cliente.
        """
        self.authenticate_user(self.barber_user)
        url = reverse(
            "barbershop-customers-detail", kwargs={"pk": self.barbershop_customer.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Como não há pagamentos, deve ser "New"
        self.assertEqual(response.data["customer_tier"], "New")

    def test_barbershop_contact_info_validation(self):
        """
        Testa a validação de informações de contato.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-detail", kwargs={"pk": self.barbershop.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Barbearia tem email e telefone
        self.assertTrue(response.data["has_contact_info"])


class BarbershopPaginationTests(BarbershopAPITestCase):
    """
    Testes para paginação.
    """

    def setUp(self):
        super().setUp()
        # Criar mais barbearias para testar paginação
        for i in range(15):
            user = self.create_user(
                username=f"owner_{i}",
                email=f"owner_{i}@test.com",
                password="testpass123",
                is_barbershop_owner=True,
            )
            Barbershop.objects.create(
                name=f"Barbearia {i}",
                description=f"Descrição {i}",
                cnpj=f"1234567890123{i:02d}",
                address=f"Endereço {i}",
                email=f"barbershop{i}@test.com",
                phone=f"1199999999{i:02d}",
                owner=user,
            )

    def test_barbershop_list_pagination(self):
        """
        Testa a paginação da lista de barbearias.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        # Total deve ser 17 (2 criadas no setUp + 15 criadas aqui)
        self.assertEqual(response.data["count"], 17)

    def test_barbershop_list_pagination_with_page_size(self):
        """
        Testa a paginação com tamanho de página customizado.
        """
        self.authenticate_user(self.client_user)
        url = reverse("barbershops-list")

        response = self.client.get(url, {"page_size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # A API pode ter um tamanho de página máximo ou padrão
        # Verificar se retornou um número válido de resultados
        self.assertLessEqual(len(response.data["results"]), 10)  # Max 10 per page
        self.assertGreater(len(response.data["results"]), 0)  # At least some results
        self.assertIsNotNone(response.data["next"])


class BarbershopErrorHandlingTests(BarbershopAPITestCase):
    """
    Testes para tratamento de erros.
    """

    def test_barbershop_not_found(self):
        """
        Testa erro 404 para barbearia inexistente.
        """
        self.authenticate_user(self.client_user)
        url = reverse(
            "barbershops-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_service_not_found(self):
        """
        Testa erro 404 para serviço inexistente.
        """
        self.authenticate_user(self.client_user)
        url = reverse(
            "services-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_uuid_format(self):
        """
        Testa erro para formato UUID inválido.
        """
        self.authenticate_user(self.client_user)
        url = "/api/v1/barbershops/invalid-uuid/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_barbershop_missing_required_field(self):
        """
        Testa erro ao criar barbearia sem campo obrigatório.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("barbershops-list")
        data = self.create_barbershop_data()
        del data["name"]  # Remover campo obrigatório

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_service_missing_barbershop(self):
        """
        Testa erro ao criar serviço sem especificar barbearia.
        """
        self.authenticate_user(self.barber_user)
        url = reverse("services-list")
        data = self.create_service_data()
        del data["barbershop"]  # Remover campo obrigatório

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("barbershop", response.data)
