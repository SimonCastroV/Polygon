<script setup>
// Pantalla principal de Picky: las OP que Producción ya liberó, incluidas
// las que Picky ya pasó a Pesaje (ver ordenes_visibles_para en el backend).
import { computed, onMounted, ref } from 'vue'
import api from '../../services/api'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import { CLASIFICACION_BADGE, ESTADO_BADGE, formatearFechaHora } from '../../utils/ordenes'

const FILTROS = [
  { value: 'pendientes', label: 'Pendientes' },
  { value: 'proceso', label: 'En proceso' },
  { value: 'liberadas', label: 'Ya liberado' },
]

const filtro = ref('pendientes')

const ordenes = ref([])
const cargando = ref(true)
const enviandoId = ref(null)
const errorEnvio = ref('')

// Pendiente = llegó de Producción pero Picky aún no confirma la recepción.
// En proceso = recepción confirmada y sigue En Picky.
// Ya liberado = Picky ya la envió a Pesaje.
function grupoDe(orden) {
  if (orden.estado !== 'picky') return 'liberadas'
  return orden.fecha_recepcion_picky ? 'proceso' : 'pendientes'
}

const ordenesFiltradas = computed(() =>
  ordenes.value.filter((orden) => grupoDe(orden) === filtro.value),
)

function contar(valorFiltro) {
  return ordenes.value.filter((orden) => grupoDe(orden) === valorFiltro).length
}

async function cargarOrdenes() {
  cargando.value = true
  const { data } = await api.get('/produccion/ordenes/')
  ordenes.value = data
  cargando.value = false
}

async function enviarAPesaje(orden) {
  errorEnvio.value = ''
  enviandoId.value = orden.id
  try {
    await api.patch(`/produccion/ordenes/${orden.id}/enviar-pesaje/`)
    await cargarOrdenes()
  } catch (e) {
    const detalle = e.response?.data?.non_field_errors
    errorEnvio.value = Array.isArray(detalle) ? detalle[0] : 'No se pudo enviar la orden a Pesaje.'
  } finally {
    enviandoId.value = null
  }
}

onMounted(cargarOrdenes)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <div class="mb-4">
      <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">Picky</h1>
      <p class="mt-1 text-sm text-ink-500">Órdenes de Producción recibidas de Producción.</p>
    </div>

    <div class="mb-6 flex gap-2 overflow-x-auto pb-1">
      <button
        v-for="opcion in FILTROS"
        :key="opcion.value"
        type="button"
        class="shrink-0 rounded-lg border px-3.5 py-2 text-sm font-semibold transition-colors"
        :class="
          filtro === opcion.value
            ? 'border-navy-900 bg-navy-900 text-white'
            : 'border-slate-300 bg-white text-ink-900 hover:bg-surface-alt'
        "
        @click="filtro = opcion.value"
      >
        {{ opcion.label }} ({{ contar(opcion.value) }})
      </button>
    </div>

    <p v-if="errorEnvio" class="mb-4 text-sm font-medium text-danger">{{ errorEnvio }}</p>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando órdenes…</p>
    <p v-else-if="ordenesFiltradas.length === 0" class="py-8 text-center text-sm text-ink-500">
      No hay Órdenes de Producción en esta vista.
    </p>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="orden in ordenesFiltradas"
        :key="orden.id"
        class="flex flex-col gap-3 rounded-xl bg-white p-5 shadow-sm"
      >
        <div class="flex items-start justify-between gap-2">
          <span class="font-semibold text-ink-900">{{ orden.numero_orden }}</span>
          <Badge :color="ESTADO_BADGE[orden.estado]">{{ orden.estado_display }}</Badge>
        </div>

        <dl class="space-y-1 text-sm">
          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Producto</dt>
            <dd class="text-right font-medium text-ink-900">{{ orden.referencia }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Cantidad</dt>
            <dd class="text-right font-medium text-ink-900">
              {{ orden.cantidad }} {{ orden.unidad }}
            </dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Recibida el</dt>
            <dd class="text-right font-medium text-ink-900">
              {{ formatearFechaHora(orden.fecha_envio_picky) }}
            </dd>
          </div>
          <div v-if="orden.fecha_envio_pesaje" class="flex justify-between gap-3">
            <dt class="text-ink-500">Enviada a Pesaje</dt>
            <dd class="text-right font-medium text-ink-900">
              {{ formatearFechaHora(orden.fecha_envio_pesaje) }}
            </dd>
          </div>
        </dl>

        <div class="flex flex-wrap gap-2">
          <Badge :color="CLASIFICACION_BADGE[orden.clasificacion]">
            {{ orden.clasificacion_display }}
          </Badge>
          <Badge v-if="!orden.fecha_recepcion_picky" color="gray">Pendiente de recibir</Badge>
        </div>

        <div class="mt-auto flex flex-col gap-2 pt-1">
          <BaseButton
            v-if="grupoDe(orden) === 'proceso'"
            variant="primary"
            class="w-full"
            :loading="enviandoId === orden.id"
            @click="enviarAPesaje(orden)"
          >
            Enviar a Pesaje
          </BaseButton>
          <router-link
            :to="{ name: 'picky-orden-detalle', params: { id: orden.id } }"
            class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-ink-900 shadow-sm transition-colors hover:bg-surface-alt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-900"
          >
            Visualizar
          </router-link>
        </div>
      </div>
    </div>
  </main>
</template>
