from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import HistorialOrdenProduccion, OrdenProduccion
from .permissions import EsPicky, EsProduccion, PuedeVerOP
from .serializers import (
    OrdenProduccionEnviarPesajeSerializer,
    OrdenProduccionEnviarPickySerializer,
    OrdenProduccionIngresarSerializer,
    OrdenProduccionRecepcionPickySerializer,
    OrdenProduccionSerializer,
)

# Campos que se rastrean en HistorialOrdenProduccion cuando cambian al
# "ingresar a la OP" (ver OrdenProduccionIngresarSerializer).
CAMPOS_AUDITADOS = ['clasificacion', 'observaciones']


def registrar_historial(orden, usuario, campo, valor_anterior, valor_nuevo):
    """Deja evidencia de un cambio en HistorialOrdenProduccion (trazabilidad)."""
    HistorialOrdenProduccion.objects.create(
        orden=orden,
        modificado_por=usuario,
        campo=campo,
        valor_anterior=str(valor_anterior or ''),
        valor_nuevo=str(valor_nuevo or ''),
    )


def ordenes_visibles_para(usuario):
    """
    Define qué Órdenes de Producción puede consultar cada estación.

    - Picky ve las OP que Producción ya liberó, incluso si después
      avanzaron a Pesaje. (Consulta el filtro "Ya liberado" para verlas)
    - Pesaje ve únicamente las OP pendientes en su etapa, es decir,
      aquellas cuyo estado actual es 'pesaje'.
    - Producción, Supervisor y Administrador pueden consultar todas.
    """
    queryset = OrdenProduccion.objects.prefetch_related('materiales').all()

    if usuario.rol == 'picky':
        return queryset.filter(fecha_envio_picky__isnull=False)

    if usuario.rol == 'pesaje':
        return queryset.filter(estado=OrdenProduccion.Estado.PESAJE)

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
    (encabezado + tabla de materiales + trazabilidad de Picky).
    """

    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated, PuedeVerOP]

    def get_queryset(self):
        return ordenes_visibles_para(self.request.user)


class OrdenProduccionIngresarView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/ingresar/ -> "Ingresar a OP": solo
    Producción (rol 'produccion') diligencia clasificación y observaciones,
    sin importar el estado de la OP (mientras no esté Finalizada o
    Cancelada, ver OrdenProduccionIngresarSerializer). Queda registrado en
    HistorialOrdenProduccion.
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionIngresarSerializer
    permission_classes = [IsAuthenticated, EsProduccion]

    def perform_update(self, serializer):
        orden = self.get_object()
        valores_anteriores = {campo: getattr(orden, campo) for campo in CAMPOS_AUDITADOS}
        orden_actualizada = serializer.save()

        for campo in CAMPOS_AUDITADOS:
            valor_anterior = valores_anteriores[campo]
            valor_nuevo = getattr(orden_actualizada, campo)
            if valor_anterior != valor_nuevo:
                registrar_historial(
                    orden_actualizada, self.request.user, campo, valor_anterior, valor_nuevo
                )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response


class OrdenProduccionEnviarPickyView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/enviar-picky/ -> "Mandar orden a
    Picky": solo Producción libera la OP. Cambia el estado En Producción →
    En Picky, sella la fecha/hora del servidor y deja la transición en
    HistorialOrdenProduccion. Una OP que ya salió de Producción no puede
    volver a enviarse (ver OrdenProduccionEnviarPickySerializer).
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionEnviarPickySerializer
    permission_classes = [IsAuthenticated, EsProduccion]

    def perform_update(self, serializer):
        estado_anterior = self.get_object().estado
        orden = serializer.save()
        registrar_historial(
            orden, self.request.user, 'estado', estado_anterior, orden.estado
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response


class OrdenProduccionRecepcionPickyView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/recepcion-picky/ -> Picky confirma
    que recibió la OP: registra el nombre del operario y el servidor sella
    la fecha/hora de recepción y la cuenta que confirmó. Solo aplica a OP
    que estén En Picky.
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionRecepcionPickySerializer
    permission_classes = [IsAuthenticated, EsPicky]

    def perform_update(self, serializer):
        nombre_anterior = self.get_object().nombre_operario_picky
        orden = serializer.save()
        registrar_historial(
            orden,
            self.request.user,
            'nombre_operario_picky',
            nombre_anterior,
            orden.nombre_operario_picky,
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response


class OrdenProduccionEnviarPesajeView(generics.UpdateAPIView):
    """
    PATCH /api/produccion/ordenes/<pk>/enviar-pesaje/ -> "Enviar a Pesaje":
    Picky termina y libera la OP. Cambia el estado En Picky → En Pesaje y
    sella la fecha/hora del servidor (finalización en Picky = envío a
    Pesaje). La base de Pesaje todavía no está construida: la OP queda ahí
    esperando esa etapa.
    """

    http_method_names = ['patch']
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionEnviarPesajeSerializer
    permission_classes = [IsAuthenticated, EsPicky]

    def perform_update(self, serializer):
        estado_anterior = self.get_object().estado
        orden = serializer.save()
        registrar_historial(orden, self.request.user, 'estado', estado_anterior, orden.estado)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response
