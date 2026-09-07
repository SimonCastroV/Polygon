<script setup>
// Trazabilidad de la liberación Producción → Picky: cuándo se envió, quién
// la recibió y cuándo. Es un bloque aparte porque cada pantalla lo ubica en
// un lugar distinto (en Picky va arriba, junto a las indicaciones).
import { formatearFechaHora } from '../../utils/ordenes'

defineProps({
  orden: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <!-- Solo aparece cuando la OP ya salió de Producción -->
  <section v-if="orden.fecha_envio_picky" class="mb-6 rounded-xl bg-white p-5 shadow-sm">
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
  </section>
</template>
