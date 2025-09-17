from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.barbershops.models import Barbershop, Service, BarbershopCustomer

class BarberSchedule(models.Model):
    class WeekDay(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name='barber_schedules'
    )
    weekday = models.IntegerField(choices=WeekDay.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time')

    def __str__(self):
        return f"{self.barber.get_full_name()} - {self.get_weekday_display()}"

    class Meta:
        verbose_name = 'Barber Schedule'
        verbose_name_plural = 'Barber Schedules'
        unique_together = ['barber', 'barbershop', 'weekday']
        ordering = ['weekday', 'start_time']


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    customer = models.ForeignKey(
        BarbershopCustomer,
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='barber_appointments'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError('Start time must be before end time')

    def save(self, *args, **kwargs):
        if not self.final_price:
            self.final_price = self.service.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.customer.get_full_name()} - {self.service.name} with {self.barber.get_full_name()}"

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-start_datetime']
