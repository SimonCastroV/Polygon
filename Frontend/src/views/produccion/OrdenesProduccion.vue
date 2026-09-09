<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import {
  CLASIFICACION_BADGE,
  ESTADOS_CERRADOS,
  ESTADO_BADGE,
  formatearFechaHora,
} from '../../utils/ordenes'

const auth = useAuthStore()
// Producción "ingresa" a la OP para diligenciar clasificación/observaciones
// y es la única que puede liberarla a Picky (ver EsProduccion en el backend);
// Admin/Supervisor solo consultan.
const esProduccion = computed(() => auth.rol === 'produccion')
const textoBoton = computed(() => (esProduccion.value ? 'Ingresar a OP' : 'Ver detalle'))

const FILTROS = [
  { value: 'pendientes', label: 'Pendientes por enviar' },
  { value: 'proceso', label: 'En proceso' },
  { value: 'todas', label: 'Todas' },
]

// Producción entra a su cola de trabajo; Supervisor/Admin al panorama completo.
const filtro = ref(auth.rol === 'produccion' ? 'pendientes' : 'todas')

const ordenes = ref([])
const cargando = ref(true)

const ordenesActivas = computed(() =>
  ordenes.value.filter((orden) => !ESTADOS_CERRADOS.includes(orden.estado)),
)

const ordenesFiltradas = computed(() => {
  if (filtro.value === 'pendientes') {
    return ordenesActivas.value.filter((orden) => orden.estado === 'produccion')
  }
  if (filtro.value === 'proceso') {
    return ordenesActivas.value.filter((orden) => orden.estado !== 'produccion')
  }
  return ordenesActivas.value
})

function contar(valorFiltro) {
  if (valorFiltro === 'pendientes') {
    return ordenesActivas.value.filter((orden) => orden.estado === 'produccion').length
  }
  if (valorFiltro === 'proceso') {
    return ordenesActivas.value.filter((orden) => orden.estado !== 'produccion').length
  }
  return ordenesActivas.value.length
}

async function cargarOrdenes() {
  cargando.value = true
  const { data } = await api.get('/produccion/ordenes/')
  ordenes.value = data
  cargando.value = false
}

onMounted(cargarOrdenes)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <div class="mb-4">
      <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">Órdenes de Producción</h1>
      <p class="mt-1 text-sm text-ink-500">Órdenes en curso (sin finalizar ni cancelar).</p>
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
            <dt class="text-ink-500">Código</dt>
            <dd class="text-right font-medium text-ink-900">{{ orden.codigo_producto }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Cliente</dt>
            <dd class="text-right font-medium text-ink-900">{{ orden.cliente || '—' }}</dd>
          </div>
          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Producto</dt>
            <dd class="text-right font-medium text-ink-900">{{ orden.referencia }}</dd>
          </div>
          <div v-if="orden.fecha_envio_picky" class="flex justify-between gap-3">
            <dt class="text-ink-500">Enviada a Picky</dt>
            <dd class="text-right font-medium text-ink-900">
              {{ formatearFechaHora(orden.fecha_envio_picky) }}
            </dd>
          </div>
        </dl>

        <div>
          <Badge :color="CLASIFICACION_BADGE[orden.clasificacion]">
            {{ orden.clasificacion_display }}
          </Badge>
        </div>

        <!-- La OP se libera a Picky desde su detalle, no desde la card: así el
             operario ve la orden completa antes de mandarla. -->
        <div class="mt-auto flex flex-col gap-2 pt-1">
          <router-link
            :to="{ name: 'admin-orden-detalle', params: { id: orden.id } }"
            class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-ink-900 shadow-sm transition-colors hover:bg-surface-alt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-900"
          >
            {{ textoBoton }}
          </router-link>
        </div>
      </div>
    </div>
  </main>
</template>
