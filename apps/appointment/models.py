from datetime import date, datetime, timedelta
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.barbershop.models import Barbershop, BarbershopCustomer, Service


# Create your models here.
class BarberSchedule(models.Model):
    class Meta:
        verbose_name = "Agenda do Barbeiro"
        verbose_name_plural = "Agendas dos Barbeiros"
        unique_together = ["barber", "barbershop"]
        ordering = ["weekday", "start_time"]
        db_table = "barber_schedules"

    class WeekDay(models.IntegerChoices):
        SUNDAY = 0, "Domingo"
        MONDAY = 1, "Segunda-feira"
        TUESDAY = 2, "Terça-feira"
        WEDNESDAY = 3, "Quarta-feira"
        THURSDAY = 4, "Quinta-feira"
        FRIDAY = 5, "Sexta-feira"
        SATURDAY = 6, "Sábado"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="barber_schedules",
        verbose_name="Barbeiro",
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name="barber_schedules",
        verbose_name="Barbearia",
    )
    weekday = models.IntegerField(choices=WeekDay.choices, verbose_name="Dia da Semana")
    start_time = models.TimeField(verbose_name="Hora de Início")
    end_time = models.TimeField(verbose_name="Hora de Término")
    is_available = models.BooleanField(default=True, verbose_name="Disponível")

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("A hora de início deve ser antes da hora de término")

    def __str__(self):
        return f"{self.barber.get_full_name()} - {self.get_weekday_display()}"

    def get_work_duration_hours(self):
        """Retorna a duração do trabalho em horas"""
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        return (end - start).total_seconds() / 3600

    def get_work_duration_minutes(self):
        """Retorna a duração do trabalho em minutos"""
        return int(self.get_work_duration_hours() * 60)

    def is_working_now(self):
        """Verifica se o barbeiro está trabalhando agora"""
        now = datetime.now()
        if now.weekday() + 1 == self.weekday and self.is_available:
            current_time = now.time()
            return self.start_time <= current_time <= self.end_time
        return False

    def get_available_slots(self, date, service_duration_minutes=30):
        """Retorna os horários disponíveis para um dia específico"""

        if not self.is_available or date.weekday() != self.weekday:
            return []

        # Buscar agendamentos existentes para esse dia
        existing_appointments = Appointment.objects.filter(
            barber=self.barber,
            barbershop=self.barbershop,
            start_datetime__date=date,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).order_by("start_datetime")

        slots = []
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        slot_duration = timedelta(minutes=service_duration_minutes)

        for appointment in existing_appointments:
            # Adicionar slots até o início do agendamento
            while current_time + slot_duration <= appointment.start_datetime:
                slots.append(current_time.time())
                current_time += slot_duration

            # Pular para depois do agendamento
            current_time = appointment.end_datetime

        # Adicionar slots restantes até o fim do horário
        while current_time + slot_duration <= end_time:
            slots.append(current_time.time())
            current_time += slot_duration

        return slots

    def has_appointment_at(self, datetime):
        """Verifica se há agendamento em um horário específico"""
        return Appointment.objects.filter(
            barber=self.barber,
            barbershop=self.barbershop,
            start_datetime__lte=datetime,
            end_datetime__gt=datetime,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).exists()

    def get_next_available_slot(self, service_duration_minutes=30):
        """Retorna o próximo horário disponível"""

        today = datetime.now().date()
        for i in range(7):  # Verificar próximos 7 dias
            check_date = today + timedelta(days=i)
            if check_date.weekday() == self.weekday:
                slots = self.get_available_slots(check_date, service_duration_minutes)
                if slots:
                    return datetime.combine(check_date, slots[0])
        return None

    def get_appointments_count_today(self):
        """Retorna o número de agendamentos para hoje"""
        return Appointment.objects.filter(
            barber=self.barber,
            barbershop=self.barbershop,
            start_datetime__date=date.today(),
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).count()

    def is_fully_booked_today(self, service_duration_minutes=30):
        """Verifica se o barbeiro está totalmente ocupado hoje"""
        if date.today().weekday() != self.weekday:
            return False
        return (
            len(self.get_available_slots(date.today(), service_duration_minutes)) == 0
        )

    @classmethod
    def get_available_barbers(cls, barbershop, weekday, time):
        """Retorna barbeiros disponíveis em um horário específico"""
        return cls.objects.filter(
            barbershop=barbershop,
            weekday=weekday,
            start_time__lte=time,
            end_time__gt=time,
            is_available=True,
        )


class Appointment(models.Model):
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        unique_together = ["customer", "barber", "service", "barbershop"]
        ordering = ["-start_datetime"]
        db_table = "appointments"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        CONFIRMED = "CONFIRMED", "Confirmado"
        COMPLETED = "COMPLETED", "Concluído"
        CANCELLED = "CANCELLED", "Cancelado"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    customer = models.ForeignKey(
        BarbershopCustomer,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Cliente",
    )
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="barber_appointments",
        verbose_name="Barbeiro",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Serviço",
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Barbearia",
    )
    start_datetime = models.DateTimeField(verbose_name="Data e Hora de Início")
    end_datetime = models.DateTimeField(verbose_name="Data e Hora de Término")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Preço Final",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError(
                "A data e hora de início devem ser antes da data e hora de término"
            )

    def save(self, *args, **kwargs):
        if not self.final_price:
            self.final_price = self.service.price

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.customer.get_full_name()} - {self.service.name} com {self.barber.get_full_name()}"

    def get_duration_minutes(self):
        """Retorna a duração do agendamento em minutos"""
        return int((self.end_datetime - self.start_datetime).total_seconds() / 60)

    def get_duration_hours(self):
        """Retorna a duração do agendamento em horas"""
        return self.get_duration_minutes() / 60

    def is_today(self):
        """Verifica se o agendamento é hoje"""
        return self.start_datetime.date() == date.today()

    def is_past(self):
        """Verifica se o agendamento já passou"""
        return self.end_datetime < datetime.now()

    def is_upcoming(self):
        """Verifica se o agendamento é futuro"""
        return self.start_datetime > datetime.now()

    def is_in_progress(self):
        """Verifica se o agendamento está em andamento"""
        now = datetime.now()
        return self.start_datetime <= now <= self.end_datetime

    def can_be_cancelled(self):
        """Verifica se o agendamento pode ser cancelado"""
        return (
            self.status in [self.Status.PENDING, self.Status.CONFIRMED]
            and not self.is_past()
        )

    def can_be_confirmed(self):
        """Verifica se o agendamento pode ser confirmado"""
        return self.status == self.Status.PENDING and not self.is_past()

    def can_be_completed(self):
        """Verifica se o agendamento pode ser marcado como concluído"""
        return self.status == self.Status.CONFIRMED and (
            self.is_past() or self.is_in_progress()
        )

    def cancel(self):
        """Cancela o agendamento"""
        if self.can_be_cancelled():
            self.status = self.Status.CANCELLED
            self.save()
            return True
        return False

    def confirm(self):
        """Confirma o agendamento"""
        if self.can_be_confirmed():
            self.status = self.Status.CONFIRMED
            self.save()
            return True
        return False

    def complete(self):
        """Marca o agendamento como concluído"""
        if self.can_be_completed():
            self.status = self.Status.COMPLETED
            self.save()
            return True
        return False

    def get_time_until_appointment(self):
        """Retorna o tempo até o agendamento"""
        if self.is_past():
            return None
        return self.start_datetime - datetime.now()

    def get_formatted_datetime(self):
        """Retorna data e hora formatadas"""
        return self.start_datetime.strftime("%d/%m/%Y às %H:%M")

    def get_formatted_date(self):
        """Retorna apenas a data formatada"""
        return self.start_datetime.strftime("%d/%m/%Y")

    def get_formatted_time(self):
        """Retorna apenas o horário formatado"""
        return f"{self.start_datetime.strftime('%H:%M')} - {self.end_datetime.strftime('%H:%M')}"

    @classmethod
    def get_today_appointments(cls, barber=None, barbershop=None):
        """Retorna agendamentos de hoje"""
        queryset = cls.objects.filter(start_datetime__date=date.today())
        if barber:
            queryset = queryset.filter(barber=barber)
        if barbershop:
            queryset = queryset.filter(barbershop=barbershop)
        return queryset

    @classmethod
    def get_upcoming_appointments(cls, barber=None, barbershop=None, days=7):
        """Retorna agendamentos futuros"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        queryset = cls.objects.filter(
            start_datetime__gte=start_date, start_datetime__lte=end_date
        )
        if barber:
            queryset = queryset.filter(barber=barber)
        if barbershop:
            queryset = queryset.filter(barbershop=barbershop)
        return queryset

    @classmethod
    def get_revenue_by_period(cls, start_date, end_date, barbershop=None):
        """Retorna a receita de um período"""
        queryset = cls.objects.filter(
            start_datetime__date__gte=start_date,
            start_datetime__date__lte=end_date,
            status=cls.Status.COMPLETED,
        )
        if barbershop:
            queryset = queryset.filter(barbershop=barbershop)
        return queryset.aggregate(total=models.Sum("final_price"))["total"] or 0
