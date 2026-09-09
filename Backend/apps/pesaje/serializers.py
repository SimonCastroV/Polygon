from decimal import Decimal

from rest_framework import serializers

from .models import VERIFICACIONES, VERIFICACIONES_CRITICAS, PesoMaterial, RegistroPesaje


class PesoMaterialSerializer(serializers.ModelSerializer):
    material = serializers.IntegerField(source='material_id', min_value=1)
    peso_real = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001')
    )

    class Meta:
        model = PesoMaterial
        fields = ['material', 'peso_real']
        validators = []

    def validate(self, attrs):
        # PATCH parcial de la OP no hace opcionales los campos de cada peso.
        errores = {}
        if 'material_id' not in attrs:
            errores['material'] = 'Seleccione una materia prima.'
        if 'peso_real' not in attrs:
            errores['peso_real'] = 'Registre el peso real.'
        if errores:
            raise serializers.ValidationError(errores)
        return attrs


class RegistroPesajeSerializer(serializers.ModelSerializer):
    pesos = PesoMaterialSerializer(many=True, required=False)
    registrado_por_username = serializers.CharField(
        source='registrado_por.username', read_only=True
    )
    supervisor_username = serializers.CharField(
        source='supervisor.username', read_only=True, default=None
    )
    revision_display = serializers.CharField(source='get_revision_display', read_only=True)

    class Meta:
        model = RegistroPesaje
        fields = [
            'id',
            'lote_anterior',
            'referencia_anterior',
            'lote_actual',
            'referencia_actual',
            'nombre_operario',
            *[campo for campo, _ in VERIFICACIONES],
            *[campo for campo, _ in VERIFICACIONES_CRITICAS],
            'critico_observaciones',
            'observaciones',
            'pesos',
            'registrado_por_username',
            'fecha_recepcion',
            'fecha_modificacion',
            'fecha_inicio_pesaje',
            'fecha_envio_supervision',
            'supervisor_username',
            'fecha_revision',
            'revision',
            'revision_display',
            'motivo_devolucion',
        ]
        read_only_fields = [
            'id',
            'referencia_actual',
            'fecha_recepcion',
            'fecha_modificacion',
            'fecha_inicio_pesaje',
            'fecha_envio_supervision',
            'fecha_revision',
            'revision',
            'motivo_devolucion',
        ]

    def validate(self, attrs):
        orden = self.context['orden']
        if not orden.es_critico_pesaje:
            # No aceptar respuestas ocultas ni borrar un registro anterior al reclasificar.
            campos = [campo for campo, _ in VERIFICACIONES_CRITICAS] + ['critico_observaciones']
            if any(attrs.get(campo) not in (None, '') for campo in campos):
                raise serializers.ValidationError(
                    {'detail': 'Las condiciones críticas no aplican a esta OP.'}
                )
            for campo in campos:
                attrs.pop(campo, None)
        materiales = set(orden.materiales.values_list('id', flat=True))
        pesos = attrs.get('pesos')
        if pesos is not None:
            ids = [peso['material_id'] for peso in pesos]
            if len(ids) != len(set(ids)):
                raise serializers.ValidationError({'pesos': 'Hay materias primas repetidas.'})
            if not set(ids).issubset(materiales):
                raise serializers.ValidationError(
                    {'pesos': 'Todas las materias primas deben pertenecer a esta OP.'}
                )

        if self.context.get('enviar'):
            errores = {}
            if not orden.grupo_critico_pesaje:
                errores['grupo_critico_pesaje'] = (
                    'La OP está sin clasificar. Solicite clasificar el producto en administración.'
                )
            for campo in ('lote_anterior', 'referencia_anterior', 'lote_actual', 'nombre_operario'):
                valor = attrs.get(campo, getattr(self.instance, campo, ''))
                if not valor.strip():
                    errores[campo] = 'Este campo es obligatorio para enviar a supervisor.'
            # Un producto crítico responde el formulario de condiciones críticas
            # y uno normal el estándar: nunca se exigen los dos.
            verificaciones = VERIFICACIONES_CRITICAS if orden.es_critico_pesaje else VERIFICACIONES
            respuestas = {
                campo: attrs.get(campo, getattr(self.instance, campo, None))
                for campo, _ in verificaciones
            }
            for campo, valor in respuestas.items():
                if valor is None:
                    errores[campo] = 'Seleccione Cumple o No cumple.'
            # Un "No cumple" no impide continuar, pero sí debe quedar explicado.
            campo_observaciones = (
                'critico_observaciones' if orden.es_critico_pesaje else 'observaciones'
            )
            observacion = attrs.get(
                campo_observaciones, getattr(self.instance, campo_observaciones, '')
            )
            if any(valor is False for valor in respuestas.values()) and not observacion.strip():
                errores[campo_observaciones] = (
                    'Explique los puntos marcados “No cumple” antes de enviar a supervisor.'
                )
            if pesos is None:
                ids_pesados = (
                    set(self.instance.pesos.values_list('material_id', flat=True))
                    if self.instance
                    else set()
                )
            else:
                ids_pesados = {peso['material_id'] for peso in pesos}
            if not materiales or ids_pesados != materiales:
                errores['pesos'] = 'Registre un peso positivo para cada materia prima de la OP.'
            if errores:
                raise serializers.ValidationError(errores)
        return attrs

    def create(self, validated_data):
        pesos = validated_data.pop('pesos', [])
        registro = RegistroPesaje.objects.create(**validated_data)
        self.guardar_pesos(registro, pesos)
        return registro

    def update(self, instance, validated_data):
        pesos = validated_data.pop('pesos', None)
        instance = super().update(instance, validated_data)
        if pesos is not None:
            self.guardar_pesos(instance, pesos)
        return instance

    @staticmethod
    def guardar_pesos(registro, pesos):
        # La lista enviada reemplaza el borrador de pesos, nunca la fórmula.
        registro.pesos.exclude(material_id__in=[p['material_id'] for p in pesos]).delete()
        for peso in pesos:
            PesoMaterial.objects.update_or_create(
                pesaje=registro,
                material_id=peso['material_id'],
                defaults={'peso_real': peso['peso_real']},
            )


class DevolucionPesajeSerializer(serializers.Serializer):
    motivo = serializers.CharField(allow_blank=False, trim_whitespace=True)
