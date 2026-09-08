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
        SUPERVISOR_PESAJE = 'supervisor_pesaje', 'Supervisor de Pesaje'
        # Una cuenta por estación. El supervisor genérico conserva su consulta;
        # supervisor_pesaje es el único rol que revisa y libera Pesaje a Mezcla.
        PRODUCCION = 'produccion', 'Producción'
        PICKY = 'picky', 'Picky'
        PESAJE = 'pesaje', 'Pesaje'
        MEZCLA = 'mezcla', 'Mezcla'
        EXTRUSION = 'extrusion', 'Extrusión'
        CALIDAD = 'calidad', 'Calidad'
        EMPAQUE = 'empaque', 'Empaque'
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


class RegistroAuditoriaUsuario(models.Model):
    """
    Historial de cambios sobre un usuario (HU-05: 'El sistema mantiene un
    registro de la modificación'). Se crea una fila por cada campo que
    cambia en una edición (incluye el rol, para HU-06).
    """

    usuario = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='auditorias'
    )
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modificaciones_realizadas',
    )
    campo = models.CharField(max_length=50)
    valor_anterior = models.CharField(max_length=255, blank=True)
    valor_nuevo = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de auditoría de usuario'
        verbose_name_plural = 'Registros de auditoría de usuarios'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.usuario} · {self.campo}: {self.valor_anterior} → {self.valor_nuevo}'
