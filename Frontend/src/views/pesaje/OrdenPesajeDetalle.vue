<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'
import Badge from '../../components/ui/Badge.vue'
import OrdenResumen from '../../components/produccion/OrdenResumen.vue'
import {
  CLASIFICACION_BADGE,
  ESTADO_BADGE,
  formatearFechaHora,
} from '../../utils/ordenes'

const route = useRoute()

const orden = ref(null)
const cargando = ref(true)
const errorCarga = ref('')

async function cargarOrden() {
  cargando.value = true
  errorCarga.value = ''

  try {
    const { data } = await api.get(
      `/produccion/ordenes/${route.params.id}/`,
    )

    orden.value = data
  } catch (e) {
    errorCarga.value = 'No se pudo cargar la Orden de Producción.'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarOrden)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <router-link
      :to="{ name: 'pesaje-ordenes' }"
      class="mb-4 inline-block text-sm font-semibold text-accent-blue hover:underline"
    >
      ← Volver a Pesaje
    </router-link>

    <p
      v-if="cargando"
      class="py-8 text-center text-sm text-ink-500"
    >
      Cargando orden…
    </p>

    <p
      v-else-if="errorCarga"
      class="py-8 text-center text-sm font-medium text-danger"
    >
      {{ errorCarga }}
    </p>

    <template v-else-if="orden">
      <div
        class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">
            {{ orden.numero_orden }}
          </h1>

          <p class="mt-1 text-sm text-ink-500">
            Orden de Producción en Pesaje
          </p>
        </div>

        <Badge :color="ESTADO_BADGE[orden.estado]">
          {{ orden.estado_display }}
        </Badge>
      </div>

      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2
          class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500"
        >
          Información para Pesaje
        </h2>

        <dl class="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt class="text-ink-500">
              Clasificación
            </dt>

            <dd class="mt-1">
              <Badge :color="CLASIFICACION_BADGE[orden.clasificacion]">
                {{ orden.clasificacion_display }}
              </Badge>
            </dd>
          </div>

          <div>
            <dt class="text-ink-500">
              Fecha de envío a Pesaje
            </dt>

            <dd class="mt-1 font-medium text-ink-900">
              {{ formatearFechaHora(orden.fecha_envio_pesaje) }}
            </dd>
          </div>

          <div class="sm:col-span-2">
            <dt class="text-ink-500">
              Observaciones
            </dt>

            <dd class="mt-1 whitespace-pre-line text-ink-900">
              {{ orden.observaciones || 'Sin observaciones.' }}
            </dd>
          </div>
        </dl>
      </section>

      <OrdenResumen :orden="orden" />

      <section class="rounded-xl bg-white p-5 shadow-sm">
        <p class="text-sm text-ink-500">
          El registro de las cantidades pesadas se realizará en la etapa
          correspondiente del proceso de Pesaje.
        </p>
      </section>
    </template>
  </main>
</template>