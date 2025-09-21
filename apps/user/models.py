import os
from datetime import date
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

    @property
    def age(self):
        """Calcula a idade do usuário baseado na data de nascimento"""
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def is_barber(self):
        """Verifica se o usuário é barbeiro"""
        return self.role == self.Role.BARBER

    def is_client(self):
        """Verifica se o usuário é cliente"""
        return self.role == self.Role.CLIENT

    def is_admin_user(self):
        """Verifica se o usuário é administrador"""
        return self.role == self.Role.ADMIN

    def has_profile_picture(self):
        """Verifica se o usuário possui foto de perfil"""
        return bool(self.profile_picture)

    def get_display_name(self):
        """Retorna o nome de exibição preferencial do usuário"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def get_role_display_translated(self):
        """Retorna a tradução do papel do usuário"""
        return self.get_role_display()

    def get_profile_completion_percentage(self):
        """Calcula a porcentagem de preenchimento do perfil"""
        fields = [
            self.first_name,
            self.last_name,
            self.email,
            self.phone,
            self.birth_date,
            self.profile_picture,
            self.bio,
        ]
        filled_fields = sum(1 for field in fields if field)
        return round((filled_fields / len(fields)) * 100, 2)

    @classmethod
    def get_barbers_queryset(cls):
        """Retorna queryset filtrado de barbeiros ativos"""
        return cls.objects.filter(role=cls.Role.BARBER, is_active=True)

    @classmethod
    def get_clients_queryset(cls):
        """Retorna queryset filtrado de clientes ativos"""
        return cls.objects.filter(role=cls.Role.CLIENT, is_active=True)

    @classmethod
    def get_admins_queryset(cls):
        """Retorna queryset filtrado de administradores"""
        return cls.objects.filter(role=cls.Role.ADMIN)

    @classmethod
    def get_users_stats(cls):
        """Retorna estatísticas dos usuários"""
        return {
            "total_users": cls.objects.count(),
            "active_users": cls.objects.filter(is_active=True).count(),
            "inactive_users": cls.objects.filter(is_active=False).count(),
            "clients_count": cls.objects.filter(role=cls.Role.CLIENT).count(),
            "barbers_count": cls.objects.filter(role=cls.Role.BARBER).count(),
            "admins_count": cls.objects.filter(role=cls.Role.ADMIN).count(),
            "barbershop_owners": cls.objects.filter(is_barbershop_owner=True).count(),
        }

    def can_be_deactivated_by(self, user):
        """Verifica se o usuário pode ser desativado por outro usuário"""
        if not user.is_admin_user():
            return False
        if self.is_admin_user() and user != self:
            return False
        return True
