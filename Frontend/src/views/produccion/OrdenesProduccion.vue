<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'

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

const ESTADOS_NO_DISPONIBLES = ['finalizada', 'cancelada']

const auth = useAuthStore()
// Producción "ingresa" a la OP para diligenciar clasificación/observaciones;
// Admin/Supervisor solo la consultan (ver PuedeVerOP / EsProduccion en el backend).
const textoBoton = computed(() => (auth.rol === 'produccion' ? 'Ingresar a OP' : 'Ver detalle'))

const ordenes = ref([])
const cargando = ref(true)

const ordenesDisponibles = computed(() =>
  ordenes.value.filter((orden) => !ESTADOS_NO_DISPONIBLES.includes(orden.estado)),
)

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
    <div class="mb-6">
      <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">Órdenes de Producción</h1>
      <p class="mt-1 text-sm text-ink-500">Órdenes disponibles (en curso, sin finalizar ni cancelar).</p>
    </div>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando órdenes…</p>
    <p v-else-if="ordenesDisponibles.length === 0" class="py-8 text-center text-sm text-ink-500">
      No hay Órdenes de Producción disponibles en este momento.
    </p>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="orden in ordenesDisponibles"
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
        </dl>

        <router-link
          :to="{ name: 'admin-orden-detalle', params: { id: orden.id } }"
          class="mt-1 inline-flex items-center justify-center gap-2 rounded-lg bg-navy-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-navy-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-900"
        >
          {{ textoBoton }}
        </router-link>
      </div>
    </div>
  </main>
</template>
