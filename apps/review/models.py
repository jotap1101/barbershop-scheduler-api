from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.barbershop.models import Barbershop, BarbershopCustomer, Service


# Create your models here.
class Review(models.Model):
    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        unique_together = ("barbershop_customer", "barber", "service", "barbershop")
        ordering = ["-created_at"]
        db_table = "reviews"

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

    def is_positive_review(self):
        """Verifica se a avaliação é positiva (4 ou 5 estrelas)"""
        return self.rating >= self.Rating.FOUR

    def is_negative_review(self):
        """Verifica se a avaliação é negativa (1 ou 2 estrelas)"""
        return self.rating <= self.Rating.TWO

    def is_neutral_review(self):
        """Verifica se a avaliação é neutra (3 estrelas)"""
        return self.rating == self.Rating.THREE

    def has_comment(self):
        """Verifica se a avaliação possui comentário"""
        return bool(self.comment and self.comment.strip())

    def get_rating_stars(self):
        """Retorna uma string com estrelas visuais da avaliação"""
        return "⭐" * self.rating

    def get_rating_display_with_stars(self):
        """Retorna a avaliação com estrelas e texto"""
        return f"{self.get_rating_stars()} ({self.get_rating_display()})"

    def get_customer_name(self):
        """Retorna o nome do cliente que fez a avaliação"""
        return self.barbershop_customer.customer.get_display_name()

    def get_barber_name(self):
        """Retorna o nome do barbeiro avaliado"""
        return self.barber.get_display_name()

    def get_service_name(self):
        """Retorna o nome do serviço avaliado"""
        return self.service.name

    def get_barbershop_name(self):
        """Retorna o nome da barbearia"""
        return self.barbershop.name

    def get_short_comment(self, max_length=100):
        """Retorna uma versão encurtada do comentário"""
        if not self.comment:
            return "Sem comentário"
        if len(self.comment) <= max_length:
            return self.comment
        return f"{self.comment[:max_length]}..."

    @classmethod
    def get_average_rating_for_barber(cls, barber):
        """Calcula a média de avaliações de um barbeiro"""
        reviews = cls.objects.filter(barber=barber)
        if not reviews.exists():
            return 0
        return round(
            reviews.aggregate(avg_rating=models.Avg("rating"))["avg_rating"], 2
        )

    @classmethod
    def get_average_rating_for_barbershop(cls, barbershop):
        """Calcula a média de avaliações de uma barbearia"""
        reviews = cls.objects.filter(barbershop=barbershop)
        if not reviews.exists():
            return 0
        return round(
            reviews.aggregate(avg_rating=models.Avg("rating"))["avg_rating"], 2
        )

    @classmethod
    def get_average_rating_for_service(cls, service):
        """Calcula a média de avaliações de um serviço"""
        reviews = cls.objects.filter(service=service)
        if not reviews.exists():
            return 0
        return round(
            reviews.aggregate(avg_rating=models.Avg("rating"))["avg_rating"], 2
        )

    def get_review_age_days(self):
        """Retorna a idade da avaliação em dias"""
        return (timezone.now() - self.created_at).days

    def is_recent_review(self, days=7):
        """Verifica se a avaliação é recente (padrão: 7 dias)"""
        return self.get_review_age_days() <= days
