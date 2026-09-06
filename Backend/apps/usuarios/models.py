from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('rol', CustomUser.Rol.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        SUPERVISOR = 'supervisor', 'Supervisor'
        PLANTA = 'planta', 'Personal de Planta'

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.PLANTA)
    email = models.EmailField(blank=True)

    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.username} ({self.get_rol_display()})'
