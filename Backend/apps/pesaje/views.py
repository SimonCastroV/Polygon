from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.produccion.models import OrdenProduccion
from apps.produccion.serializers import OrdenProduccionSerializer
from apps.produccion.views import registrar_historial

from .models import VERIFICACIONES, VERIFICACIONES_CRITICAS, RegistroPesaje
from .permissions import EsPesaje, EsSupervisorPesaje
from .serializers import DevolucionPesajeSerializer, RegistroPesajeSerializer


class VerificacionesPesajeView(APIView):
    """
    Definición de los dos formularios de verificación (estándar y de
    condiciones críticas). El frontend los pinta desde aquí para no mantener
    una copia de los textos que se desincronice de los campos del modelo.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                'normales': [list(item) for item in VERIFICACIONES],
                'criticas': [list(item) for item in VERIFICACIONES_CRITICAS],
            }
        )


def bloquear_orden(pk, estado):
    orden = get_object_or_404(OrdenProduccion.objects.select_for_update(), pk=pk)
    if orden.estado != estado:
        raise serializers.ValidationError(
            {'detail': f'La orden está en "{orden.get_estado_display()}". Recargue la bandeja.'}
        )
    return orden


def cambiar_estado(orden, usuario, estado, detalle):
    anterior = orden.estado
    orden.estado = estado
    orden.save(update_fields=['estado', 'fecha_modificacion'])
    registrar_historial(orden, usuario, 'estado', anterior, estado, detalle=detalle)


def detalle_registro(orden, registro):
    detalle = f'Operario: {registro.nombre_operario}'
    respuestas_criticas = [getattr(registro, campo) for campo, _ in VERIFICACIONES_CRITICAS]
    # Antes de que el operario conteste algo, todas las respuestas están en None
    # (p. ej. justo al "Confirmar recibido"): mostrar ahí la lista completa en
    # "Pendiente" no aporta nada y ensucia la trazabilidad. Solo se agrega este
    # detalle cuando ya hay una respuesta real que registrar.
    if orden.es_critico_pesaje and (
        any(valor is not None for valor in respuestas_criticas) or registro.critico_observaciones
    ):
        # Instantánea legible en el historial existente: conserva respuestas previas
        # aunque se corrijan en una devolución y se vuelvan a enviar.
        respuestas = {True: 'Cumple', False: 'No cumple', None: 'Pendiente'}
        lineas = [f'Producto crítico: {orden.get_grupo_critico_pesaje_display()}']
        lineas.extend(
            f'{label} {respuestas[valor]}'
            for (campo, label), valor in zip(VERIFICACIONES_CRITICAS, respuestas_criticas)
        )
        lineas.append(f'Acciones correctivas / Observaciones: {registro.critico_observaciones}')
        detalle += '\n' + '\n'.join(lineas)
    return detalle


class GuardarPesajeView(APIView):
    permission_classes = [IsAuthenticated, EsPesaje]
    enviar = False

    @transaction.atomic
    def patch(self, request, pk):
        orden = bloquear_orden(pk, OrdenProduccion.Estado.PESAJE)
        registro = RegistroPesaje.objects.filter(orden=orden).first()
        nuevo = registro is None
        serializer = RegistroPesajeSerializer(
            registro,
            data=request.data,
            partial=True,
            context={'orden': orden, 'enviar': self.enviar},
        )
        serializer.is_valid(raise_exception=True)
        registro = serializer.save(
            orden=orden, registrado_por=request.user, referencia_actual=orden.referencia
        )
        registrar_historial(
            orden,
            request.user,
            'pesaje_registro',
            '',
            'Recepción y primer registro' if nuevo else 'Registro actualizado',
            detalle=detalle_registro(orden, registro),
        )
        if self.enviar:
            registro.fecha_envio_supervision = timezone.now()
            registro.revision = RegistroPesaje.Revision.PENDIENTE
            registro.supervisor = None
            registro.fecha_revision = None
            registro.motivo_devolucion = ''
            registro.save()
            cambiar_estado(
                orden,
                request.user,
                OrdenProduccion.Estado.SUPERVISION_PESAJE,
                'Pesaje enviado a supervisor.',
            )
        # Instancia nueva: evita relaciones inversas/prefetch obsoletos en la respuesta.
        return Response(OrdenProduccionSerializer(OrdenProduccion.objects.get(pk=pk)).data)


class EnviarSupervisorView(GuardarPesajeView):
    enviar = True


class IniciarPesajeView(APIView):
    """
    Sella la hora de inicio del pesaje ("H.INC" de la hoja de proceso) cuando
    el operario abre el registro de cantidades. Es idempotente: si ya se selló,
    no la mueve, para que el dato siga siendo el del primer inicio real.
    """

    permission_classes = [IsAuthenticated, EsPesaje]

    @transaction.atomic
    def patch(self, request, pk):
        orden = bloquear_orden(pk, OrdenProduccion.Estado.PESAJE)
        registro = get_object_or_404(RegistroPesaje, orden=orden)
        if registro.fecha_inicio_pesaje is None:
            registro.fecha_inicio_pesaje = timezone.now()
            registro.save(update_fields=['fecha_inicio_pesaje', 'fecha_modificacion'])
            registrar_historial(
                orden,
                request.user,
                'pesaje_registro',
                '',
                'Inicio del pesaje de materias primas',
                detalle=f'Operario: {registro.nombre_operario}',
            )
        return Response(OrdenProduccionSerializer(OrdenProduccion.objects.get(pk=pk)).data)


class RevisarPesajeView(APIView):
    permission_classes = [IsAuthenticated, EsSupervisorPesaje]
    devolver = False

    @transaction.atomic
    def patch(self, request, pk):
        orden = bloquear_orden(pk, OrdenProduccion.Estado.SUPERVISION_PESAJE)
        registro = get_object_or_404(RegistroPesaje, orden=orden)
        motivo = ''
        if self.devolver:
            serializer = DevolucionPesajeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            motivo = serializer.validated_data['motivo']
        else:
            # Comprueba integridad incluso si la OP fue alterada fuera de este flujo.
            serializer = RegistroPesajeSerializer(
                registro, data={}, partial=True, context={'orden': orden, 'enviar': True}
            )
            serializer.is_valid(raise_exception=True)
        registro.supervisor = request.user
        registro.fecha_revision = timezone.now()
        registro.revision = (
            RegistroPesaje.Revision.DEVUELTA if self.devolver else RegistroPesaje.Revision.APROBADA
        )
        registro.motivo_devolucion = motivo
        registro.save()
        cambiar_estado(
            orden,
            request.user,
            OrdenProduccion.Estado.PESAJE if self.devolver else OrdenProduccion.Estado.MEZCLA,
            motivo if self.devolver else 'Pesaje aprobado y enviado a Mezcla.',
        )
        return Response(OrdenProduccionSerializer(OrdenProduccion.objects.get(pk=pk)).data)


class DevolverPesajeView(RevisarPesajeView):
    devolver = True
