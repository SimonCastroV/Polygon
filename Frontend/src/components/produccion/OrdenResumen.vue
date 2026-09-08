<script setup>
// Vista de solo lectura del documento de la OP (encabezado de Sumicolor +
// materiales). La comparten el detalle de Producción/Supervisor y el de
// Picky para no duplicarlo en dos pantallas. La trazabilidad va aparte,
// en OrdenTrazabilidad.vue, porque cada pantalla la ubica en otro lugar.
import { formatearFecha, formatearFechaHora, formatearHora } from '../../utils/ordenes'

defineProps({
  orden: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
    <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
      Datos del pedido
    </h2>
    <dl class="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
      <div>
        <dt class="text-ink-500">Código</dt>
        <dd class="font-medium text-ink-900">{{ orden.codigo_producto }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Referencia</dt>
        <dd class="font-medium text-ink-900">{{ orden.referencia }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Grupo de producto para Pesaje</dt>
        <dd class="font-medium text-ink-900">{{ orden.grupo_critico_pesaje_display || 'Sin clasificar' }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Cantidad</dt>
        <dd class="font-medium text-ink-900">{{ orden.cantidad }} {{ orden.unidad }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Cliente</dt>
        <dd class="font-medium text-ink-900">{{ orden.cliente || '—' }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">C. Cliente</dt>
        <dd class="font-medium text-ink-900">{{ orden.codigo_cliente }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Pedido</dt>
        <dd class="font-medium text-ink-900">{{ orden.pedido }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Fecha Pedido</dt>
        <dd class="font-medium text-ink-900">{{ formatearFecha(orden.fecha_pedido) }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Hora Pedido</dt>
        <dd class="font-medium text-ink-900">{{ formatearHora(orden.hora_pedido) }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Vencimiento Pedido</dt>
        <dd class="font-medium text-ink-900">{{ formatearFecha(orden.vencimiento_pedido) }}</dd>
      </div>
      <div>
        <dt class="text-ink-500">Fecha Hora Lote</dt>
        <dd class="font-medium text-ink-900">{{ formatearFechaHora(orden.fecha_hora_lote) }}</dd>
      </div>
    </dl>
  </section>

  <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
    <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">Materiales</h2>
    <div class="overflow-x-auto rounded-lg border border-slate-100">
      <table class="w-full min-w-[560px] text-left text-sm">
        <thead class="bg-surface-alt text-xs font-semibold uppercase text-ink-500">
          <tr>
            <th class="px-4 py-2">Código</th>
            <th class="px-4 py-2">Descripción</th>
            <th class="px-4 py-2">%</th>
            <th class="px-4 py-2">Cantidad</th>
            <th class="px-4 py-2">Localización</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="orden.materiales.length === 0">
            <td colspan="5" class="px-4 py-6 text-center text-ink-500">
              Esta orden no tiene materiales registrados.
            </td>
          </tr>
          <tr v-for="material in orden.materiales" :key="material.id">
            <td class="px-4 py-2 text-ink-900">{{ material.codigo || '—' }}</td>
            <td class="px-4 py-2 text-ink-900">{{ material.descripcion }}</td>
            <td class="px-4 py-2 text-ink-500">{{ material.porcentaje }}%</td>
            <td class="px-4 py-2 text-ink-500">{{ material.cantidad }}</td>
            <td class="px-4 py-2 text-ink-500">{{ material.localizacion || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

</template>
