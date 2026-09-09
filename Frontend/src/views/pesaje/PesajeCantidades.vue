<script setup>
// Hoja de proceso de Pesaje: los datos del encabezado llegan de la OP (solo
// lectura) y el operario únicamente registra el peso real de cada materia
// prima. Las horas las sella el servidor. La trazabilidad se consulta en el
// detalle de la OP, no se repite aquí.
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../services/api'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import { ESTADO_BADGE, formatearFechaHora, mapearErroresCampo } from '../../utils/ordenes'

const route = useRoute()
const router = useRouter()

const orden = ref(null)
const cargando = ref(true)
const errorCarga = ref('')
const enviando = ref(false)
const mensajeBloqueo = ref('')
const pesos = ref([])

const registro = computed(() => orden.value?.pesaje || null)
const esCritico = computed(() => orden.value?.es_critico_pesaje === true)
const enPesaje = computed(() => orden.value?.estado === 'pesaje')

// Solo presentación: conserva los decimales significativos, sin redondear.
function formatearCantidad(valor) {
  return String(valor ?? '').replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1')
}

const unidad = computed(() => orden.value?.unidad?.trim() || '')

function mostrarOrden(data) {
  orden.value = data
  pesos.value = data.materiales.map((material) => ({
    material: material.id,
    peso_real: formatearCantidad(
      data.pesaje?.pesos?.find((peso) => peso.material === material.id)?.peso_real ?? '',
    ),
  }))
}

async function cargarOrden() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const { data } = await api.get(`/produccion/ordenes/${route.params.id}/`)
    mostrarOrden(data)
    if (!data.pesaje) {
      errorCarga.value = 'Primero confirme el recibido de la OP en el detalle de Pesaje.'
      return
    }
    if (data.estado !== 'pesaje') {
      errorCarga.value = `Esta OP ya no está en Pesaje: su estado es “${data.estado_display}”.`
      return
    }
    // Sella la hora de inicio del pesaje (H.INC de la hoja de proceso).
    const respuesta = await api.patch(`/produccion/ordenes/${route.params.id}/pesaje/iniciar/`)
    mostrarOrden(respuesta.data)
  } catch {
    errorCarga.value = 'No se pudo abrir el pesaje. Vuelva al detalle de la OP.'
  } finally {
    cargando.value = false
  }
}

function pesoValido(valor) {
  const texto = String(valor || '').trim()
  return texto !== '' && Number.isFinite(Number(texto)) && Number(texto) > 0
}

async function enviarASupervisor() {
  if (enviando.value) return
  mensajeBloqueo.value = ''
  const faltantes = orden.value.materiales.filter((_, i) => !pesoValido(pesos.value[i].peso_real))
  if (!orden.value.materiales.length) {
    mensajeBloqueo.value = 'Esta OP no tiene materias primas cargadas. Avise a administración.'
    return
  }
  if (faltantes.length) {
    mensajeBloqueo.value = `Falta registrar el peso de ${faltantes.length} materia(s) prima(s). Todos los pesos deben ser mayores que cero.`
    return
  }
  enviando.value = true
  try {
    await api.patch(`/produccion/ordenes/${route.params.id}/pesaje/enviar-supervisor/`, {
      pesos: pesos.value.map((peso) => ({ material: peso.material, peso_real: peso.peso_real })),
    })
    router.push({ name: 'pesaje-ordenes' })
  } catch (e) {
    const errores = mapearErroresCampo(e)
    mensajeBloqueo.value =
      errores.pesos ||
      errores.detail ||
      errores.non_field_errors ||
      'No se pudo enviar a supervisor. Revise la verificación en el detalle de la OP.'
  } finally {
    enviando.value = false
  }
}

onMounted(cargarOrden)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <router-link
      :to="{ name: 'pesaje-orden-detalle', params: { id: route.params.id } }"
      class="mb-4 inline-block text-sm font-semibold text-accent-blue hover:underline"
    >
      ← Volver al detalle de Pesaje
    </router-link>

    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando orden…</p>
    <p v-else-if="errorCarga" class="py-8 text-center text-base font-medium text-danger">
      {{ errorCarga }}
    </p>

    <template v-else-if="orden">
      <div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">{{ orden.numero_orden }}</h1>
          <p class="mt-1 text-sm text-ink-500">Hoja de proceso de Pesaje</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <Badge v-if="esCritico" color="red">⚠️ Producto crítico</Badge>
          <Badge :color="ESTADO_BADGE[orden.estado]">{{ orden.estado_display }}</Badge>
        </div>
      </div>

      <!-- Encabezado de la hoja: llega de la OP, el operario no lo digita. -->
      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-1 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Datos de la orden
        </h2>
        <p class="mb-4 text-sm text-ink-500">Vienen de la OP. No se modifican aquí.</p>
        <dl class="grid grid-cols-1 gap-x-6 gap-y-4 text-base sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt class="text-sm text-ink-500">Lote</dt>
            <dd class="font-semibold text-ink-900">{{ registro.lote_actual || '—' }}</dd>
          </div>
          <div>
            <dt class="text-sm text-ink-500">Código</dt>
            <dd class="font-semibold text-ink-900">{{ orden.codigo_producto }}</dd>
          </div>
          <div>
            <dt class="text-sm text-ink-500">Referencia</dt>
            <dd class="font-semibold text-ink-900">{{ orden.referencia }}</dd>
          </div>
          <div>
            <dt class="text-sm text-ink-500">Cantidad</dt>
            <dd class="font-semibold text-ink-900">{{ orden.cantidad }} {{ orden.unidad }}</dd>
          </div>
          <div>
            <dt class="text-sm text-ink-500">Cliente</dt>
            <dd class="font-semibold text-ink-900">{{ orden.cliente || '—' }}</dd>
          </div>
        </dl>
      </section>

      <!-- Único dato que registra el operario en esta pantalla. -->
      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-1 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Pesaje de materias primas
        </h2>
        <p class="mb-4 text-sm text-ink-500">
          Registre el peso real de cada materia prima. La cantidad de la fórmula no se modifica.
        </p>

        <p v-if="!orden.materiales.length" class="py-6 text-center text-sm text-ink-500">
          Esta orden no tiene materias primas registradas.
        </p>

        <ul v-else class="space-y-3">
          <li
            v-for="(material, index) in orden.materiales"
            :key="material.id"
            class="rounded-lg border border-slate-200 p-4"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div class="min-w-0">
                <p class="text-base font-semibold text-ink-900">{{ material.descripcion }}</p>
                <p class="mt-0.5 text-sm text-ink-500">
                  {{ material.codigo }} · Fórmula:
                  <span class="font-medium text-ink-900 tabular-nums">
                    {{ formatearCantidad(material.cantidad) }} {{ unidad }}
                  </span>
                </p>
              </div>
              <label class="block sm:w-56">
                <span class="mb-1.5 block text-sm font-medium text-ink-900">Peso real</span>
                <div class="flex items-center gap-2">
                  <input
                    v-model="pesos[index].peso_real"
                    type="number"
                    inputmode="decimal"
                    min="0.0001"
                    step="0.0001"
                    :disabled="enviando || !enPesaje"
                    class="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-base text-ink-900 tabular-nums outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
                  />
                  <span v-if="unidad" class="shrink-0 text-sm text-ink-500">{{ unidad }}</span>
                </div>
              </label>
            </div>
          </li>
        </ul>
      </section>

      <!-- "DATOS PESAJE" de la hoja: los sella el servidor, no se digitan. -->
      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-1 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Datos del pesaje
        </h2>
        <p class="mb-4 text-sm text-ink-500">Los registra el sistema automáticamente.</p>
        <dl class="grid grid-cols-1 gap-x-6 gap-y-4 text-base sm:grid-cols-3">
          <div>
            <dt class="text-sm text-ink-500">Operario</dt>
            <dd class="font-semibold text-ink-900">{{ registro.nombre_operario || '—' }}</dd>
          </div>
          <div>
            <dt class="text-sm text-ink-500">Inicio</dt>
            <dd class="font-semibold text-ink-900">
              {{ formatearFechaHora(registro.fecha_inicio_pesaje) }}
            </dd>
          </div>
          <div>
            <dt class="text-sm text-ink-500">Fin</dt>
            <dd class="font-semibold text-ink-900">
              {{
                registro.fecha_envio_supervision
                  ? formatearFechaHora(registro.fecha_envio_supervision)
                  : 'Al enviar a supervisor'
              }}
            </dd>
          </div>
        </dl>
      </section>

      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <p class="mb-4 text-sm text-ink-500">
          Al enviar, la OP pasa a revisión del Supervisor. No avanza a Mezcla hasta que él la
          apruebe.
        </p>
        <p v-if="mensajeBloqueo" role="alert" class="mb-4 text-sm font-medium text-danger">
          {{ mensajeBloqueo }}
        </p>
        <BaseButton
          variant="primary"
          class="w-full py-3 text-base sm:w-auto"
          :loading="enviando"
          @click="enviarASupervisor"
        >
          Enviar a supervisor
        </BaseButton>
      </section>
    </template>
  </main>
</template>
