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
