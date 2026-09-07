<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'

const ESTADO_BADGE = {
  planeacion: 'blue',
  picky: 'navy',
  pesaje: 'navy',
  mezcla: 'navy',
  extrusion: 'navy',
  calidad: 'navy',
  empaque: 'navy',
  finalizada: 'gray',
  cancelada: 'red',
}

const CLASIFICACION_BADGE = {
  urgente: 'amber',
  peligroso: 'red',
  normal: 'gray',
}

const CLASIFICACION_OPCIONES = [
  { value: 'normal', label: 'Proceso normal' },
  { value: 'urgente', label: 'Urgente' },
  { value: 'peligroso', label: 'Producto peligroso' },
]

const route = useRoute()
const auth = useAuthStore()
// Solo Producción (rol 'produccion') diligencia clasificación/observaciones
// al "ingresar a la OP" (ver EsProduccion en el backend); Admin/Supervisor
// las consultan de solo lectura.
const esProduccion = computed(() => auth.rol === 'produccion')

const orden = ref(null)
const cargando = ref(true)

const formIngreso = ref({ clasificacion: 'normal', observaciones: '' })
const guardando = ref(false)
const errorGuardar = ref('')
const guardadoOk = ref(false)

async function cargarOrden() {
  cargando.value = true
  const { data } = await api.get(`/produccion/ordenes/${route.params.id}/`)
  orden.value = data
  formIngreso.value = { clasificacion: data.clasificacion, observaciones: data.observaciones }
  cargando.value = false
}

async function guardarIngreso() {
  errorGuardar.value = ''
  guardadoOk.value = false
  guardando.value = true
  try {
    const { data } = await api.patch(
      `/produccion/ordenes/${route.params.id}/ingresar/`,
      formIngreso.value,
    )
    orden.value = data
    guardadoOk.value = true
  } catch (e) {
    const detalle = e.response?.data?.non_field_errors
    errorGuardar.value = Array.isArray(detalle) ? detalle[0] : 'No se pudo guardar.'
  } finally {
    guardando.value = false
  }
}

function formatearFecha(fecha) {
  if (!fecha) return '—'
  return new Date(`${fecha}T00:00:00`).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatearHora(hora) {
  if (!hora) return '—'
  return new Date(`1970-01-01T${hora}`).toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatearFechaHora(fechaIso) {
  if (!fechaIso) return '—'
  return new Date(fechaIso).toLocaleString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(cargarOrden)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <router-link
      :to="{ name: 'admin-ordenes-produccion' }"
      class="mb-4 inline-block text-sm font-semibold text-accent-blue hover:underline"
    >
      ← Volver a Órdenes de Producción
    </router-link>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando orden…</p>

    <template v-else-if="orden">
      <div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">{{ orden.numero_orden }}</h1>
        <Badge :color="ESTADO_BADGE[orden.estado]">{{ orden.estado_display }}</Badge>
      </div>

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
            <dt class="text-ink-500">Cantidad</dt>
            <dd class="font-medium text-ink-900">
              {{ orden.cantidad }} {{ orden.unidad }}
            </dd>
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

      <section class="rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">Producción</h2>

        <form v-if="esProduccion" class="space-y-4" @submit.prevent="guardarIngreso">
          <fieldset>
            <legend class="mb-1.5 text-sm font-medium text-ink-900">Tipo de orden</legend>
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <label
                v-for="opcion in CLASIFICACION_OPCIONES"
                :key="opcion.value"
                class="flex items-center gap-2 rounded-lg border px-3.5 py-2.5 text-sm"
                :class="
                  formIngreso.clasificacion === opcion.value
                    ? 'border-navy-900 bg-navy-900/5'
                    : 'border-slate-300'
                "
              >
                <input
                  v-model="formIngreso.clasificacion"
                  type="radio"
                  name="clasificacion-ingreso"
                  :value="opcion.value"
                  class="h-4 w-4 border-slate-300"
                />
                <span class="text-ink-900">{{ opcion.label }}</span>
              </label>
            </div>
          </fieldset>
          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-ink-900">Observaciones</span>
            <textarea
              v-model="formIngreso.observaciones"
              rows="4"
              placeholder="Notas para el equipo de producción (opcional)"
              class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
            />
          </label>

          <p v-if="errorGuardar" class="text-sm text-danger">{{ errorGuardar }}</p>
          <p v-if="guardadoOk" class="text-sm font-medium text-navy-900">Guardado correctamente.</p>

          <BaseButton type="submit" variant="primary" class="w-full sm:w-auto" :loading="guardando">
            Guardar
          </BaseButton>
        </form>

        <dl v-else class="space-y-3 text-sm">
          <div>
            <dt class="text-ink-500">Tipo de orden</dt>
            <dd class="mt-1">
              <Badge :color="CLASIFICACION_BADGE[orden.clasificacion]">
                {{ orden.clasificacion_display }}
              </Badge>
            </dd>
          </div>
          <div>
            <dt class="text-ink-500">Observaciones</dt>
            <dd class="mt-1 whitespace-pre-line text-ink-900">
              {{ orden.observaciones || 'Sin observaciones.' }}
            </dd>
          </div>
        </dl>
      </section>
    </template>
  </main>
</template>
