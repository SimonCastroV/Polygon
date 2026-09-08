<script setup>
// Trazabilidad compartida: hitos de Picky y eventos de Pesaje/supervisión
// del mismo HistorialOrdenProduccion, incluidos todos los ciclos de devolución.
import { computed } from 'vue'
import { formatearFechaHora } from '../../utils/ordenes'

const props = defineProps({
  orden: {
    type: Object,
    required: true,
  },
})

const eventosPesaje = computed(() =>
  (props.orden.historial || []).filter(
    (evento) =>
      evento.campo === 'pesaje_registro' ||
      evento.campo === 'grupo_critico_pesaje' ||
      (evento.campo === 'estado' &&
        (['pesaje', 'supervision_pesaje'].includes(evento.valor_nuevo) ||
          evento.valor_anterior === 'supervision_pesaje')),
  ),
)

function tituloEvento(evento) {
  if (evento.campo === 'grupo_critico_pesaje') return 'Clasificación del producto para Pesaje'
  if (evento.campo === 'pesaje_registro') return evento.valor_nuevo
  if (evento.valor_nuevo === 'supervision_pesaje') return 'Enviada a supervisión de Pesaje'
  if (evento.valor_nuevo === 'mezcla') return 'Aprobada y enviada a Mezcla'
  if (evento.valor_anterior === 'supervision_pesaje') return 'Devuelta a Pesaje'
  return 'Enviada desde Picky a Pesaje'
}
</script>

<template>
  <!-- Solo aparece cuando la OP ya salió de Producción -->
  <section
    v-if="orden.fecha_envio_picky || orden.pesaje || eventosPesaje.length"
    class="mb-6 rounded-xl bg-white p-5 shadow-sm"
  >
    <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">Trazabilidad</h2>
    <dl class="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
      <div>
        <dt class="text-ink-500">Enviada a Picky</dt>
        <dd class="font-medium text-ink-900">{{ formatearFechaHora(orden.fecha_envio_picky) }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Recibida en Picky</dt>
        <dd class="font-medium text-ink-900">
          {{ formatearFechaHora(orden.fecha_recepcion_picky) }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-500">Operario de Picky</dt>
        <dd class="font-medium text-ink-900">{{ orden.nombre_operario_picky || '—' }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Estación que recibió</dt>
        <dd class="font-medium text-ink-900">{{ orden.recibida_por_picky_username || '—' }}</dd>
      </div>
      <div v-if="orden.fecha_envio_pesaje">
        <dt class="text-ink-500">Finalizada en Picky · Enviada a Pesaje</dt>
        <dd class="font-medium text-ink-900">{{ formatearFechaHora(orden.fecha_envio_pesaje) }}</dd>
      </div>
    </dl>
    <dl
      v-if="orden.pesaje"
      class="mt-4 grid grid-cols-1 gap-x-6 gap-y-3 border-t border-slate-100 pt-4 text-sm sm:grid-cols-2"
    >
      <div>
        <dt class="text-ink-500">Recepción en Pesaje · Primer registro</dt>
        <dd class="font-medium text-ink-900">
          {{ formatearFechaHora(orden.pesaje.fecha_recepcion) }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-500">Último registro de Pesaje</dt>
        <dd class="font-medium text-ink-900">
          {{ orden.pesaje.nombre_operario || '—' }} · {{ orden.pesaje.registrado_por_username }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-500">Envío a supervisión</dt>
        <dd class="font-medium text-ink-900">
          {{ formatearFechaHora(orden.pesaje.fecha_envio_supervision) }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-500">Revisión</dt>
        <dd class="font-medium text-ink-900">{{ orden.pesaje.revision_display || 'Borrador' }}</dd>
      </div>
      <div v-if="orden.pesaje.supervisor_username">
        <dt class="text-ink-500">Supervisor que revisó</dt>
        <dd class="font-medium text-ink-900">
          {{ orden.pesaje.supervisor_username }} ·
          {{ formatearFechaHora(orden.pesaje.fecha_revision) }}
        </dd>
      </div>
    </dl>
    <ol v-if="eventosPesaje.length" class="mt-4 space-y-3 border-t border-slate-100 pt-4 text-sm">
      <li v-for="evento in eventosPesaje" :key="evento.id">
        <p class="font-medium text-ink-900">{{ tituloEvento(evento) }}</p>
        <p class="text-ink-500">
          {{ evento.modificado_por_username || '—' }} · {{ formatearFechaHora(evento.fecha) }}
        </p>
        <p v-if="evento.detalle" class="whitespace-pre-line text-ink-900">{{ evento.detalle }}</p>
      </li>
    </ol>
  </section>
</template>
