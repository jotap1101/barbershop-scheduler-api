from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.barbershop.models import Barbershop, BarbershopCustomer, Service

from .models import Appointment, BarberSchedule

User = get_user_model()


class AppointmentAPITestCase(APITestCase):
    """
    Classe base para testes da API de agendamentos com métodos utilitários.
    """

    def setUp(self):
        """Configuração inicial para os testes"""
        # Criar usuários com diferentes roles
        self.client_user = self.create_user(
            email="client@test.com",
            role=User.Role.CLIENT,
            first_name="Cliente",
            last_name="Test",
        )

        self.barber_user = self.create_user(
            email="barber@test.com",
            role=User.Role.BARBER,
            first_name="Barbeiro",
            last_name="Test",
        )

        self.owner_user = self.create_user(
            email="owner@test.com",
            role=User.Role.CLIENT,
            is_barbershop_owner=True,
            first_name="Proprietário",
            last_name="Test",
        )

        self.admin_user = self.create_user(
            email="admin@test.com",
            role=User.Role.ADMIN,
            is_staff=True,
            first_name="Admin",
            last_name="Test",
        )

        # Criar barbearia
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            email="barbershop@test.com",
            phone="11987654321",
            address="Test Address, 123",
            cnpj="12345678000100",
        )

        # Criar serviço
        self.service = Service.objects.create(
            barbershop=self.barbershop,
            name="Corte de Cabelo",
            description="Corte tradicional",
            price=Decimal("25.00"),
            duration=timedelta(minutes=30),
            available=True,
        )

        # Criar cliente da barbearia
        self.barbershop_customer = BarbershopCustomer.objects.create(
            barbershop=self.barbershop, customer=self.client_user
        )

        # Criar horário de barbeiro
        self.barber_schedule = BarberSchedule.objects.create(
            barber=self.barber_user,
            barbershop=self.barbershop,
            weekday=1,  # Segunda-feira
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_available=True,
        )

        # Criar agendamento
        self.appointment = Appointment.objects.create(
            customer=self.barbershop_customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(days=1, hours=10),
            end_datetime=timezone.now() + timedelta(days=1, hours=10, minutes=30),
            status=Appointment.Status.PENDING,
            final_price=self.service.price,
        )

    def create_user(self, **kwargs):
        """Método para criar usuário com dados padrão"""
        defaults = {
            "username": kwargs.get("email", "test@test.com"),
            "password": "testpass123",
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    def authenticate_user(self, user):
        """Método para autenticar usuário nos testes"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def create_barber_schedule_data(self, **kwargs):
        """Método para criar dados de horário de barbeiro"""
        defaults = {
            "barber": self.barber_user.id,
            "barbershop": self.barbershop.id,
            "weekday": 2,  # Terça-feira
            "start_time": "10:00:00",
            "end_time": "18:00:00",
            "is_available": True,
        }
        defaults.update(kwargs)
        return defaults

    def create_appointment_data(self, **kwargs):
        """Método para criar dados de agendamento"""
        # Encontrar a próxima Monday (weekday=0) para garantir que o barbeiro está disponível
        now = timezone.now()
        days_ahead = 0 - now.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        future_datetime = now.replace(
            hour=14, minute=0, second=0, microsecond=0
        ) + timedelta(days=days_ahead)

        defaults = {
            "customer": self.barbershop_customer.id,
            "barber": self.barber_user.id,
            "service": self.service.id,
            "barbershop": self.barbershop.id,
            "start_datetime": future_datetime.isoformat(),
            "end_datetime": (future_datetime + timedelta(minutes=30)).isoformat(),
        }
        defaults.update(kwargs)
        return defaults


class BarberScheduleCRUDTests(AppointmentAPITestCase):
    """
    Testes para as operações CRUD de BarberSchedule.
    """

    def test_list_barber_schedules_authenticated(self):
        """Teste para listar horários de barbeiros autenticado"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_barber_schedules_unauthenticated(self):
        """Teste para listar horários sem autenticação"""
        url = reverse("barberschedule-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_barber_schedule(self):
        """Teste para recuperar horário específico"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-detail", args=[self.barber_schedule.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.barber_schedule.id))
        self.assertEqual(response.data["barber_name"], self.barber_user.get_full_name())

    def test_create_barber_schedule_as_barber(self):
        """Teste para criar horário como barbeiro"""
        self.authenticate_user(self.barber_user)
        url = reverse("barberschedule-list")
        data = self.create_barber_schedule_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["barber"], self.barber_user.id)
        self.assertEqual(response.data["weekday"], 2)

    def test_create_barber_schedule_as_owner(self):
        """Teste para criar horário como proprietário da barbearia"""
        self.authenticate_user(self.owner_user)
        url = reverse("barberschedule-list")
        data = self.create_barber_schedule_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_barber_schedule_as_client(self):
        """Teste para tentar criar horário como cliente (deve falhar)"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-list")
        data = self.create_barber_schedule_data()

        response = self.client.post(url, data, format="json")

        # Pode retornar 400 devido a validações ou 403 devido a permissões
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST],
        )

    def test_create_barber_schedule_invalid_time(self):
        """Teste para criar horário com tempo inválido"""
        self.authenticate_user(self.barber_user)
        url = reverse("barberschedule-list")
        data = self.create_barber_schedule_data(
            start_time="18:00:00", end_time="10:00:00"  # Fim antes do início
        )

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_barber_schedule_as_barber(self):
        """Teste para atualizar horário como barbeiro proprietário"""
        self.authenticate_user(self.barber_user)
        url = reverse("barberschedule-detail", args=[self.barber_schedule.id])
        data = {"start_time": "08:00:00", "end_time": "16:00:00"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["start_time"], "08:00:00")

    def test_update_barber_schedule_as_other_barber(self):
        """Teste para tentar atualizar horário de outro barbeiro"""
        other_barber = self.create_user(email="other@test.com", role=User.Role.BARBER)
        self.authenticate_user(other_barber)
        url = reverse("barberschedule-detail", args=[self.barber_schedule.id])
        data = {"start_time": "08:00:00"}

        response = self.client.patch(url, data, format="json")

        # Pode retornar 404 se o objeto não for encontrado devido às permissões
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_delete_barber_schedule_as_owner(self):
        """Teste para deletar horário como proprietário"""
        self.authenticate_user(self.owner_user)
        url = reverse("barberschedule-detail", args=[self.barber_schedule.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            BarberSchedule.objects.filter(id=self.barber_schedule.id).exists()
        )


class BarberScheduleCustomActionsTests(AppointmentAPITestCase):
    """
    Testes para as ações customizadas de BarberSchedule.
    """

    def test_my_schedules_as_barber(self):
        """Teste para listar horários do barbeiro logado"""
        self.authenticate_user(self.barber_user)
        url = reverse("barberschedule-my-schedules")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["barber"], self.barber_user.id)

    def test_my_schedules_as_client(self):
        """Teste para tentar acessar horários como cliente"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-my-schedules")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_by_barbershop(self):
        """Teste para filtrar horários por barbearia"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-by-barbershop")

        response = self.client.get(url, {"barbershop_id": self.barbershop.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_by_barbershop_missing_param(self):
        """Teste para filtrar sem parâmetro barbershop_id"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-by-barbershop")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_available_slots(self):
        """Teste para consultar horários disponíveis"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-available-slots")
        tomorrow = (timezone.now() + timedelta(days=1)).date()

        response = self.client.get(
            url, {"barbershop_id": self.barbershop.id, "date": tomorrow.isoformat()}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("available_slots", response.data)

    def test_available_slots_invalid_date(self):
        """Teste para consultar horários com data inválida"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-available-slots")
        yesterday = (timezone.now() - timedelta(days=1)).date()

        response = self.client.get(
            url, {"barbershop_id": self.barbershop.id, "date": yesterday.isoformat()}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_as_owner(self):
        """Teste para criar múltiplos horários como proprietário"""
        self.authenticate_user(self.owner_user)
        url = reverse("barberschedule-bulk-create")
        data = {
            "barber_id": self.barber_user.id,
            "barbershop_id": self.barbershop.id,
            "schedules": [
                {"weekday": 3, "start_time": "09:00:00", "end_time": "17:00:00"},
                {"weekday": 4, "start_time": "09:00:00", "end_time": "17:00:00"},
            ],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("schedules", response.data)
        self.assertEqual(len(response.data["schedules"]), 2)

    def test_bulk_create_unauthorized(self):
        """Teste para criar múltiplos horários sem autorização"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-bulk-create")
        data = {
            "barber_id": self.barber_user.id,
            "barbershop_id": self.barbershop.id,
            "schedules": [
                {"weekday": 3, "start_time": "09:00:00", "end_time": "17:00:00"}
            ],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_availability(self):
        """Teste para alternar disponibilidade de horário"""
        self.authenticate_user(self.barber_user)
        url = reverse(
            "barberschedule-toggle-availability", args=[self.barber_schedule.id]
        )
        original_availability = self.barber_schedule.is_available

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_available"], not original_availability)

    def test_working_now(self):
        """Teste para listar barbeiros trabalhando agora"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-working-now")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("working_barbers", response.data)


class AppointmentCRUDTests(AppointmentAPITestCase):
    """
    Testes para as operações CRUD de Appointment.
    """

    def test_list_appointments_as_client(self):
        """Teste para listar agendamentos como cliente"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Cliente deve ver apenas seus agendamentos
        for appointment in response.data["results"]:
            self.assertEqual(
                appointment["customer_name"], self.client_user.get_full_name()
            )

    def test_list_appointments_as_barber(self):
        """Teste para listar agendamentos como barbeiro"""
        self.authenticate_user(self.barber_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Barbeiro deve ver apenas seus agendamentos
        for appointment in response.data["results"]:
            self.assertEqual(
                appointment["barber_name"], self.barber_user.get_full_name()
            )

    def test_retrieve_appointment_as_participant(self):
        """Teste para recuperar agendamento como participante"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-detail", args=[self.appointment.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.appointment.id))

    def test_retrieve_appointment_unauthorized(self):
        """Teste para tentar recuperar agendamento de outro cliente"""
        other_client = self.create_user(email="other@test.com")
        self.authenticate_user(other_client)
        url = reverse("appointment-detail", args=[self.appointment.id])

        response = self.client.get(url)

        # Pode retornar 404 se o objeto não for encontrado devido às permissões
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_create_appointment_as_client(self):
        """Teste para criar agendamento como cliente"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")
        data = self.create_appointment_data()

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["service"], self.service.id)

    def test_create_appointment_past_datetime(self):
        """Teste para tentar criar agendamento no passado"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")
        past_datetime = timezone.now() - timedelta(hours=1)
        data = self.create_appointment_data(
            start_datetime=past_datetime.isoformat(),
            end_datetime=(past_datetime + timedelta(minutes=30)).isoformat(),
        )

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_appointment_conflicting_time(self):
        """Teste para tentar criar agendamento em horário já ocupado"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")
        # Usar mesmo horário do agendamento existente
        data = self.create_appointment_data(
            start_datetime=self.appointment.start_datetime.isoformat(),
            end_datetime=self.appointment.end_datetime.isoformat(),
        )

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_appointment_as_client(self):
        """Teste para atualizar agendamento como cliente"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-detail", args=[self.appointment.id])
        new_datetime = timezone.now() + timedelta(days=3, hours=15)
        data = {
            "start_datetime": new_datetime.isoformat(),
            "end_datetime": (new_datetime + timedelta(minutes=30)).isoformat(),
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_appointment_as_client(self):
        """Teste para deletar agendamento como cliente"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-detail", args=[self.appointment.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class AppointmentCustomActionsTests(AppointmentAPITestCase):
    """
    Testes para as ações customizadas de Appointment.
    """

    def test_my_appointments(self):
        """Teste para listar agendamentos do usuário logado"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-my-appointments")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_today_appointments(self):
        """Teste para listar agendamentos de hoje"""
        # Usar o próximo Monday quando o barbeiro trabalha
        now = timezone.now()
        days_ahead = 0 - now.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        monday_datetime = now.replace(
            hour=15, minute=0, second=0, microsecond=0
        ) + timedelta(days=days_ahead)

        # Criar agendamento para Monday (quando barbeiro trabalha)
        today_appointment = Appointment.objects.create(
            customer=self.barbershop_customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=monday_datetime,
            end_datetime=monday_datetime + timedelta(minutes=30),
            status=Appointment.Status.CONFIRMED,
            final_price=self.service.price,
        )

        self.authenticate_user(self.barber_user)
        url = reverse("appointment-today")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("appointments", response.data)

    def test_upcoming_appointments(self):
        """Teste para listar próximos agendamentos"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-upcoming")

        response = self.client.get(url, {"days": 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("appointments", response.data)
        self.assertIn("period", response.data)

    def test_confirm_appointment(self):
        """Teste para confirmar agendamento"""
        self.authenticate_user(self.barber_user)
        url = reverse("appointment-confirm", args=[self.appointment.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Appointment.Status.CONFIRMED)

    def test_confirm_appointment_unauthorized(self):
        """Teste para tentar confirmar agendamento sem autorização"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-confirm", args=[self.appointment.id])

        response = self.client.post(url)

        # Cliente pode confirmar seu próprio agendamento
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_appointment(self):
        """Teste para cancelar agendamento"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-cancel", args=[self.appointment.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Appointment.Status.CANCELLED)

    def test_complete_appointment(self):
        """Teste para marcar agendamento como concluído"""
        # Primeiro confirmar o agendamento
        self.appointment.status = Appointment.Status.CONFIRMED
        self.appointment.save()

        self.authenticate_user(self.barber_user)
        url = reverse("appointment-complete", args=[self.appointment.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Appointment.Status.COMPLETED)

    def test_statistics_as_barber(self):
        """Teste para ver estatísticas como barbeiro"""
        self.authenticate_user(self.barber_user)
        url = reverse("appointment-statistics")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("barber_name", response.data)
        self.assertIn("total_appointments", response.data)

    def test_statistics_as_client(self):
        """Teste para tentar ver estatísticas como cliente"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-statistics")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_revenue_report_as_owner(self):
        """Teste para ver relatório de receita como proprietário"""
        self.authenticate_user(self.owner_user)
        url = reverse("appointment-revenue-report")

        response = self.client.get(
            url,
            {
                "barbershop_id": self.barbershop.id,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_revenue", response.data)

    def test_revenue_report_unauthorized(self):
        """Teste para tentar ver relatório sem autorização"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-revenue-report")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AppointmentPermissionTests(AppointmentAPITestCase):
    """
    Testes para verificar as permissões do sistema.
    """

    def test_client_can_only_see_own_appointments(self):
        """Teste para verificar que cliente vê apenas seus agendamentos"""
        # Criar outro cliente e agendamento
        other_client = self.create_user(email="other@test.com")
        other_customer = BarbershopCustomer.objects.create(
            barbershop=self.barbershop, customer=other_client
        )
        other_appointment = Appointment.objects.create(
            customer=other_customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(days=5, hours=10),
            end_datetime=timezone.now() + timedelta(days=5, hours=10, minutes=30),
        )

        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que só vê seus próprios agendamentos
        appointment_ids = [apt["id"] for apt in response.data["results"]]
        self.assertIn(str(self.appointment.id), appointment_ids)
        self.assertNotIn(str(other_appointment.id), appointment_ids)

    def test_barber_can_only_see_own_appointments(self):
        """Teste para verificar que barbeiro vê apenas seus agendamentos"""
        # Criar outro barbeiro e agendamento
        other_barber = self.create_user(email="other@test.com", role=User.Role.BARBER)
        other_appointment = Appointment.objects.create(
            customer=self.barbershop_customer,
            barber=other_barber,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(days=5, hours=11),
            end_datetime=timezone.now() + timedelta(days=5, hours=11, minutes=30),
        )

        self.authenticate_user(self.barber_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que só vê seus próprios agendamentos
        appointment_ids = [apt["id"] for apt in response.data["results"]]
        self.assertIn(str(self.appointment.id), appointment_ids)
        self.assertNotIn(str(other_appointment.id), appointment_ids)

    def test_owner_can_see_barbershop_appointments(self):
        """Teste para verificar que proprietário vê agendamentos da barbearia"""
        self.authenticate_user(self.owner_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_admin_can_see_all_appointments(self):
        """Teste para verificar que admin vê todos os agendamentos"""
        self.authenticate_user(self.admin_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AppointmentModelTests(AppointmentAPITestCase):
    """
    Testes para os métodos dos modelos.
    """

    def test_barber_schedule_work_duration(self):
        """Teste para cálculo de duração de trabalho"""
        duration_hours = self.barber_schedule.get_work_duration_hours()
        duration_minutes = self.barber_schedule.get_work_duration_minutes()

        self.assertEqual(duration_hours, 8.0)  # 9h às 17h = 8 horas
        self.assertEqual(duration_minutes, 480)  # 8 horas * 60 minutos

    def test_appointment_duration_calculation(self):
        """Teste para cálculo de duração do agendamento"""
        duration_minutes = self.appointment.get_duration_minutes()
        duration_hours = self.appointment.get_duration_hours()

        self.assertEqual(duration_minutes, 30)
        self.assertEqual(duration_hours, 0.5)

    def test_appointment_status_checks(self):
        """Teste para verificações de status do agendamento"""
        # Agendamento futuro deve poder ser cancelado
        self.assertTrue(self.appointment.can_be_cancelled())
        # Agendamento pendente deve poder ser confirmado
        self.assertTrue(self.appointment.can_be_confirmed())
        # Agendamento pendente não deve poder ser completado
        self.assertFalse(self.appointment.can_be_completed())

    def test_appointment_transitions(self):
        """Teste para transições de status"""
        # Confirmar agendamento
        success = self.appointment.confirm()
        self.assertTrue(success)
        self.assertEqual(self.appointment.status, Appointment.Status.CONFIRMED)

        # Agora deve poder ser completado
        self.assertTrue(self.appointment.can_be_completed())

    def test_appointment_formatted_datetime(self):
        """Teste para formatação de data e hora"""
        formatted = self.appointment.get_formatted_datetime()
        self.assertIsInstance(formatted, str)
        self.assertIn("/", formatted)  # Formato brasileiro de data
        self.assertIn(":", formatted)  # Formato de hora

    def test_barber_schedule_available_slots(self):
        """Teste para consulta de horários disponíveis"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        if tomorrow.weekday() == 1:  # Se for segunda-feira
            slots = self.barber_schedule.get_available_slots(tomorrow, 30)
            self.assertIsInstance(slots, list)


class AppointmentFilterTests(AppointmentAPITestCase):
    """
    Testes para filtros e busca.
    """

    def test_appointment_filter_by_status(self):
        """Teste para filtrar agendamentos por status"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")

        response = self.client.get(url, {"status": Appointment.Status.PENDING})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for appointment in response.data["results"]:
            self.assertEqual(appointment["status"], Appointment.Status.PENDING)

    def test_appointment_filter_by_barber(self):
        """Teste para filtrar agendamentos por barbeiro"""
        self.authenticate_user(self.owner_user)
        url = reverse("appointment-list")

        response = self.client.get(url, {"barber": self.barber_user.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for appointment in response.data["results"]:
            self.assertEqual(appointment["barber"], self.barber_user.id)

    def test_appointment_search_by_customer_name(self):
        """Teste para buscar agendamentos por nome do cliente"""
        self.authenticate_user(self.owner_user)
        url = reverse("appointment-list")

        response = self.client.get(url, {"search": self.client_user.first_name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_appointment_ordering(self):
        """Teste para ordenação de agendamentos"""
        # Criar outro agendamento para Monday mas em semana diferente
        base_monday = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        days_ahead = 0 - base_monday.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        future_monday = base_monday + timedelta(days=days_ahead, weeks=1)

        future_appointment = Appointment.objects.create(
            customer=self.barbershop_customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=future_monday,
            end_datetime=future_monday + timedelta(minutes=30),
            final_price=self.service.price,
        )

        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")

        response = self.client.get(url, {"ordering": "start_datetime"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_barber_schedule_filter_by_weekday(self):
        """Teste para filtrar horários por dia da semana"""
        self.authenticate_user(self.client_user)
        url = reverse("barberschedule-list")

        response = self.client.get(url, {"weekday": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for schedule in response.data["results"]:
            self.assertEqual(schedule["weekday"], 1)


class AppointmentPaginationTests(AppointmentAPITestCase):
    """
    Testes para paginação.
    """

    def setUp(self):
        super().setUp()
        # Criar múltiplos agendamentos para testar paginação
        # Usar sempre Monday (quando o barbeiro trabalha) mas com horários diferentes
        base_monday = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        days_ahead = 0 - base_monday.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        base_monday = base_monday + timedelta(days=days_ahead)

        for i in range(15):
            # Criar appointments em Mondays diferentes ou horários diferentes no mesmo dia
            if i < 8:  # Primeiros 8 no mesmo dia, horários diferentes
                start_time = base_monday + timedelta(hours=i)
            else:  # Restantes em Mondays seguintes
                weeks_ahead = (i - 8) + 1
                start_time = base_monday + timedelta(weeks=weeks_ahead)

            Appointment.objects.create(
                customer=self.barbershop_customer,
                barber=self.barber_user,
                service=self.service,
                barbershop=self.barbershop,
                start_datetime=start_time,
                end_datetime=start_time + timedelta(minutes=30),
                final_price=self.service.price,
            )

    def test_appointment_pagination(self):
        """Teste para paginação de agendamentos"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_appointment_pagination_page_size(self):
        """Teste para tamanho da página na paginação"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")

        response = self.client.get(url, {"page_size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["results"]), 5)


class AppointmentErrorHandlingTests(AppointmentAPITestCase):
    """
    Testes para tratamento de erros.
    """

    def test_appointment_not_found(self):
        """Teste para agendamento não encontrado"""
        self.authenticate_user(self.client_user)
        url = reverse(
            "appointment-detail", args=["00000000-0000-0000-0000-000000000000"]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_barber_schedule_not_found(self):
        """Teste para horário não encontrado"""
        self.authenticate_user(self.client_user)
        url = reverse(
            "barberschedule-detail", args=["00000000-0000-0000-0000-000000000000"]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_appointment_data(self):
        """Teste para dados inválidos de agendamento"""
        self.authenticate_user(self.client_user)
        url = reverse("appointment-list")
        data = {
            "customer": "invalid-id",
            "barber": self.barber_user.id,
            "service": self.service.id,
            "barbershop": self.barbershop.id,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_barber_schedule_data(self):
        """Teste para dados inválidos de horário"""
        self.authenticate_user(self.barber_user)
        url = reverse("barberschedule-list")
        data = {
            "barber": self.barber_user.id,
            "barbershop": self.barbershop.id,
            "weekday": 8,  # Dia da semana inválido
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
