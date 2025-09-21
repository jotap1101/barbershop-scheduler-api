from uuid import uuid4

from django.db import models
from django.utils import timezone

from apps.appointment.models import Appointment


# Create your models here.
class Payment(models.Model):
    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]
        db_table = "payments"

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
        max_length=15,
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
    transaction_id = models.UUIDField(
        default=uuid4,
        editable=False,
        null=True,
        blank=True,
        verbose_name="ID da Transação",
    )
    payment_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Data do Pagamento"
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = uuid4()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento {self.id} - {self.get_status_display()}"

    def is_paid(self):
        """Verifica se o pagamento foi realizado"""
        return self.status == self.Status.PAID

    def is_pending(self):
        """Verifica se o pagamento está pendente"""
        return self.status == self.Status.PENDING

    def is_refunded(self):
        """Verifica se o pagamento foi reembolsado"""
        return self.status == self.Status.REFUNDED

    def is_card_payment(self):
        """Verifica se o pagamento foi realizado com cartão"""
        return self.method in [self.Method.CREDIT_CARD, self.Method.DEBIT_CARD]

    def is_cash_payment(self):
        """Verifica se o pagamento foi em dinheiro"""
        return self.method == self.Method.CASH

    def is_digital_payment(self):
        """Verifica se é um pagamento digital"""
        return self.method in [
            self.Method.PIX,
            self.Method.CREDIT_CARD,
            self.Method.DEBIT_CARD,
        ]

    def get_formatted_amount(self):
        """Retorna o valor formatado em reais"""
        return (
            f"R$ {self.amount:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    def get_customer_name(self):
        """Retorna o nome do cliente do agendamento"""
        return self.appointment.customer.get_display_name()

    def get_service_name(self):
        """Retorna o nome do serviço do agendamento"""
        return self.appointment.service.name

    def get_barbershop_name(self):
        """Retorna o nome da barbearia"""
        return self.appointment.barbershop.name

    def has_transaction_id(self):
        """Verifica se o pagamento possui ID de transação"""
        return bool(self.transaction_id and self.transaction_id.strip())

    def get_payment_age_days(self):
        """Retorna quantos dias se passaram desde o pagamento"""
        if not self.payment_date:
            return None
        return (timezone.now() - self.payment_date).days

    def mark_as_paid(self, transaction_id=None):
        """Marca o pagamento como pago"""
        self.status = self.Status.PAID
        self.payment_date = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    def mark_as_refunded(self):
        """Marca o pagamento como reembolsado"""
        self.status = self.Status.REFUNDED
        self.save()

    @classmethod
    def get_total_revenue(cls, start_date=None, end_date=None):
        """Calcula a receita total dos pagamentos confirmados"""
        queryset = cls.objects.filter(status=cls.Status.PAID)
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        return queryset.aggregate(total=models.Sum("amount"))["total"] or 0

    @classmethod
    def get_revenue_by_method(cls, start_date=None, end_date=None):
        """Retorna a receita agrupada por método de pagamento"""
        queryset = cls.objects.filter(status=cls.Status.PAID)
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        return queryset.values("method").annotate(
            total=models.Sum("amount"), count=models.Count("id")
        )

    def get_method_display_icon(self):
        """Retorna um ícone para o método de pagamento"""
        icons = {
            self.Method.PIX: "💳",
            self.Method.CREDIT_CARD: "💳",
            self.Method.DEBIT_CARD: "💳",
            self.Method.CASH: "💰",
        }
        return icons.get(self.method, "💸")

    def get_status_display_icon(self):
        """Retorna um ícone para o status do pagamento"""
        icons = {
            self.Status.PENDING: "⏳",
            self.Status.PAID: "✅",
            self.Status.REFUNDED: "↩️",
        }
        return icons.get(self.status, "❓")
