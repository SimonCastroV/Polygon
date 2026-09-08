from django.conf import settings
from django.db import models

VERIFICACIONES = (
    ('productos_retirados', 'Se retiraron todos los productos del lote anterior'),
    (
        'sin_restos_lote_anterior',
        'No quedan pigmentos, etiquetas o documentos en el proceso del lote anterior',
    ),
    ('balanzas_limpias', 'Balanzas niveladas, limpias y sin residuos'),
    ('superficies_limpias', 'Superficies y mesas limpias'),
    ('utensilios_limpios', 'Utensilios limpios y en buen estado'),
    ('piso_limpio', 'Piso limpio y sin derrames'),
    ('area_ordenada', 'Área ordenada y acondicionada para nuevo lote'),
    ('bolsa_identificada', 'Bolsa provisional de empaque correctamente identificada'),
    ('epp_adecuado', 'Uso adecuado de EPP'),
    ('residuos_dispuestos', 'Residuos del lote anterior dispuestos correctamente'),
)


VERIFICACIONES_CRITICAS = (
    (
        'critico_area_equipos_limpios',
        'El área (pisos, paredes) y los equipos a operar se encuentran limpios y '
        'libres de residuos.',
    ),
    (
        'critico_limpieza_anterior_liberada',
        'Se libera la limpieza ejecutada del producto anterior.',
    ),
    (
        'critico_uniforme_epp',
        'El personal que participa en la operación porta uniforme limpio, completo y '
        'utiliza los EPP.',
    ),
    (
        'critico_mp_identificadas',
        'Las MP presentes en el área están identificadas, segregadas y corresponden '
        'con la OP a fabricar.',
    ),
    (
        'critico_equipos_aptos',
        'Los equipos y periféricos requeridos para la fabricación se encuentran '
        'disponibles y aptos para iniciar la operación.',
    ),
    (
        'critico_sin_actividades_simultaneas',
        'No se realizan actividades simultáneas (limpieza, mantenimiento u otras) '
        'que puedan generar contaminación del producto.',
    ),
    (
        'critico_ambiente_adecuado',
        'Las condiciones ambientales del área son adecuadas para iniciar pesaje.',
    ),
    ('critico_cero_pellets', 'Se cumple con “Cero Pellets en el Piso”.'),
    (
        'critico_sin_condiciones_inseguras',
        'No se identifican condiciones inseguras o desviaciones que afecten la '
        'integridad del producto.',
    ),
    (
        'critico_liberacion_autorizada',
        '¿Se autoriza la liberación de las condiciones operacionales para iniciar el '
        'pesaje del lote?',
    ),
)


class RegistroPesaje(models.Model):
    """Formulario vigente de la OP. Las revisiones anteriores quedan en su historial.

    Las respuestas nulas permiten guardar borradores sin confundir pendiente con
    No cumple. El estado del flujo pertenece exclusivamente a OrdenProduccion.
    """

    class Revision(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de revisión'
        APROBADA = 'aprobada', 'Aprobada'
        DEVUELTA = 'devuelta', 'Devuelta a Pesaje'

    orden = models.OneToOneField(
        'produccion.OrdenProduccion', on_delete=models.CASCADE, related_name='pesaje'
    )
    lote_anterior = models.CharField(max_length=120, blank=True)
    referencia_anterior = models.CharField(max_length=120, blank=True)
    lote_actual = models.CharField(max_length=120, blank=True)
    # Copia de la referencia de la OP al guardar; nunca la proporciona el cliente.
    referencia_actual = models.CharField(max_length=120)
    nombre_operario = models.CharField(max_length=120, blank=True)
    productos_retirados = models.BooleanField(null=True, blank=True)
    sin_restos_lote_anterior = models.BooleanField(null=True, blank=True)
    balanzas_limpias = models.BooleanField(null=True, blank=True)
    superficies_limpias = models.BooleanField(null=True, blank=True)
    utensilios_limpios = models.BooleanField(null=True, blank=True)
    piso_limpio = models.BooleanField(null=True, blank=True)
    area_ordenada = models.BooleanField(null=True, blank=True)
    bolsa_identificada = models.BooleanField(null=True, blank=True)
    epp_adecuado = models.BooleanField(null=True, blank=True)
    residuos_dispuestos = models.BooleanField(null=True, blank=True)
    # Evidencia futura: asociar adjuntos a este registro cuando exista un servicio
    # compartido de archivos. No se aceptan rutas/URLs como sustituto de archivos.
    critico_area_equipos_limpios = models.BooleanField(null=True, blank=True)
    critico_limpieza_anterior_liberada = models.BooleanField(null=True, blank=True)
    critico_uniforme_epp = models.BooleanField(null=True, blank=True)
    critico_mp_identificadas = models.BooleanField(null=True, blank=True)
    critico_equipos_aptos = models.BooleanField(null=True, blank=True)
    critico_sin_actividades_simultaneas = models.BooleanField(null=True, blank=True)
    critico_ambiente_adecuado = models.BooleanField(null=True, blank=True)
    critico_cero_pellets = models.BooleanField(null=True, blank=True)
    critico_sin_condiciones_inseguras = models.BooleanField(null=True, blank=True)
    critico_liberacion_autorizada = models.BooleanField(null=True, blank=True)
    critico_observaciones = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pesajes_registrados'
    )
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_envio_supervision = models.DateTimeField(null=True, blank=True)
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pesajes_revisados',
        null=True,
        blank=True,
    )
    fecha_revision = models.DateTimeField(null=True, blank=True)
    revision = models.CharField(max_length=12, choices=Revision.choices, blank=True)
    motivo_devolucion = models.TextField(blank=True)

    def __str__(self):
        return f'Pesaje · {self.orden.numero_orden}'


class PesoMaterial(models.Model):
    """Peso real en la misma unidad que la cantidad de fórmula; no altera MaterialOrden."""

    pesaje = models.ForeignKey(RegistroPesaje, on_delete=models.CASCADE, related_name='pesos')
    material = models.ForeignKey('produccion.MaterialOrden', on_delete=models.PROTECT)
    peso_real = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['pesaje', 'material'], name='peso_material_unico'),
            models.CheckConstraint(condition=models.Q(peso_real__gt=0), name='peso_real_positivo'),
        ]

    def __str__(self):
        return f'{self.material.codigo} · {self.peso_real}'
