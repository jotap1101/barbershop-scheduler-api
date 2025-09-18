from django.db import models
from django.conf import settings
from uuid import uuid4


class Barbershop(models.Model):
    class Meta:
        verbose_name = "Barbearia"
        verbose_name_plural = "Barbearias"
        ordering = ["name"]

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
        upload_to="barbershops/logos/", null=True, blank=True, verbose_name="Logo"
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


class Service(models.Model):
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["barbershop", "name"]

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
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    duration = models.DurationField(verbose_name="Duração")
    available = models.BooleanField(default=True, verbose_name="Disponível")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return self.name


class BarbershopCustomer(models.Model):
    class Meta:
        verbose_name = "Cliente da Barbearia"
        verbose_name_plural = "Clientes da Barbearia"
        unique_together = ["customer", "barbershop"]
        ordering = ["-last_visit"]

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
