<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import { CLASIFICACION_BADGE, ESTADO_BADGE, formatearFechaHora } from '../../utils/ordenes'

const auth = useAuthStore()
// La supervisión de Pesaje la hace el rol 'supervisor' genérico.
const esSupervisor = computed(() => auth.rol === 'supervisor')

// Pesaje solo recibe del backend su propia cola (las OP En Pesaje), así que
// sus grupos distinguen si ya confirmó el recibido. El Supervisor recibe
// todas las OP, por eso su bandeja se acota aquí a las que pasaron por Pesaje.
const FILTROS_PESAJE = [
  { value: 'pendientes', label: 'Pendientes' },
  { value: 'proceso', label: 'En proceso' },
]
const FILTROS_SUPERVISOR = [
  { value: 'revision', label: 'Pendientes de revisión' },
  { value: 'proceso', label: 'En Pesaje' },
  { value: 'liberadas', label: 'Ya liberadas' },
]

const filtros = computed(() => (esSupervisor.value ? FILTROS_SUPERVISOR : FILTROS_PESAJE))
const filtro = ref(esSupervisor.value ? 'revision' : 'pendientes')

const ordenes = ref([])
const cargando = ref(true)
const errorCarga = ref('')

const ordenesDePesaje = computed(() =>
  esSupervisor.value ? ordenes.value.filter((orden) => orden.fecha_envio_pesaje) : ordenes.value,
)

// Pendientes = llegó de Picky pero Pesaje aún no confirma el recibido.
// En proceso = recibido confirmado y sigue En Pesaje.
// Pendientes de revisión / Ya liberadas = etapas que solo ve el Supervisor.
function grupoDe(orden) {
  if (esSupervisor.value) {
    if (orden.estado === 'supervision_pesaje') return 'revision'
    return orden.estado === 'pesaje' ? 'proceso' : 'liberadas'
  }
  return orden.pesaje ? 'proceso' : 'pendientes'
}

const ordenesFiltradas = computed(() =>
  ordenesDePesaje.value.filter((orden) => grupoDe(orden) === filtro.value),
)

function contar(valorFiltro) {
  return ordenesDePesaje.value.filter((orden) => grupoDe(orden) === valorFiltro).length
}

async function cargarOrdenes() {
  cargando.value = true
  errorCarga.value = ''

  try {
    const { data } = await api.get('/produccion/ordenes/')
    ordenes.value = data
  } catch {
    errorCarga.value = 'No se pudieron cargar las Órdenes de Producción.'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarOrdenes)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <div class="mb-4">
      <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">
        {{ esSupervisor ? 'Supervisión de Pesaje' : 'Pesaje' }}
      </h1>

      <p class="mt-1 text-sm text-ink-500">
        {{
          esSupervisor
            ? 'Órdenes de Producción que pasaron por Pesaje.'
            : 'Órdenes de Producción recibidas de Picky.'
        }}
      </p>
    </div>

    <div class="mb-6 flex gap-2 overflow-x-auto pb-1">
      <button
        v-for="opcion in filtros"
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

    <p v-if="errorCarga" class="mb-4 text-sm font-medium text-danger">
      {{ errorCarga }}
    </p>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando órdenes…</p>

    <p
      v-else-if="!errorCarga && ordenesFiltradas.length === 0"
      class="py-8 text-center text-sm text-ink-500"
    >
      No hay Órdenes de Producción en esta vista.
    </p>

    <div v-else-if="!errorCarga" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="orden in ordenesFiltradas"
        :key="orden.id"
        class="flex flex-col gap-3 rounded-xl bg-white p-5 shadow-sm"
      >
        <div class="flex items-start justify-between gap-2">
          <span class="font-semibold text-ink-900">
            {{ orden.numero_orden }}
          </span>

          <Badge :color="ESTADO_BADGE[orden.estado]">
            {{ orden.estado_display }}
          </Badge>
        </div>

        <dl class="space-y-2 text-sm">
          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Producto</dt>

            <dd class="text-right font-medium text-ink-900">
              {{ orden.referencia }}
            </dd>
          </div>

          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Código</dt>

            <dd class="text-right font-medium text-ink-900">
              {{ orden.codigo_producto }}
            </dd>
          </div>

          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Cantidad</dt>

            <dd class="text-right font-medium text-ink-900">
              {{ orden.cantidad }} {{ orden.unidad }}
            </dd>
          </div>

          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">Materias primas</dt>

            <dd class="text-right font-medium text-ink-900">
              {{ orden.materiales.length }}
            </dd>
          </div>

          <div class="flex justify-between gap-3">
            <dt class="text-ink-500">
              {{ esSupervisor ? 'Enviada a supervisión' : 'Enviada a Pesaje' }}
            </dt>

            <dd class="text-right font-medium text-ink-900">
              {{
                formatearFechaHora(
                  esSupervisor ? orden.pesaje?.fecha_envio_supervision : orden.fecha_envio_pesaje,
                )
              }}
            </dd>
          </div>
        </dl>

        <div class="flex flex-wrap gap-2">
          <Badge :color="CLASIFICACION_BADGE[orden.clasificacion]">
            {{ orden.clasificacion_display }}
          </Badge>
          <Badge v-if="orden.es_critico_pesaje" color="red">⚠️ Producto crítico</Badge>
          <Badge v-if="!orden.pesaje && !esSupervisor" color="gray">Pendiente de recibir</Badge>
          <Badge v-if="orden.pesaje?.revision === 'devuelta'" color="red">Devuelta a Pesaje</Badge>
        </div>

        <div class="mt-auto pt-2">
          <router-link
            :to="{
              name: esSupervisor ? 'supervision-pesaje-detalle' : 'pesaje-orden-detalle',
              params: { id: orden.id },
            }"
            class="inline-flex w-full items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-ink-900 shadow-sm transition-colors hover:bg-surface-alt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-900"
          >
            {{ esSupervisor ? 'Revisar' : 'Visualizar' }}
          </router-link>
        </div>
      </div>
    </div>
  </main>
</template>
