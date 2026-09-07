from rest_framework import serializers

from .models import HistorialOrdenProduccion, OrdenProduccion


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


class OrdenProduccionSerializer(serializers.ModelSerializer):
    """Serializer de lectura (HU-12 Consultar OP y detalle de HU-10/HU-11)."""

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = OrdenProduccion
        fields = [
            'id',
            'numero_orden',
            'producto',
            'cantidad',
            'materia_prima',
            'urgente',
            'observaciones',
            'estado',
            'estado_display',
            'creado_por',
            'creado_por_username',
            'fecha_creacion',
            'fecha_modificacion',
        ]
        read_only_fields = fields


class OrdenProduccionCreateSerializer(serializers.ModelSerializer):
    """HU-10 Crear Orden de Producción."""

    class Meta:
        model = OrdenProduccion
        fields = ['producto', 'cantidad', 'materia_prima', 'urgente', 'observaciones']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor a cero.')
        return value

    def validate_producto(self, value):
        if not value.strip():
            raise serializers.ValidationError('El producto es obligatorio.')
        return value

    def validate_materia_prima(self, value):
        if not value.strip():
            raise serializers.ValidationError('La materia prima es obligatoria.')
        return value

    def create(self, validated_data):
        validated_data['creado_por'] = self.context['request'].user
        return OrdenProduccion.objects.create(**validated_data)


class OrdenProduccionUpdateSerializer(serializers.ModelSerializer):
    """
    HU-11 Editar Orden de Producción.

    Regla de negocio: una OP solo puede editarse mientras está en estado
    Planeación (no puede editarse una OP que ya inició producción).
    """

    class Meta:
        model = OrdenProduccion
        fields = ['producto', 'cantidad', 'materia_prima', 'urgente', 'observaciones']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor a cero.')
        return value

    def validate(self, attrs):
        if self.instance.estado != OrdenProduccion.Estado.PLANEACION:
            raise serializers.ValidationError(
                'Solo se puede editar una Orden de Producción mientras está en estado Planeación.'
            )
        return attrs
