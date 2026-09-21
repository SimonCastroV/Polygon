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
  mapearErroresCampo,
} from '../../utils/ordenes'

const route = useRoute()
const auth = useAuthStore()
// Solo Producción (rol 'produccion') diligencia la hoja de la OP y la
// libera a Picking (ver EsProduccion en el backend); Admin, Supervisor e
// Ing. Producción la consultan de solo lectura.
const esProduccion = computed(() => auth.rol === 'produccion')

const orden = ref(null)
const cargando = ref(true)

const formIngreso = ref({ clasificacion: 'normal', observaciones: '', grupo_critico_pesaje: '' })

const enviando = ref(false)
const errorEnvio = ref('')

// La hoja solo se diligencia mientras la OP sigue En Producción: se guarda al
// mandarla a Picking (no hay un botón Guardar aparte) y después queda de
// solo lectura, porque Pesaje responde su formulario según el grupo elegido.
const puedeEnviarAPicking = computed(
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

// Guarda lo diligenciado y manda la OP a Picking en una sola acción: el
// backend lo hace en una transacción, así que o queda todo o no queda nada.
async function mandarAPicking() {
  if (enviando.value) return
  errorEnvio.value = ''
  enviando.value = true
  try {
    const { data } = await api.patch(
      `/produccion/ordenes/${route.params.id}/enviar-picking/`,
      formIngreso.value,
    )
    orden.value = data
  } catch (e) {
    const errores = mapearErroresCampo(e)
    errorEnvio.value =
      errores.non_field_errors ||
      errores.clasificacion ||
      errores.grupo_critico_pesaje ||
      errores.observaciones ||
      errores.detail ||
      'No se pudo mandar la orden a Picking. Lo diligenciado no se perdió: intente nuevamente.'
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

        <form v-if="puedeEnviarAPicking" class="space-y-4" @submit.prevent>
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
              class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
            >
              <option v-for="opcion in GRUPO_CRITICO_OPCIONES" :key="opcion.value" :value="opcion.value">
                {{ opcion.label }}
              </option>
            </select>
            <span class="mt-1 block text-sm text-ink-500">
              Blancos, Aditivos / Retardantes y Producto peligroso son productos críticos: Pesaje
              responderá el formulario de condiciones especiales.
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

      <!-- Liberación a Picking: solo Producción y solo mientras la OP siga aquí -->
      <section v-if="esProduccion" class="rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Liberar a Picking
        </h2>

        <template v-if="puedeEnviarAPicking">
          <p class="mb-4 text-sm text-ink-500">
            Al mandarla se guarda lo diligenciado arriba (tipo de orden, grupo para Pesaje y
            observaciones), la orden pasa a Picking y queda registrada la fecha y hora del envío.
            Después ya no se puede modificar.
          </p>
          <p v-if="errorEnvio" role="alert" class="mb-3 text-sm font-medium text-danger">
            {{ errorEnvio }}
          </p>
          <BaseButton
            variant="primary"
            class="w-full sm:w-auto"
            :loading="enviando"
            @click="mandarAPicking"
          >
            Mandar orden a Picking
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
