from django.db import models
from django.conf import settings

class Barbershop(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_barbershops'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Barbershop'
        verbose_name_plural = 'Barbershops'
        ordering = ['name']


class Service(models.Model):
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name='services'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text='Duration in minutes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} at {self.barbershop.name}"

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['barbershop', 'name']


class Barber(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='barber_profile'
    )
    barbershops = models.ManyToManyField(
        Barbershop,
        related_name='barbers'
    )
    specialties = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Barber"

    class Meta:
        verbose_name = 'Barber'
        verbose_name_plural = 'Barbers'
        ordering = ['user__first_name', 'user__last_name']


class BarbershopCustomer(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customer_barbershops'
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name='customers'
    )
    loyalty_points = models.PositiveIntegerField(default=0)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer.get_full_name()} at {self.barbershop.name}"

    class Meta:
        verbose_name = 'Barbershop Customer'
        verbose_name_plural = 'Barbershop Customers'
        unique_together = ['customer', 'barbershop']
        ordering = ['-date_joined']
