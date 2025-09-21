from functools import partial
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.file_uploads import encrypted_filename


class User(AbstractUser):
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-date_joined"]

    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Cliente"
        BARBER = "BARBER", "Barbeiro"
        ADMIN = "ADMIN", "Administrador"

    id = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, verbose_name="ID"
    )
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.CLIENT, verbose_name="Função"
    )
    is_barbershop_owner = models.BooleanField(
        default=False, verbose_name="Proprietário de Barbearia"
    )
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Telefone"
    )
    birth_date = models.DateField(
        null=True, blank=True, verbose_name="Data de Nascimento"
    )
    profile_picture = models.ImageField(
        upload_to=partial(
            encrypted_filename,
            base_folder="profile_pictures",
            app_name=True,
            subfolder_map={
                Role.BARBER: "barbers",
                Role.CLIENT: "clients",
            },
            subfolder_attr="role",
            default_subfolder="others",
        ),
        null=True,
        blank=True,
        verbose_name="Foto de Perfil",
    )
    bio = models.TextField(null=True, blank=True, verbose_name="Biografia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    def __str__(self):
        return self.get_full_name() or self.username
