from django.conf import settings
from django.db import models


class OrdenProduccion(models.Model):
    """
    HU-10 Crear Orden de Producción / HU-11 Editar Orden de Producción.

    Supuesto (a confirmar con el equipo): esta primera versión modela los
    campos explícitamente mencionados en las HU (número de orden, producto,
    cantidad, materia prima, observaciones) más 'urgente', pedido por el
    negocio para que Adriana (Planeación) marque la orden antes de pasarla
    a Picky. No se modela un catálogo de Productos/Materias Primas (eso
    corresponde a HU-09 'Gestionar catálogos', fuera del alcance de esta
    tarea) ni un desglose de materias primas con porcentaje por lote (como
    existe en el sistema legado de Sumicolor: tablas CantidadesLotes /
    FrmProductos en DiccionarioDatos_OP.xlsx). Aquí 'materia_prima' es un
    campo de texto libre. Si Sumicolor requiere varias materias primas por
    orden, cada una con su propia cantidad, este modelo debería evolucionar
    a una tabla relacionada (similar a CantidadesLotes).
    """

    class Estado(models.TextChoices):
        PLANEACION = 'planeacion', 'Planeación'
        PICKY = 'picky', 'Picky'
        PESAJE = 'pesaje', 'Pesaje'
        MEZCLA = 'mezcla', 'Mezcla'
        EXTRUSION = 'extrusion', 'Extrusión'
        CALIDAD = 'calidad', 'Calidad'
        EMPAQUE = 'empaque', 'Empaque'
        FINALIZADA = 'finalizada', 'Finalizada'
        CANCELADA = 'cancelada', 'Cancelada'

    numero_orden = models.CharField(max_length=20, unique=True, editable=False)
    producto = models.CharField(max_length=120)
    cantidad = models.FloatField()
    materia_prima = models.CharField(max_length=120)
    urgente = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PLANEACION
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_creadas',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden de Producción'
        verbose_name_plural = 'Órdenes de Producción'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.numero_orden} ({self.get_estado_display()})'

    def save(self, *args, **kwargs):
        if not self.numero_orden:
            self.numero_orden = self._generar_numero_orden()
        super().save(*args, **kwargs)

    @staticmethod
    def _generar_numero_orden():
        """
        Genera un consecutivo simple OP-000001. Suficiente para el MVP con
        un solo proceso escribiendo a la vez; si hay creación concurrente
        real, esto debería reemplazarse por una secuencia de base de datos.
        """
        ultimo = OrdenProduccion.objects.order_by('-id').first()
        siguiente = (ultimo.id + 1) if ultimo else 1
        return f'OP-{siguiente:06d}'


class HistorialOrdenProduccion(models.Model):
    """Historial de cambios de una OP (HU-11: fecha, hora y usuario que editó)."""

    orden = models.ForeignKey(
        OrdenProduccion, on_delete=models.CASCADE, related_name='historial'
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    campo = models.CharField(max_length=50)
    valor_anterior = models.CharField(max_length=255, blank=True)
    valor_nuevo = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Orden de Producción'
        verbose_name_plural = 'Historial de Órdenes de Producción'
        ordering = ['-fecha']

    def __str__(self):
        campos = (self.campo, self.valor_anterior, self.valor_nuevo)
        return f'{self.orden.numero_orden} · {campos[0]}: {campos[1]} → {campos[2]}'
