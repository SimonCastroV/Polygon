from django.conf import settings
from django.db import models


class OrdenProduccion(models.Model):
    """
    Contraste con BD_TABLAS_OP_HP.xlsx / DiccionarioDatos_OP.xlsx (copia de
    la base de datos legada de Sumicolor): el encabezado completo de la OP
    física (código de producto, referencia, cantidad, cliente, código de
    cliente, pedido, fechas de pedido/lote/vencimiento) y el desglose de
    materias primas (tabla MaterialOrden: código, descripción, %, cantidad)
    provienen de tablas ya existentes de Sumicolor (vista CantidadesLotes,
    FrmProductos, Productos, MateriasPrimas, LotesProduccion). Ese
    diccionario NO tiene ningún campo de observaciones ni de clasificación
    urgente/peligroso/normal: esos dos sí son datos propios que captura
    Producción en Polygon (ver OrdenProduccionIngresarSerializer).

    Regla de negocio: la OP no se crea/edita desde Polygon — llega ya hecha
    de Sumicolor. Mientras no exista esa integración, el encabezado y los
    materiales se cargan por Django admin (ver OrdenProduccionAdmin); la
    API REST solo los expone en modo lectura. Por eso 'codigo_producto',
    'referencia', 'cliente', etc. no tienen serializer de escritura.

    'fecha_hora_lote' se deja opcional (null=True) aunque en Sumicolor es
    "not null": al cargar la OP en Polygon el lote de producción puede no
    existir todavía. Fuera de alcance por ahora (sin tabla fuente en el
    Excel entregado): Procesos/Sec/Tiempo Textil/Nota, y las líneas de
    firma manual O.P./HP/A mezclas/A calidad del documento impreso.
    """

    class Clasificacion(models.TextChoices):
        URGENTE = 'urgente', 'Urgente'
        PELIGROSO = 'peligroso', 'Producto peligroso'
        NORMAL = 'normal', 'Proceso normal'

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

    # --- Identificación (Polygon vs. Sumicolor) ---
    numero_orden = models.CharField(max_length=20, unique=True, editable=False)
    codigo_producto = models.CharField('código', max_length=20)

    # --- Encabezado (Sumicolor: vista CantidadesLotes) ---
    referencia = models.CharField(max_length=120)
    cantidad = models.FloatField()
    unidad = models.CharField(max_length=10, blank=True)
    cliente = models.CharField(max_length=100, blank=True)
    codigo_cliente = models.CharField(max_length=15)
    pedido = models.CharField(max_length=9)
    fecha_pedido = models.DateField(null=True, blank=True)
    hora_pedido = models.TimeField(null=True, blank=True)
    vencimiento_pedido = models.DateField()
    fecha_hora_lote = models.DateTimeField(null=True, blank=True)

    # --- Propios de Polygon (los diligencia Producción al "ingresar a la OP") ---
    clasificacion = models.CharField(
        max_length=20, choices=Clasificacion.choices, default=Clasificacion.NORMAL
    )
    observaciones = models.TextField(blank=True)

    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PLANEACION
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordenes_creadas',
        # blank=True: en el admin se autocompleta con el usuario actual si
        # se deja vacío (ver OrdenProduccionAdmin.save_model).
        blank=True,
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


class MaterialOrden(models.Model):
    """
    Una fila de la tabla de materiales del documento físico de OP (columnas
    Código/Descripción/%/Cantidad/Localización). En Sumicolor sale de
    FrmProductos/Productos/MateriasPrimas por cada OP; aquí se carga junto
    con el encabezado (ver OrdenProduccion) por Django admin mientras no
    exista la integración real. 'localizacion' queda como texto libre: en
    Sumicolor es un valor compuesto/derivado (ej. "W01 - H320 = 4.0000"),
    sin una columna simple confirmada en el diccionario de datos.
    """

    orden = models.ForeignKey(
        OrdenProduccion, on_delete=models.CASCADE, related_name='materiales'
    )
    codigo = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=120)
    porcentaje = models.FloatField()
    cantidad = models.FloatField()
    localizacion = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = 'Material de Orden de Producción'
        verbose_name_plural = 'Materiales de Orden de Producción'

    def __str__(self):
        return f'{self.orden.numero_orden} · {self.codigo} ({self.porcentaje}%)'


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
