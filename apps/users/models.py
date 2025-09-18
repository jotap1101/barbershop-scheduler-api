from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid import uuid4

class User(AbstractUser):
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-date_joined']

    class Role(models.TextChoices):
        CLIENT = 'CLIENT', 'Cliente'
        BARBER = 'BARBER', 'Barbeiro'

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, verbose_name='ID')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT, verbose_name='Cargo')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telefone')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Data de Nascimento')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, verbose_name='Foto de Perfil')
    bio = models.TextField(blank=True, verbose_name='Biografia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    is_barbershop_owner = models.BooleanField(default=False, verbose_name='Proprietário de Barbearia')

    def __str__(self):
        return self.get_full_name() or self.username
