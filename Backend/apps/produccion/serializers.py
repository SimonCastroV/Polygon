from rest_framework import serializers

from .models import HistorialOrdenProduccion, MaterialOrden, OrdenProduccion


class HistorialOrdenProduccionSerializer(serializers.ModelSerializer):
    modificado_por_username = serializers.CharField(
        source='modificado_por.username', read_only=True, default=None
    )

    class Meta:
        model = HistorialOrdenProduccion
        fields = [
            'id',
            'campo',
            'valor_anterior',
            'valor_nuevo',
            'modificado_por_username',
            'fecha',
        ]


class MaterialOrdenSerializer(serializers.ModelSerializer):
    """Fila de la tabla de materiales del documento (solo lectura desde la API)."""

    class Meta:
        model = MaterialOrden
        fields = ['id', 'codigo', 'descripcion', 'porcentaje', 'cantidad', 'localizacion']
        read_only_fields = fields


class OrdenProduccionSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura de la OP: encabezado real (Sumicolor) + tabla de
    materiales + clasificación/observaciones (Producción). Se usa tanto
    para el listado como para el detalle; el encabezado y los materiales
    solo se cargan por Django admin (ver apps.produccion.admin), la API
    únicamente los expone en modo lectura.
    """

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    clasificacion_display = serializers.CharField(
        source='get_clasificacion_display', read_only=True
    )
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True)
    materiales = MaterialOrdenSerializer(many=True, read_only=True)

    class Meta:
        model = OrdenProduccion
        fields = [
            'id',
            'numero_orden',
            'codigo_producto',
            'referencia',
            'cantidad',
            'unidad',
            'cliente',
            'codigo_cliente',
            'pedido',
            'fecha_pedido',
            'hora_pedido',
            'vencimiento_pedido',
            'fecha_hora_lote',
            'materiales',
            'clasificacion',
            'clasificacion_display',
            'observaciones',
            'estado',
            'estado_display',
            'creado_por',
            'creado_por_username',
            'fecha_creacion',
            'fecha_modificacion',
        ]
        read_only_fields = fields


class OrdenProduccionIngresarSerializer(serializers.ModelSerializer):
    """
    "Ingresar a OP": único dato que Producción diligencia dentro de
    Polygon. El resto de la OP (encabezado y materiales) es de solo
    lectura porque viene de Sumicolor (ver docstring de OrdenProduccion).
    """

    class Meta:
        model = OrdenProduccion
        fields = ['clasificacion', 'observaciones']

    def validate(self, attrs):
        if self.instance.estado in (
            OrdenProduccion.Estado.FINALIZADA,
            OrdenProduccion.Estado.CANCELADA,
        ):
            raise serializers.ValidationError(
                'No se puede ingresar a una Orden de Producción Finalizada o Cancelada.'
            )
        return attrs
