from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import HistorialOrdenProduccion, OrdenProduccion
from .permissions import EsPicking, EsProduccion, PuedeVerOP
from .serializers import (
    OrdenProduccionEnviarPesajeSerializer,
    OrdenProduccionEnviarPickingSerializer,
    OrdenProduccionRecepcionPickingSerializer,
    OrdenProduccionSerializer,
)

# Campos de la hoja de Producción que se rastrean en HistorialOrdenProduccion
# cuando cambian al mandar la OP a Picking (ver
# OrdenProduccionEnviarPickingSerializer).
CAMPOS_AUDITADOS = ['clasificacion', 'observaciones', 'grupo_critico_pesaje']


def registrar_historial(orden, usuario, campo, valor_anterior, valor_nuevo, detalle=''):
    """Deja evidencia de un cambio en HistorialOrdenProduccion (trazabilidad)."""
    HistorialOrdenProduccion.objects.create(
        orden=orden,
        modificado_por=usuario,
        campo=campo,
        valor_anterior=str(valor_anterior or ''),
        valor_nuevo=str(valor_nuevo or ''),
        detalle=detalle,
    )


def ordenes_visibles_para(usuario):
    """
    Define qué Órdenes de Producción puede consultar cada estación.

    - Picking ve las OP que Producción ya liberó, incluso si después
      avanzaron a Pesaje. (Consulta el filtro "Ya liberado" para verlas)
    - Pesaje ve únicamente las OP pendientes en su etapa, es decir,
      aquellas cuyo estado actual es 'pesaje'.
    - Ing. Producción ve solo las OP con acompañamiento de IP (hoja azul),
      en cualquier etapa: acompaña su proceso completo, sin editarlo.
    - Producción, Supervisor y Administrador pueden consultar todas. El
      Supervisor además revisa el pesaje, pero no se le restringe el
      queryset: su vista de supervisión filtra por estado en el frontend,
      porque también necesita ver todas las OP en su pantalla principal.
    """
    queryset = (
        OrdenProduccion.objects.select_related(
            'creado_por', 'recibida_por_picking', 'pesaje__registrado_por', 'pesaje__supervisor'
        )
        .prefetch_related('materiales', 'historial__modificado_por')
        .all()
    )

    if usuario.rol == 'picking':
        return queryset.filter(fecha_envio_picking__isnull=False)

    if usuario.rol == 'pesaje':
        return queryset.filter(estado=OrdenProduccion.Estado.PESAJE)

    if usuario.rol == 'ing_produccion':
        return queryset.filter(clasificacion=OrdenProduccion.Clasificacion.ACOMPANAMIENTO_IP)

    return queryset


class OrdenProduccionListView(generics.ListAPIView):
    """
    GET /api/produccion/ordenes/ -> listado de OP. El encabezado y los
    materiales son de solo lectura: la OP llega ya hecha de Sumicolor (por
    ahora, cargada por Django admin) y no se crea/edita desde Polygon.
    """

    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated, PuedeVerOP]

    def get_queryset(self):
        return ordenes_visibles_para(self.request.user)


class OrdenProduccionDetailView(generics.RetrieveAPIView):
    """
    GET /api/produccion/ordenes/<pk>/ -> detalle completo de la OP
    (encabezado + tabla de materiales + trazabilidad de Picking).
    """

    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated, PuedeVerOP]

    def get_queryset(self):
        return ordenes_visibles_para(self.request.user)


class OrdenProduccionEnviarPickingView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/enviar-picking/ -> "Mandar orden a
    Picking": solo Producción libera la OP. Guarda la hoja de Producción
    (tipo de orden, grupo para Pesaje y observaciones), cambia el estado En
    Producción → En Picking y sella la fecha/hora del servidor. Todo en una
    transacción: o se guarda y se envía, o no pasa nada. Cada cambio queda en
    HistorialOrdenProduccion. Una OP que ya salió de Producción no puede
    volver a enviarse (ver OrdenProduccionEnviarPickingSerializer).
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionEnviarPickingSerializer
    permission_classes = [IsAuthenticated, EsProduccion]

    @transaction.atomic
    def perform_update(self, serializer):
        orden = self.get_object()
        valores_anteriores = {campo: getattr(orden, campo) for campo in CAMPOS_AUDITADOS}
        estado_anterior = orden.estado
        orden = serializer.save()

        for campo in CAMPOS_AUDITADOS:
            valor_anterior = valores_anteriores[campo]
            valor_nuevo = getattr(orden, campo)
            if valor_anterior != valor_nuevo:
                # La trazabilidad de Pesaje muestra este detalle al operario.
                detalle = (
                    f'Clasificación del producto {orden.codigo_producto}: '
                    f'{orden.get_grupo_critico_pesaje_display()}'
                    if campo == 'grupo_critico_pesaje'
                    else ''
                )
                registrar_historial(
                    orden, self.request.user, campo, valor_anterior, valor_nuevo, detalle=detalle
                )
        registrar_historial(orden, self.request.user, 'estado', estado_anterior, orden.estado)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response


class OrdenProduccionRecepcionPickingView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/recepcion-picking/ -> Picking confirma
    que recibió la OP: registra el nombre del operario y el servidor sella
    la fecha/hora de recepción y la cuenta que confirmó. Solo aplica a OP
    que estén En Picking.
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionRecepcionPickingSerializer
    permission_classes = [IsAuthenticated, EsPicking]

    def perform_update(self, serializer):
        nombre_anterior = self.get_object().nombre_operario_picking
        orden = serializer.save()
        registrar_historial(
            orden,
            self.request.user,
            'nombre_operario_picking',
            nombre_anterior,
            orden.nombre_operario_picking,
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response


class OrdenProduccionEnviarPesajeView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/enviar-pesaje/ -> "Enviar a Pesaje":
    Picking termina y libera la OP. Cambia el estado En Picking → En Pesaje y
    sella la fecha/hora del servidor (finalización en Picking = envío a
    Pesaje). Desde ahí se registra el formulario en apps.pesaje y se envía
    a Supervisor de Pesaje antes de continuar a Mezcla.
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionEnviarPesajeSerializer
    permission_classes = [IsAuthenticated, EsPicking]

    def perform_update(self, serializer):
        estado_anterior = self.get_object().estado
        orden = serializer.save()
        registrar_historial(orden, self.request.user, 'estado', estado_anterior, orden.estado)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response
