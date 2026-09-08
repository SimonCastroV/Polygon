<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import { CLASIFICACION_BADGE, ESTADO_BADGE, formatearFechaHora } from '../../utils/ordenes'

const auth = useAuthStore()
const esSupervisor = computed(() => auth.rol === 'supervisor_pesaje')
const ordenes = ref([])
const cargando = ref(true)
const errorCarga = ref('')

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
    <div class="mb-6">
      <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">
        {{ esSupervisor ? 'Supervisión de Pesaje' : 'Pesaje' }}
      </h1>

      <p class="mt-1 text-sm text-ink-500">
        {{
          esSupervisor
            ? 'Órdenes de Producción pendientes de revisión.'
            : 'Órdenes de Producción pendientes de pesaje.'
        }}
      </p>
    </div>

    <p v-if="errorCarga" class="mb-4 text-sm font-medium text-danger">
      {{ errorCarga }}
    </p>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando órdenes…</p>

    <p
      v-else-if="!errorCarga && ordenes.length === 0"
      class="py-8 text-center text-sm text-ink-500"
    >
      {{
        esSupervisor
          ? 'No hay Órdenes de Producción pendientes de revisión.'
          : 'No hay Órdenes de Producción pendientes en Pesaje.'
      }}
    </p>

    <div v-else-if="!errorCarga" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="orden in ordenes"
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
        </div>

        <Badge v-if="orden.pesaje?.revision === 'devuelta'" color="red">Devuelta a Pesaje</Badge>

        <div class="mt-auto pt-2">
          <router-link
            :to="{
              name: esSupervisor ? 'supervision-pesaje-detalle' : 'pesaje-orden-detalle',
              params: { id: orden.id },
            }"
            class="inline-flex w-full items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-ink-900 shadow-sm transition-colors hover:bg-surface-alt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-900"
          >
            {{ esSupervisor ? 'Revisar' : 'Registrar pesaje' }}
          </router-link>
        </div>
      </div>
    </div>
  </main>
</template>
