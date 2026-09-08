<script setup>
// Detalle de una OP en Picky: consulta de la orden (solo lectura, Picky no
// modifica los datos originales) + registro de la recepción. En esta
// versión Picky NO registra materiales utilizados ni preparados.
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import OrdenResumen from '../../components/produccion/OrdenResumen.vue'
import OrdenTrazabilidad from '../../components/produccion/OrdenTrazabilidad.vue'
import { CLASIFICACION_BADGE, ESTADO_BADGE, mapearErroresCampo } from '../../utils/ordenes'

const route = useRoute()

const orden = ref(null)
const cargando = ref(true)

const nombreOperario = ref('')
const guardando = ref(false)
const errores = ref({})
const guardadoOk = ref(false)

const enviando = ref(false)
const errorEnvio = ref('')

async function cargarOrden() {
  cargando.value = true
  const { data } = await api.get(`/produccion/ordenes/${route.params.id}/`)
  orden.value = data
  nombreOperario.value = data.nombre_operario_picky
  cargando.value = false
}

async function registrarRecepcion() {
  errores.value = {}
  guardadoOk.value = false
  guardando.value = true
  try {
    const { data } = await api.patch(
      `/produccion/ordenes/${route.params.id}/recepcion-picky/`,
      { nombre_operario_picky: nombreOperario.value },
    )
    orden.value = data
    nombreOperario.value = data.nombre_operario_picky
    guardadoOk.value = true
  } catch (e) {
    errores.value = mapearErroresCampo(e)
  } finally {
    guardando.value = false
  }
}

async function enviarAPesaje() {
  errorEnvio.value = ''
  enviando.value = true
  try {
    const { data } = await api.patch(`/produccion/ordenes/${route.params.id}/enviar-pesaje/`)
    orden.value = data
  } catch (e) {
    const detalle = e.response?.data?.non_field_errors
    errorEnvio.value = Array.isArray(detalle) ? detalle[0] : 'No se pudo enviar la orden a Pesaje.'
  } finally {
    enviando.value = false
  }
}

onMounted(cargarOrden)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <router-link
      :to="{ name: 'picky-ordenes' }"
      class="mb-4 inline-block text-sm font-semibold text-accent-blue hover:underline"
    >
      ← Volver a Picky
    </router-link>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando orden…</p>

    <template v-else-if="orden">
      <div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">{{ orden.numero_orden }}</h1>
        <Badge :color="ESTADO_BADGE[orden.estado]">{{ orden.estado_display }}</Badge>
      </div>

      <!-- Lo que dejó Producción: importante para Picky (urgente / peligroso) -->
      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Indicaciones de Producción
        </h2>
        <dl class="space-y-3 text-sm">
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

      <p v-if="guardadoOk" class="mb-4 text-sm font-medium text-navy-900">
        Recepción registrada correctamente.
      </p>

      <OrdenTrazabilidad :orden="orden" />

      <!-- El formulario solo existe mientras la recepción esté pendiente:
           una vez registrada, el dato ya se ve en Trazabilidad. -->
      <section
        v-if="!orden.fecha_recepcion_picky"
        class="mb-6 rounded-xl bg-white p-5 shadow-sm"
      >
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Registrar recepción
        </h2>

        <form class="space-y-4" @submit.prevent="registrarRecepcion">
          <BaseInput
            v-model="nombreOperario"
            label="Nombre del operario de Picky"
            placeholder="ej. Juan Pérez"
            :error="errores.nombre_operario_picky"
            required
          />
          <p class="text-sm text-ink-500">
            La fecha y hora de recepción las registra el sistema automáticamente.
          </p>

          <p v-if="errores.non_field_errors" class="text-sm text-danger">
            {{ errores.non_field_errors }}
          </p>

          <BaseButton type="submit" variant="primary" class="w-full sm:w-auto" :loading="guardando">
            Confirmar recepción
          </BaseButton>
        </form>
      </section>

      <!-- Liberación a Pesaje: solo con la recepción ya registrada -->
      <section
        v-if="orden.estado === 'picky' && orden.fecha_recepcion_picky"
        class="mb-6 rounded-xl bg-white p-5 shadow-sm"
      >
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Finalizar en Picky
        </h2>
        <p class="mb-4 text-sm text-ink-500">
          Al enviarla, la orden pasa a Pesaje y queda registrada la fecha y hora de finalización.
        </p>
        <p v-if="errorEnvio" class="mb-3 text-sm text-danger">{{ errorEnvio }}</p>
        <BaseButton
          variant="primary"
          class="w-full sm:w-auto"
          :loading="enviando"
          @click="enviarAPesaje"
        >
          Enviar a Pesaje
        </BaseButton>
      </section>

      <OrdenResumen :orden="orden" />
    </template>
  </main>
</template>
