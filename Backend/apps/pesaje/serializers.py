from rest_framework import serializers

from .models import VERIFICACIONES, VERIFICACIONES_CRITICAS, RegistroPesaje


class RegistroPesajeSerializer(serializers.ModelSerializer):
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
        # Cada OP responde un solo formulario: el de condiciones críticas o el
        # estándar. Las respuestas del otro no se aceptan (no se muestran, así
        # que llegarían de un cliente desactualizado) ni se guardan, para no
        # dejar datos que nadie revisó.
        if orden.es_critico_pesaje:
            campos_ajenos = [campo for campo, _ in VERIFICACIONES] + ['observaciones']
            mensaje = 'Un producto crítico responde solo las condiciones críticas.'
        else:
            campos_ajenos = [campo for campo, _ in VERIFICACIONES_CRITICAS] + [
                'critico_observaciones'
            ]
            mensaje = 'Las condiciones críticas no aplican a esta OP.'
        if any(attrs.get(campo) not in (None, '') for campo in campos_ajenos):
            raise serializers.ValidationError({'detail': mensaje})
        for campo in campos_ajenos:
            attrs.pop(campo, None)

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
            # El operario pesa las cantidades de la fórmula (no las digita), pero
            # una OP sin materias primas no tiene nada que pesar.
            if not orden.materiales.exists():
                errores['materiales'] = (
                    'Esta OP no tiene materias primas cargadas. Avise a administración.'
                )
            if errores:
                raise serializers.ValidationError(errores)
        return attrs


class DevolucionPesajeSerializer(serializers.Serializer):
    motivo = serializers.CharField(allow_blank=False, trim_whitespace=True)
