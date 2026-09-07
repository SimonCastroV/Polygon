from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import HistorialOrdenProduccion, OrdenProduccion
from .permissions import PuedeGestionarOP
from .serializers import (
    OrdenProduccionCreateSerializer,
    OrdenProduccionSerializer,
    OrdenProduccionUpdateSerializer,
)

# Campos que se rastrean en HistorialOrdenProduccion cuando cambian.
CAMPOS_AUDITADOS = ['producto', 'cantidad', 'materia_prima', 'urgente', 'observaciones']


class OrdenProduccionListCreateView(generics.ListCreateAPIView):
    """
    HU-10 Crear Orden de Producción.
    GET  /api/produccion/ordenes/  -> listado (usado también por HU-12).
    POST /api/produccion/ordenes/  -> crea la OP en estado 'planeacion' con
    un número de orden único autogenerado.
    """

    queryset = OrdenProduccion.objects.all()
    permission_classes = [IsAuthenticated, PuedeGestionarOP]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrdenProduccionCreateSerializer
        return OrdenProduccionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        orden = serializer.save()
        return Response(OrdenProduccionSerializer(orden).data, status=status.HTTP_201_CREATED)


class OrdenProduccionDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    HU-11 Editar Orden de Producción.
    GET   /api/produccion/ordenes/<pk>/ -> detalle.
    PATCH/PUT /api/produccion/ordenes/<pk>/ -> edita mientras esté en
    Planeación; cada campo modificado queda en HistorialOrdenProduccion.
    """

    queryset = OrdenProduccion.objects.all()
    permission_classes = [IsAuthenticated, PuedeGestionarOP]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrdenProduccionSerializer
        return OrdenProduccionUpdateSerializer

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
