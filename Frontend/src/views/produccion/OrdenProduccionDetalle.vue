<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import OrdenResumen from '../../components/produccion/OrdenResumen.vue'
import OrdenTrazabilidad from '../../components/produccion/OrdenTrazabilidad.vue'
import {
  CLASIFICACION_BADGE,
  CLASIFICACION_OPCIONES,
  ESTADO_BADGE,
  GRUPO_CRITICO_OPCIONES,
} from '../../utils/ordenes'

const route = useRoute()
const auth = useAuthStore()
// Solo Producción (rol 'produccion') diligencia clasificación/observaciones
// y libera la OP a Picky (ver EsProduccion en el backend); Admin/Supervisor
// las consultan de solo lectura.
const esProduccion = computed(() => auth.rol === 'produccion')

const orden = ref(null)
const cargando = ref(true)

const formIngreso = ref({ clasificacion: 'normal', observaciones: '', grupo_critico_pesaje: '' })
const guardando = ref(false)
const errorGuardar = ref('')
const guardadoOk = ref(false)
// La clasificación se congela cuando Pesaje ya envió su formulario a
// supervisión: cambiarla ahí invalidaría las respuestas ya dadas.
const grupoBloqueado = computed(() => Boolean(orden.value?.pesaje?.fecha_envio_supervision))

const enviando = ref(false)
const errorEnvio = ref('')

const puedeEnviarAPicky = computed(
  () => esProduccion.value && orden.value?.estado === 'produccion',
)

async function cargarOrden() {
  cargando.value = true
  const { data } = await api.get(`/produccion/ordenes/${route.params.id}/`)
  orden.value = data
  formIngreso.value = {
    clasificacion: data.clasificacion,
    observaciones: data.observaciones,
    grupo_critico_pesaje: data.grupo_critico_pesaje,
  }
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
    const datos = e.response?.data || {}
    const detalle = datos.non_field_errors || datos.grupo_critico_pesaje
    errorGuardar.value = Array.isArray(detalle) ? detalle[0] : detalle || 'No se pudo guardar.'
  } finally {
    guardando.value = false
  }
}

async function mandarAPicky() {
  errorEnvio.value = ''
  enviando.value = true
  try {
    const { data } = await api.patch(`/produccion/ordenes/${route.params.id}/enviar-picky/`)
    orden.value = data
  } catch (e) {
    const detalle = e.response?.data?.non_field_errors
    errorEnvio.value = Array.isArray(detalle)
      ? detalle[0]
      : 'No se pudo mandar la orden a Picky.'
  } finally {
    enviando.value = false
  }
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

      <!-- El grupo de producto se muestra y se edita en el bloque "Producción". -->
      <OrdenResumen :orden="orden" :mostrar-grupo-pesaje="false" />

      <OrdenTrazabilidad :orden="orden" />

      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
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
            <span class="mb-1.5 block text-sm font-medium text-ink-900">
              Grupo de producto para Pesaje
            </span>
            <select
              v-model="formIngreso.grupo_critico_pesaje"
              :disabled="grupoBloqueado"
              class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20 disabled:cursor-not-allowed disabled:bg-surface-alt"
            >
              <option v-for="opcion in GRUPO_CRITICO_OPCIONES" :key="opcion.value" :value="opcion.value">
                {{ opcion.label }}
              </option>
            </select>
            <span class="mt-1 block text-sm text-ink-500">
              {{
                grupoBloqueado
                  ? 'Pesaje ya envió el formulario a supervisión: la clasificación quedó fija.'
                  : 'Blancos, Aditivos / Retardantes y Hojas azules son productos críticos: Pesaje responderá el formulario de condiciones especiales.'
              }}
            </span>
          </label>

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
            <dt class="text-ink-500">Grupo de producto para Pesaje</dt>
            <dd class="mt-1">
              <Badge :color="orden.es_critico_pesaje ? 'red' : 'gray'">
                {{ orden.grupo_critico_pesaje_display || 'Sin clasificar' }}
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

      <!-- Liberación a Picky: solo Producción y solo mientras la OP siga aquí -->
      <section v-if="esProduccion" class="rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Liberar a Picky
        </h2>

        <template v-if="puedeEnviarAPicky">
          <p class="mb-4 text-sm text-ink-500">
            Al mandarla, la orden pasa a Picky y queda registrada la fecha y hora del envío.
          </p>
          <p v-if="errorEnvio" class="mb-3 text-sm text-danger">{{ errorEnvio }}</p>
          <BaseButton
            variant="primary"
            class="w-full sm:w-auto"
            :loading="enviando"
            @click="mandarAPicky"
          >
            Mandar orden a Picky
          </BaseButton>
        </template>

        <p v-else class="text-sm text-ink-500">
          Esta orden ya salió de Producción; su estado actual es
          <span class="font-semibold text-ink-900">{{ orden.estado_display }}</span
          >.
        </p>
      </section>
    </template>
  </main>
</template>
