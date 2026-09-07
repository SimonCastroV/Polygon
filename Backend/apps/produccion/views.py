from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import HistorialOrdenProduccion, OrdenProduccion
from .permissions import EsProduccion, PuedeVerOP
from .serializers import OrdenProduccionIngresarSerializer, OrdenProduccionSerializer

# Campos que se rastrean en HistorialOrdenProduccion cuando cambian al
# "ingresar a la OP" (único dato editable desde la API, ver
# OrdenProduccionIngresarSerializer).
CAMPOS_AUDITADOS = ['clasificacion', 'observaciones']


class OrdenProduccionListView(generics.ListAPIView):
    """
    GET /api/produccion/ordenes/ -> listado de OP, accesible a Producción,
    Supervisor y Administrador. Encabezado y materiales son de solo
    lectura: la OP llega ya hecha de Sumicolor (por ahora, cargada por
    Django admin) y no se crea/edita desde Polygon.
    """

    queryset = OrdenProduccion.objects.prefetch_related('materiales').all()
    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated, PuedeVerOP]


class OrdenProduccionDetailView(generics.RetrieveAPIView):
    """
    GET /api/produccion/ordenes/<pk>/ -> detalle completo de la OP
    (encabezado + tabla de materiales), accesible a Producción, Supervisor
    y Administrador.
    """

    queryset = OrdenProduccion.objects.prefetch_related('materiales').all()
    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated, PuedeVerOP]


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
                HistorialOrdenProduccion.objects.create(
                    orden=orden_actualizada,
                    modificado_por=self.request.user,
                    campo=campo,
                    valor_anterior=str(valor_anterior),
                    valor_nuevo=str(valor_nuevo),
                )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = OrdenProduccionSerializer(self.get_object()).data
        return response
