from django.db import models
from uuid import uuid4
from apps.barbershops.models import BarbershopCustomer, Service, Barbershop
from django.conf import settings


class Review(models.Model):
    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        unique_together = ("barbershop_customer", "barber", "service", "barbershop")
        ordering = ["-created_at"]

    class Rating(models.IntegerChoices):
        ONE = 1, "1 Estrela"
        TWO = 2, "2 Estrelas"
        THREE = 3, "3 Estrelas"
        FOUR = 4, "4 Estrelas"
        FIVE = 5, "5 Estrelas"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    barbershop_customer = models.ForeignKey(
        BarbershopCustomer,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Cliente da Barbearia",
    )
    barber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Barbeiro",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Serviço",
    )
    barbershop = models.ForeignKey(
        Barbershop,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Barbearia",
    )
    rating = models.PositiveSmallIntegerField(
        choices=Rating.choices, verbose_name="Avaliação"
    )
    comment = models.TextField(null=True, blank=True, verbose_name="Comentário")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    def __str__(self):
        return f"{self.barbershop_customer} - {self.barber} - {self.service} - {self.rating} - {self.comment} - {self.created_at}"
