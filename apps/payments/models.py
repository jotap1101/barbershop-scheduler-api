from django.db import models
from apps.appointments.models import Appointment

class Payment(models.Model):
    class Method(models.TextChoices):
        PIX = 'PIX', 'Pix'
        CARD = 'CARD', 'Card'
        CASH = 'CASH', 'Cash'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        REFUNDED = 'REFUNDED', 'Refunded'

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name='payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(
        max_length=5,
        choices=Method.choices,
        default=Method.PIX
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.appointment}"

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
