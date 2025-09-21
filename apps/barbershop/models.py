from functools import partial
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from utils.file_uploads import encrypted_filename


# Create your models here.
class Barbershop(models.Model):
    class Meta:
        verbose_name = "Barbearia"
        verbose_name_plural = "Barbearias"
        ordering = ["name"]
        db_table = "barbershops"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    name = models.CharField(max_length=255, unique=True, verbose_name="Nome")
    description = models.TextField(null=True, blank=True, verbose_name="Descrição")
    cnpj = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name="CNPJ"
    )
    address = models.CharField(max_length=255, verbose_name="Endereço")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="Email")
    phone = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Telefone"
    )
    website = models.URLField(null=True, blank=True, verbose_name="Website")
    logo = models.ImageField(
        upload_to=partial(
            encrypted_filename,
            base_folder="logos",
            app_name=True,
            default_subfolder="barbershops",
        ),
        null=True,
        blank=True,
        verbose_name="Logo",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="barbershops",
        verbose_name="Proprietário",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return self.name

    def get_total_services(self):
        """Retorna o total de serviços da barbearia"""
        return self.services.count()

    def get_available_services(self):
        """Retorna apenas os serviços disponíveis"""
        return self.services.filter(available=True)

    def get_average_service_price(self):
        """Retorna o preço médio dos serviços"""
        return self.services.aggregate(avg_price=Avg("price"))["avg_price"] or 0

    def get_total_customers(self):
        """Retorna o total de clientes da barbearia"""
        return self.barbershop_customers.count()

    def get_total_appointments(self):
        """Retorna o total de agendamentos da barbearia"""
        return self.appointments.count()

    def get_total_revenue(self, start_date=None, end_date=None):
        """Retorna a receita total da barbearia"""

    def get_total_revenue(self, start_date=None, end_date=None):
        """Retorna a receita total da barbearia"""
        from apps.payment.models import Payment

        payments = Payment.objects.filter(
            appointment__barbershop=self, status=Payment.Status.PAID
        )
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)

        return payments.aggregate(total=models.Sum("amount"))["total"] or 0
        """Verifica se a barbearia tem logo"""
        return bool(self.logo)

    def has_contact_info(self):
        """Verifica se tem informações de contato"""
        return bool(self.email or self.phone)

    def get_formatted_cnpj(self):
        """Retorna CNPJ formatado"""
        if not self.cnpj:
            return None
        cnpj = self.cnpj.replace(".", "").replace("/", "").replace("-", "")
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"

    def get_formatted_phone(self):
        """Retorna telefone formatado"""
        if not self.phone:
            return None
        phone = "".join(filter(str.isdigit, self.phone))
        if len(phone) == 11:
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        elif len(phone) == 10:
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        return self.phone

    def get_recent_customers(self, limit=10):
        """Retorna os clientes mais recentes"""
        return self.barbershop_customers.order_by("-last_visit")[:limit]

    def get_most_popular_services(self, limit=5):
        """Retorna os serviços mais populares baseado em agendamentos"""
        return self.services.annotate(appointment_count=Count("appointments")).order_by(
            "-appointment_count"
        )[:limit]

    @classmethod
    @classmethod
    def get_top_revenue_barbershops(cls, limit=10):
        """Retorna as barbearias com maior receita"""
        from apps.payment.models import Payment

        return cls.objects.annotate(
            total_revenue=Sum(
                "appointments__payment__amount",
                filter=models.Q(appointments__payment__status=Payment.Status.PAID),
            )
        ).order_by("-total_revenue")[:limit]


class Service(models.Model):
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["barbershop", "name"]
        db_table = "services"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Barbearia",
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    description = models.TextField(null=True, blank=True, verbose_name="Descrição")
    image = models.ImageField(
        upload_to=partial(
            encrypted_filename,
            base_folder="services",
            app_name=True,
            default_subfolder="barbershops",
        ),
        null=True,
        blank=True,
        verbose_name="Imagem",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    duration = models.DurationField(verbose_name="Duração")
    available = models.BooleanField(default=True, verbose_name="Disponível")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return self.name

    def get_formatted_price(self):
        """Retorna o preço formatado"""
        return f"R$ {self.price:.2f}"

    def get_duration_in_minutes(self):
        """Retorna a duração em minutos"""
        return int(self.duration.total_seconds() / 60)

    def get_formatted_duration(self):
        """Retorna a duração formatada"""
        minutes = self.get_duration_in_minutes()
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return f"{hours}h{mins:02d}min" if mins > 0 else f"{hours}h"
        return f"{mins}min"

    def get_total_appointments(self):
        """Retorna o total de agendamentos do serviço"""
        return self.appointments.count()

    def get_total_revenue(self, start_date=None, end_date=None):
        """Retorna a receita total do serviço"""
        from apps.payment.models import Payment

        appointments = self.appointments.filter(payment__status=Payment.Status.PAID)
        if start_date:
            appointments = appointments.filter(date__gte=start_date)
        if end_date:
            appointments = appointments.filter(date__lte=end_date)

        return appointments.aggregate(total=models.Sum("payment__amount"))["total"] or 0

    def get_average_rating(self):
        """Retorna a avaliação média do serviço"""
        return self.appointments.aggregate(avg_rating=Avg("rating"))["avg_rating"] or 0

    def is_popular(self):
        """Verifica se é um serviço popular (mais de 10 agendamentos)"""
        return self.get_total_appointments() > 10

    def has_description(self):
        """Verifica se tem descrição"""
        return bool(self.description)

    def toggle_availability(self):
        """Alterna disponibilidade do serviço"""
        self.available = not self.available
        self.save(update_fields=["available"])

    @classmethod
    def get_most_expensive(cls, barbershop=None):
        """Retorna os serviços mais caros"""
        queryset = cls.objects.all()
        if barbershop:
            queryset = queryset.filter(barbershop=barbershop)
        return queryset.order_by("-price")

    @classmethod
    def get_available_services(cls, barbershop=None):
        """Retorna apenas serviços disponíveis"""
        queryset = cls.objects.filter(available=True)
        if barbershop:
            queryset = queryset.filter(barbershop=barbershop)
        return queryset


class BarbershopCustomer(models.Model):
    class Meta:
        verbose_name = "Cliente da Barbearia"
        verbose_name_plural = "Clientes da Barbearia"
        unique_together = ["customer", "barbershop"]
        ordering = ["-last_visit"]
        db_table = "barbershop_customers"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="barbershop_customers",
        verbose_name="Cliente",
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name="barbershop_customers",
        verbose_name="Barbearia",
    )
    last_visit = models.DateTimeField(
        null=True, blank=True, verbose_name="Última Visita"
    )

    def __str__(self):
        return self.customer.get_full_name() or self.customer.username

    def get_total_appointments(self):
        """Retorna o total de agendamentos do cliente nesta barbearia"""
        if not self.customer:
            return 0
        return self.barbershop.appointments.filter(customer=self.customer).count()

    def get_total_spent(self):
        """Retorna o total gasto pelo cliente nesta barbearia"""
        if not self.customer:
            return 0
        from apps.payment.models import Payment

        return (
            Payment.objects.filter(
                appointment__customer=self.customer,
                appointment__barbershop=self.barbershop,
                status=Payment.Status.PAID,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

    def get_favorite_services(self, limit=3):
        """Retorna os serviços mais utilizados pelo cliente"""
        if not self.customer:
            return Service.objects.none()
        return (
            Service.objects.filter(
                appointments__customer=self.customer,
                appointments__barbershop=self.barbershop,
            )
            .annotate(usage_count=Count("appointments"))
            .order_by("-usage_count")[:limit]
        )

    def get_average_rating_given(self):
        """Retorna a média das avaliações dadas pelo cliente"""
        if not self.customer:
            return 0
        return (
            self.barbershop.appointments.filter(
                customer=self.customer, rating__isnull=False
            ).aggregate(avg_rating=Avg("rating"))["avg_rating"]
            or 0
        )

    def is_frequent_customer(self, min_visits=5):
        """Verifica se é um cliente frequente"""
        return self.get_total_appointments() >= min_visits

    def is_vip_customer(self, min_spent=500):
        """Verifica se é um cliente VIP baseado no valor gasto"""
        return self.get_total_spent() >= min_spent

    def days_since_last_visit(self):
        """Retorna quantos dias desde a última visita"""
        if not self.last_visit:
            return None
        return (timezone.now() - self.last_visit).days

    def is_active_customer(self, days_threshold=90):
        """Verifica se é um cliente ativo (visitou nos últimos X dias)"""
        days_since = self.days_since_last_visit()
        return days_since is not None and days_since <= days_threshold

    def get_customer_tier(self):
        """Retorna o tier do cliente baseado em gastos"""
        total_spent = self.get_total_spent()
        if total_spent >= 1000:
            return "Platinum"
        elif total_spent >= 500:
            return "Gold"
        elif total_spent >= 200:
            return "Silver"
        elif total_spent > 0:
            return "Bronze"
        return "New"

    def update_last_visit(self):
        """Atualiza a data da última visita para agora"""
        self.last_visit = timezone.now()

    @classmethod
    def get_vip_customers(cls, barbershop, min_spent=500):
        """Retorna clientes VIP de uma barbearia"""
        from apps.payment.models import Payment

        return cls.objects.filter(barbershop=barbershop).annotate(
            total_spent=Sum(
                "barbershop__appointments__payment__amount",
                filter=models.Q(
                    barbershop__appointments__customer=models.F("customer"),
                    barbershop__appointments__payment__status=Payment.Status.PAID,
                ),
            )
        )

    @classmethod
    def get_inactive_customers(cls, barbershop, days_threshold=90):
        """Retorna clientes inativos de uma barbearia"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_threshold)
        return cls.objects.filter(barbershop=barbershop, last_visit__lt=cutoff_date)
