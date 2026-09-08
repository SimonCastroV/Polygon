from django.utils import timezone
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
    recibida_por_picky_username = serializers.CharField(
        source='recibida_por_picky.username', read_only=True, default=None
    )
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
            'fecha_envio_picky',
            'nombre_operario_picky',
            'recibida_por_picky_username',
            'fecha_recepcion_picky',
            'fecha_envio_pesaje',
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


class OrdenProduccionEnviarPickySerializer(serializers.ModelSerializer):
    """
    "Mandar orden a Picky": Producción libera la OP. No recibe datos del
    cliente — el nuevo estado y la fecha/hora los define el servidor — y
    solo procede si la OP sigue En Producción, de modo que no pueda
    enviarse dos veces.
    """

    class Meta:
        model = OrdenProduccion
        fields = []

    def validate(self, attrs):
        if self.instance.estado != OrdenProduccion.Estado.PRODUCCION:
            raise serializers.ValidationError(
                'Solo se puede mandar a Picky una Orden de Producción que esté En '
                f'Producción. Esta orden ya está en estado "{self.instance.get_estado_display()}".'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.estado = OrdenProduccion.Estado.PICKY
        instance.fecha_envio_picky = timezone.now()
        instance.save(update_fields=['estado', 'fecha_envio_picky', 'fecha_modificacion'])
        return instance


class OrdenProduccionRecepcionPickySerializer(serializers.ModelSerializer):
    """
    Recepción en Picky: el operario registra su nombre y el servidor
    guarda la fecha/hora y la cuenta (estación) desde la que se confirmó.
    Picky no puede tocar ningún otro dato de la OP.
    """

    class Meta:
        model = OrdenProduccion
        fields = ['nombre_operario_picky']

    def validate_nombre_operario_picky(self, value):
        if not value.strip():
            raise serializers.ValidationError('El nombre del operario de Picky es obligatorio.')
        return value.strip()

    def validate(self, attrs):
        if self.instance.estado != OrdenProduccion.Estado.PICKY:
            raise serializers.ValidationError(
                'Solo se puede registrar la recepción de una Orden de Producción que esté '
                'En Picky.'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.nombre_operario_picky = validated_data['nombre_operario_picky']
        instance.recibida_por_picky = self.context['request'].user
        instance.fecha_recepcion_picky = timezone.now()
        instance.save(
            update_fields=[
                'nombre_operario_picky',
                'recibida_por_picky',
                'fecha_recepcion_picky',
                'fecha_modificacion',
            ]
        )
        return instance


class OrdenProduccionEnviarPesajeSerializer(serializers.ModelSerializer):
    """
    "Enviar a Pesaje": Picky termina su trabajo y libera la OP. La fecha/hora
    la pone el servidor y sirve a la vez como finalización en Picky y como
    envío a Pesaje. Exige haber registrado antes la recepción, para que la
    trazabilidad quede completa (quién recibió y cuándo).
    """

    class Meta:
        model = OrdenProduccion
        fields = []

    def validate(self, attrs):
        if self.instance.estado != OrdenProduccion.Estado.PICKY:
            raise serializers.ValidationError(
                'Solo se puede enviar a Pesaje una Orden de Producción que esté En Picky. '
                f'Esta orden está en estado "{self.instance.get_estado_display()}".'
            )
        if not self.instance.fecha_recepcion_picky:
            raise serializers.ValidationError(
                'Primero debe registrar la recepción en Picky (nombre del operario).'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.estado = OrdenProduccion.Estado.PESAJE
        instance.fecha_envio_pesaje = timezone.now()
        instance.save(update_fields=['estado', 'fecha_envio_pesaje', 'fecha_modificacion'])
        return instance
