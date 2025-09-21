import os
from functools import partial
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.file_uploads import encrypted_filename


# Create your models here.
class User(AbstractUser):
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-date_joined"]
        db_table = "users"

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
                Role.ADMIN: "admins",
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

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = User.objects.get(pk=self.pk)

                if (
                    old_instance.profile_picture
                    and self.profile_picture != old_instance.profile_picture
                ):
                    if os.path.isfile(old_instance.profile_picture.path):
                        os.remove(old_instance.profile_picture.path)
            except User.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.profile_picture and os.path.isfile(self.profile_picture.path):
            os.remove(self.profile_picture.path)

        super().delete(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username
