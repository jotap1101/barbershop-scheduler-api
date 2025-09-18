from django.db import models
from apps.appointments.models import Appointment
from uuid import uuid4


class Payment(models.Model):
    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]

    class Method(models.TextChoices):
        PIX = "PIX", "Pix"
        CREDIT_CARD = "CREDIT_CARD", "Cartão de Crédito"
        DEBIT_CARD = "DEBIT_CARD", "Cartão de Débito"
        CASH = "CASH", "Dinheiro"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        PAID = "PAID", "Pago"
        REFUNDED = "REFUNDED", "Reembolsado"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name="payment",
        verbose_name="Agendamento",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    method = models.CharField(
        max_length=5,
        choices=Method.choices,
        default=Method.PIX,
        verbose_name="Método de Pagamento",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status do Pagamento",
    )
    transaction_id = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="ID da Transação"
    )
    payment_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Data do Pagamento"
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return f"Pagamento {self.id} - {self.get_status_display()}"
