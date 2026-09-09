<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import OrdenTrazabilidad from '../../components/produccion/OrdenTrazabilidad.vue'
import {
  CLASIFICACION_BADGE,
  ESTADO_BADGE,
  formatearFechaHora,
  mapearErroresCampo,
} from '../../utils/ordenes'
import VerificacionesPesaje from '../../components/produccion/VerificacionesPesaje.vue'
import { cargarVerificaciones } from '../../utils/pesaje'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const esSupervisor = computed(() => auth.rol === 'supervisor')
const rutaBandeja = computed(() =>
  esSupervisor.value ? 'supervision-pesaje-ordenes' : 'pesaje-ordenes',
)
const orden = ref(null)
const cargando = ref(true)
const errorCarga = ref('')
const procesando = ref(false)
const errores = ref({})
const mensaje = ref('')
const form = ref({})
const motivo = ref('')
const editable = computed(() => auth.rol === 'pesaje' && orden.value?.estado === 'pesaje')
const revisable = computed(() => esSupervisor.value && orden.value?.estado === 'supervision_pesaje')
const esCritico = computed(() => orden.value?.es_critico_pesaje === true)
// La OP queda "recibida en Pesaje" en cuanto existe su registro (ver
// confirmarRecepcion): antes de eso solo se muestra el paso de recepción.
const recibidaEnPesaje = computed(() => Boolean(orden.value?.pesaje))
// Definición de los dos formularios, servida por el backend (ver utils/pesaje).
const verificacionesNormales = ref([])
const verificacionesCriticas = ref([])
// Un producto crítico usa exclusivamente el formulario de condiciones
// críticas; uno normal usa exclusivamente el formulario estándar. Nunca se
// muestran ni se exigen los dos a la vez.
const verificacionesAplicables = computed(() =>
  esCritico.value ? verificacionesCriticas.value : verificacionesNormales.value,
)
const noCumple = computed(() =>
  verificacionesAplicables.value.some(([campo]) => form.value[campo] === false),
)
// Campo de observaciones del formulario que esté activo (normal o crítico).
const campoObservaciones = computed(() => (esCritico.value ? 'critico_observaciones' : 'observaciones'))
// Si hay algún "No cumple", ese formulario exige explicarlo en observaciones
// antes de continuar (no bloquea con el "No cumple" en sí, solo exige la
// justificación).
const observacionesRequeridas = computed(() => noCumple.value)

const CAMPOS = [
  ['lote_anterior', 'Lote anterior'],
  ['referencia_anterior', 'Referencia anterior'],
  ['lote_actual', 'Lote actual'],
  ['nombre_operario', 'Nombre del operario de Pesaje'],
]

// Motivo por el que "Empezar pesaje" no avanzó, en lenguaje del operario.
const mensajeBloqueo = ref('')

// Pesos que registró el operario en la hoja de proceso (solo los revisa el
// Supervisor; el operario los captura en PesajeCantidades.vue).
const registroPesaje = computed(() => orden.value?.pesaje || null)
const unidadVisible = computed(() => orden.value?.unidad?.trim() || '')

function formatearCantidad(valor) {
  return String(valor ?? '').replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1')
}

function pesoDe(material) {
  return registroPesaje.value?.pesos?.find((peso) => peso.material === material.id)?.peso_real
}

function pesoRealDe(material) {
  const peso = pesoDe(material)
  return peso ? `${formatearCantidad(peso)} ${unidadVisible.value}`.trim() : 'Pendiente'
}

function diferenciaDe(material) {
  const peso = pesoDe(material)
  if (!peso) return ''
  const diferencia = Number((Number(peso) - Number(material.cantidad)).toFixed(4))
  if (!Number.isFinite(diferencia) || diferencia === 0) return ''
  const signo = diferencia > 0 ? '+' : ''
  return `${signo}${formatearCantidad(diferencia.toFixed(4))} ${unidadVisible.value}`.trim()
}

// El botón nunca se deshabilita: al pulsarlo se marca en rojo lo que falte y
// se explica por qué no avanza.
function validarAvance() {
  const pendientes = {}
  const faltantes = []
  if (!orden.value.grupo_critico_pesaje) {
    pendientes.grupo_critico_pesaje = 'Producto sin clasificar.'
    faltantes.push('la clasificación del producto (solicítela en administración)')
  }
  const camposVacios = CAMPOS.filter(([campo]) => !String(form.value[campo] || '').trim())
  for (const [campo] of camposVacios) pendientes[campo] = 'Este campo es obligatorio.'
  if (camposVacios.length) {
    faltantes.push(camposVacios.map(([, label]) => label.toLowerCase()).join(', '))
  }
  const sinResponder = verificacionesAplicables.value.filter(
    ([campo]) => form.value[campo] === null || form.value[campo] === undefined,
  )
  for (const [campo] of sinResponder) pendientes[campo] = 'Seleccione Cumple o No cumple.'
  if (sinResponder.length) {
    faltantes.push(
      `${sinResponder.length} verificación(es) sin responder`,
    )
  }
  if (noCumple.value && !String(form.value[campoObservaciones.value] || '').trim()) {
    pendientes[campoObservaciones.value] =
      'Explique aquí los puntos marcados “No cumple”. Puede continuar una vez explicados.'
    faltantes.push('la explicación de los puntos marcados “No cumple”')
  }
  errores.value = pendientes
  mensajeBloqueo.value = faltantes.length
    ? `No se puede empezar el pesaje. Falta: ${faltantes.join('; ')}.`
    : ''
  return !faltantes.length
}

// Paso "Confirmar recibido": crea el registro de Pesaje con el operario que
// recibe. Reutiliza el mismo endpoint de guardado (PATCH parcial), igual que
// se persiste el resto del formulario y su trazabilidad.
const nombreRecepcion = ref('')
const confirmandoRecepcion = ref(false)
const erroresRecepcion = ref({})
const recepcionOk = ref(false)

function mostrarOrden(data) {
  orden.value = data
  const registro = data.pesaje || {}
  form.value = {
    ...Object.fromEntries(CAMPOS.map(([campo]) => [campo, registro[campo] || ''])),
    ...Object.fromEntries(
      [...verificacionesNormales.value, ...verificacionesCriticas.value].map(([campo]) => [
        campo,
        registro[campo] ?? null,
      ]),
    ),
    critico_observaciones: registro.critico_observaciones || '',
    observaciones: registro.observaciones || '',
  }
}

async function cargarOrden() {
  cargando.value = true
  errorCarga.value = ''
  orden.value = null
  errores.value = {}
  mensaje.value = ''
  mensajeBloqueo.value = ''
  motivo.value = ''
  nombreRecepcion.value = ''
  erroresRecepcion.value = {}
  recepcionOk.value = false
  try {
    // Las verificaciones deben estar antes de armar el formulario.
    const verificaciones = await cargarVerificaciones()
    verificacionesNormales.value = verificaciones.normales
    verificacionesCriticas.value = verificaciones.criticas
    const { data } = await api.get(`/produccion/ordenes/${route.params.id}/`)
    mostrarOrden(data)
  } catch {
    errorCarga.value =
      'No se pudo cargar la OP. Puede haber cambiado de etapa; vuelva a la bandeja.'
  } finally {
    cargando.value = false
  }
}

async function confirmarRecepcion() {
  if (confirmandoRecepcion.value || !editable.value) return
  erroresRecepcion.value = {}
  recepcionOk.value = false
  if (!nombreRecepcion.value.trim()) {
    erroresRecepcion.value.nombre_operario = 'El nombre del operario de Pesaje es obligatorio.'
    return
  }
  confirmandoRecepcion.value = true
  try {
    const { data } = await api.patch(`/produccion/ordenes/${route.params.id}/pesaje/`, {
      nombre_operario: nombreRecepcion.value.trim(),
    })
    mostrarOrden(data)
    recepcionOk.value = true
  } catch (e) {
    erroresRecepcion.value = mapearErroresCampo(e)
    if (!Object.keys(erroresRecepcion.value).length)
      erroresRecepcion.value.detail = 'No se pudo confirmar la recepción. Intente nuevamente.'
  } finally {
    confirmandoRecepcion.value = false
  }
}

// Una sola acción: valida, guarda la verificación y pasa a la vista de pesaje.
// No hay guardado aparte; lo que se ve en pantalla se persiste al continuar.
async function empezarPesaje() {
  if (procesando.value || !editable.value) return
  errores.value = {}
  mensaje.value = ''
  if (!validarAvance()) return
  procesando.value = true
  try {
    // Solo viaja el formulario que aplica: el backend rechaza el del otro tipo
    // de producto para no guardar respuestas que nadie revisó.
    const payload = { ...form.value }
    const ajenas = esCritico.value
      ? [...verificacionesNormales.value.map(([campo]) => campo), 'observaciones']
      : [...verificacionesCriticas.value.map(([campo]) => campo), 'critico_observaciones']
    for (const campo of ajenas) delete payload[campo]
    await api.patch(`/produccion/ordenes/${route.params.id}/pesaje/`, payload)
    router.push({ name: 'pesaje-orden-pesar', params: { id: route.params.id } })
  } catch (e) {
    errores.value = mapearErroresCampo(e)
    mensajeBloqueo.value =
      errores.value.detail ||
      errores.value.non_field_errors ||
      'No se pudo guardar la verificación. Intente nuevamente.'
  } finally {
    procesando.value = false
  }
}

async function revisar(devolver) {
  if (procesando.value || !revisable.value) return
  errores.value = {}
  mensaje.value = ''
  if (devolver && !motivo.value.trim()) {
    errores.value.motivo = 'El motivo de devolución es obligatorio.'
    return
  }
  procesando.value = true
  try {
    const accion = devolver ? 'devolver' : 'aprobar'
    const { data } = await api.patch(
      `/produccion/ordenes/${route.params.id}/pesaje/${accion}/`,
      devolver ? { motivo: motivo.value } : {},
    )
    mostrarOrden(data)
    mensaje.value = devolver ? 'OP devuelta a Pesaje.' : 'OP aprobada y enviada a Mezcla.'
  } catch (e) {
    errores.value = mapearErroresCampo(e)
    if (!Object.keys(errores.value).length)
      errores.value.detail = 'No se pudo registrar la revisión.'
  } finally {
    procesando.value = false
  }
}

watch(() => route.params.id, cargarOrden, { immediate: true })
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <router-link
      :to="{ name: rutaBandeja }"
      class="mb-4 inline-block text-sm font-semibold text-accent-blue hover:underline"
    >
      ← Volver a {{ esSupervisor ? 'Supervisión de Pesaje' : 'Pesaje' }}
    </router-link>
    <p v-if="cargando" class="py-8 text-center text-sm text-ink-500">Cargando orden…</p>
    <p v-else-if="errorCarga" class="py-8 text-center text-sm font-medium text-danger">
      {{ errorCarga }}
    </p>
    <template v-else-if="orden">
      <div class="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">{{ orden.numero_orden }}</h1>
          <p class="mt-1 text-sm text-ink-500">
            {{ esSupervisor ? 'Revisión de Pesaje' : 'Registro de Pesaje' }}
          </p>
        </div>
        <Badge :color="ESTADO_BADGE[orden.estado]">{{ orden.estado_display }}</Badge>
      </div>

      <!-- Visible desde que se abre la OP, antes de cualquier acción: el operario
           no debe confundir este producto con un pesaje normal. -->
      <section
        v-if="esCritico"
        class="mb-6 rounded-xl border-2 border-danger bg-red-50 p-5 shadow-sm"
      >
        <p class="text-sm font-bold uppercase tracking-wide text-danger">⚠️ Producto crítico</p>
        <p class="mt-1 text-sm text-ink-900">
          Este producto (<span class="font-semibold">{{
            orden.grupo_critico_pesaje_display
          }}</span
          >) tiene condiciones especiales de Pesaje. Además de la verificación estándar, complete
          la verificación de condiciones críticas antes de continuar.
        </p>
      </section>

      <p v-if="mensaje" role="status" class="mb-4 text-sm font-medium text-navy-900">
        {{ mensaje }}
      </p>

      <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Indicaciones de Producción
        </h2>
        <dl class="space-y-3 text-sm">
          <div>
            <dt class="text-ink-500">Clasificación</dt>
            <dd class="mt-1">
              <Badge :color="CLASIFICACION_BADGE[orden.clasificacion]">{{
                orden.clasificacion_display
              }}</Badge>
            </dd>
          </div>
          <div>
            <dt class="text-ink-500">Observaciones de Producción</dt>
            <dd class="mt-1 whitespace-pre-line text-ink-900">
              {{ orden.observaciones || 'Sin observaciones.' }}
            </dd>
          </div>
        </dl>
      </section>

      <OrdenTrazabilidad :orden="orden" solo-pesaje :mostrar-eventos="esSupervisor" />

      <!-- Confirmar recibido: paso obligatorio antes del formulario de verificación.
           Crea el registro de Pesaje (operario + fecha/hora del servidor) y una vez
           hecho, este bloque se reemplaza por el formulario. -->
      <section
        v-if="editable && !recibidaEnPesaje"
        class="mb-6 rounded-xl bg-white p-5 shadow-sm"
      >
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Confirmar recibido
        </h2>
        <p class="mb-4 text-sm text-ink-500">
          Confirme que la Orden de Producción llegó a Pesaje. La fecha y hora las registra el
          sistema automáticamente.
        </p>
        <form class="space-y-4" @submit.prevent="confirmarRecepcion">
          <BaseInput
            v-model="nombreRecepcion"
            label="Nombre del operario de Pesaje"
            placeholder="ej. Juan Pérez"
            :error="erroresRecepcion.nombre_operario"
            required
          />
          <p v-if="erroresRecepcion.detail" class="text-sm text-danger">
            {{ erroresRecepcion.detail }}
          </p>
          <BaseButton
            type="submit"
            variant="primary"
            class="w-full sm:w-auto"
            :loading="confirmandoRecepcion"
          >
            Confirmar recibido
          </BaseButton>
        </form>
      </section>

      <p v-if="recepcionOk" class="mb-4 text-sm font-medium text-navy-900">
        Recepción confirmada correctamente.
      </p>

      <section
        v-if="orden.pesaje?.revision === 'devuelta'"
        class="mb-6 rounded-xl bg-white p-5 shadow-sm"
      >
        <h2 class="mb-2 text-sm font-semibold text-danger">Devuelta a Pesaje</h2>
        <p class="whitespace-pre-line text-sm text-ink-900">{{ orden.pesaje.motivo_devolucion }}</p>
        <p v-if="editable" class="mt-2 text-sm text-ink-500">
          Corrija el registro y envíelo nuevamente a supervisor.
        </p>
      </section>

      <template v-if="recibidaEnPesaje">
        <form novalidate @submit.prevent="empezarPesaje">
          <p v-if="!orden.grupo_critico_pesaje" class="mb-4 text-sm font-medium text-danger">
            Producto sin clasificar para Pesaje. Solicite clasificar el código
            {{ orden.codigo_producto }} en administración.
          </p>
          <!-- Un producto crítico usa exclusivamente el formulario de condiciones
               críticas; uno normal usa exclusivamente el formulario estándar. -->
          <section v-if="!esCritico" class="mb-6 rounded-xl bg-white p-5 shadow-sm">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
              Verificación de limpieza de Pesaje + Despeje de línea
            </h2>
            <fieldset :disabled="!editable || procesando" class="min-w-0 space-y-4">
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <template v-for="[campo, label] in CAMPOS" :key="campo">
                  <BaseInput
                    v-if="editable"
                    v-model="form[campo]"
                    :label="label"
                    :error="errores[campo]"
                    required
                  />
                  <div v-else class="text-sm">
                    <p class="text-ink-500">{{ label }}</p>
                    <p class="font-medium text-ink-900">{{ form[campo] || '—' }}</p>
                  </div>
                </template>
                <div class="text-sm">
                  <p class="text-ink-500">Referencia actual</p>
                  <p class="font-medium text-ink-900">
                    {{ orden.pesaje?.referencia_actual || orden.referencia }}
                  </p>
                </div>
              </div>
              <p v-if="editable" class="text-sm text-ink-500">
                Complete todos los campos y verificaciones. Si no hubo un lote anterior, indique
                “No aplica” en lote y referencia anterior.
              </p>
              <VerificacionesPesaje
                v-model="form"
                :campos="verificacionesNormales"
                :errores="errores"
                :editable="editable"
              />
              <label v-if="editable" class="block">
                <span class="mb-1.5 block text-sm font-medium text-ink-900">
                  Observaciones de Pesaje
                  <span v-if="observacionesRequeridas" class="text-danger">*</span>
                  <span v-else>(opcional)</span>
                </span>
                <textarea
                  v-model="form.observaciones"
                  rows="3"
                  class="w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
                  :class="errores.observaciones ? 'border-danger' : 'border-slate-300'"
                />
                <p v-if="errores.observaciones" class="mt-1 text-sm text-danger">
                  {{ errores.observaciones }}
                </p>
              </label>
              <div v-else class="text-sm">
                <p class="text-ink-500">Observaciones de Pesaje</p>
                <p class="whitespace-pre-line text-ink-900">
                  {{ form.observaciones || 'Sin observaciones.' }}
                </p>
              </div>
            </fieldset>
          </section>

          <section v-if="esCritico" class="mb-6 rounded-xl bg-white p-5 shadow-sm">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
              LIBERACIÓN DE CONDICIONES OPERACIONALES PARA PRODUCTOS CRÍTICOS PESAJE
            </h2>
            <p class="mb-4 text-sm text-ink-500">
              Grupo de producto:
              <Badge color="amber">{{ orden.grupo_critico_pesaje_display }}</Badge>
            </p>
            <fieldset :disabled="!editable || procesando" class="min-w-0 space-y-4">
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <template v-for="[campo, label] in CAMPOS" :key="campo">
                  <BaseInput
                    v-if="editable"
                    v-model="form[campo]"
                    :label="label"
                    :error="errores[campo]"
                    required
                  />
                  <div v-else class="text-sm">
                    <p class="text-ink-500">{{ label }}</p>
                    <p class="font-medium text-ink-900">{{ form[campo] || '—' }}</p>
                  </div>
                </template>
                <div class="text-sm">
                  <p class="text-ink-500">Referencia actual</p>
                  <p class="font-medium text-ink-900">
                    {{ orden.pesaje?.referencia_actual || orden.referencia }}
                  </p>
                </div>
              </div>
              <p v-if="editable" class="text-sm text-ink-500">
                Complete todos los campos y verificaciones. Si no hubo un lote anterior, indique
                “No aplica” en lote y referencia anterior.
              </p>
              <VerificacionesPesaje
                v-model="form"
                :campos="verificacionesCriticas"
                :errores="errores"
                :editable="editable"
              />
              <label v-if="editable" class="block">
                <span class="mb-1.5 block text-sm font-medium text-ink-900">
                  Acciones correctivas / Observaciones
                  <span v-if="observacionesRequeridas" class="text-danger">*</span>
                  <span v-else>(opcional)</span>
                </span>
                <textarea
                  v-model="form.critico_observaciones"
                  rows="3"
                  class="w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
                  :class="errores.critico_observaciones ? 'border-danger' : 'border-slate-300'"
                />
                <p v-if="errores.critico_observaciones" class="mt-1 text-sm text-danger">
                  {{ errores.critico_observaciones }}
                </p>
              </label>
              <div v-else class="text-sm">
                <p class="text-ink-500">Acciones correctivas / Observaciones</p>
                <p class="whitespace-pre-line text-ink-900">
                  {{ form.critico_observaciones || 'Sin observaciones.' }}
                </p>
              </div>
            </fieldset>
            <!-- Integrar aquí evidencia del registro cuando exista soporte compartido de adjuntos. -->
          </section>

          <p v-if="noCumple" class="mb-4 text-sm font-medium text-danger">
            El registro contiene verificaciones marcadas “No cumple”. Explíquelas en observaciones;
            puede continuar con el pesaje y el supervisor las revisará después.
          </p>

          <!-- Punto de entrada al registro de cantidades pesadas: se implementa en
               una vista aparte (ver PesajeCantidades.vue). Esta misma acción guarda
               la verificación, por eso no hay un botón de guardado aparte. -->
          <section v-if="editable" class="mb-6 rounded-xl bg-white p-5 shadow-sm">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
              Pesaje de materias primas
            </h2>
            <p class="mb-4 text-sm text-ink-500">
              Al continuar se guarda la verificación y se abre el registro de cantidades pesadas
              por materia prima.
            </p>
            <p v-if="mensajeBloqueo" role="alert" class="mb-4 text-sm font-medium text-danger">
              {{ mensajeBloqueo }}
            </p>
            <BaseButton
              type="submit"
              variant="primary"
              class="w-full sm:w-auto"
              :loading="procesando"
            >
              Empezar pesaje
            </BaseButton>
          </section>
        </form>
      </template>

      <!-- Lo que registró el operario en la hoja de proceso: el Supervisor lo
           revisa antes de liberar a Mezcla. -->
      <section v-if="esSupervisor && registroPesaje" class="mb-6 rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Pesaje registrado
        </h2>
        <dl class="mb-4 grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
          <div>
            <dt class="text-ink-500">Operario</dt>
            <dd class="font-medium text-ink-900">{{ registroPesaje.nombre_operario || '—' }}</dd>
          </div>
          <div>
            <dt class="text-ink-500">Inicio del pesaje</dt>
            <dd class="font-medium text-ink-900">
              {{ formatearFechaHora(registroPesaje.fecha_inicio_pesaje) }}
            </dd>
          </div>
          <div>
            <dt class="text-ink-500">Fin del pesaje</dt>
            <dd class="font-medium text-ink-900">
              {{ formatearFechaHora(registroPesaje.fecha_envio_supervision) }}
            </dd>
          </div>
        </dl>
        <div class="overflow-x-auto rounded-lg border border-slate-100">
          <table class="w-full min-w-[520px] text-left text-sm">
            <thead class="bg-surface-alt text-xs font-semibold uppercase text-ink-500">
              <tr>
                <th class="px-4 py-2">Código</th>
                <th class="px-4 py-2">Descripción</th>
                <th class="px-4 py-2">Fórmula</th>
                <th class="px-4 py-2">Peso real</th>
                <th class="px-4 py-2">Diferencia</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-if="!orden.materiales.length">
                <td colspan="5" class="px-4 py-6 text-center text-ink-500">
                  Esta orden no tiene materias primas registradas.
                </td>
              </tr>
              <tr v-for="material in orden.materiales" :key="material.id">
                <td class="px-4 py-2 text-ink-900">{{ material.codigo }}</td>
                <td class="px-4 py-2 text-ink-900">{{ material.descripcion }}</td>
                <td class="px-4 py-2 text-ink-500 tabular-nums">
                  {{ formatearCantidad(material.cantidad) }} {{ unidadVisible }}
                </td>
                <td class="px-4 py-2 font-medium text-ink-900 tabular-nums">
                  {{ pesoRealDe(material) }}
                </td>
                <td class="px-4 py-2 tabular-nums" :class="diferenciaDe(material) ? 'text-danger' : 'text-ink-500'">
                  {{ diferenciaDe(material) || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="revisable" class="rounded-xl bg-white p-5 shadow-sm">
        <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
          Revisión del Supervisor de Pesaje
        </h2>
        <form novalidate class="space-y-4" @submit.prevent="revisar(true)">
          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-ink-900"
              >Motivo de devolución (obligatorio para devolver)</span
            >
            <textarea
              v-model="motivo"
              rows="3"
              :disabled="procesando"
              class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
            />
            <span v-if="errores.motivo" class="mt-1 block text-sm text-danger">{{
              errores.motivo
            }}</span>
          </label>
          <div class="flex flex-col gap-3 sm:flex-row">
            <BaseButton :loading="procesando" @click="revisar(false)">Enviar a Mezcla</BaseButton>
            <BaseButton type="submit" variant="danger" :disabled="procesando"
              >Devolver a Pesaje</BaseButton
            >
          </div>
        </form>
      </section>
    </template>
  </main>
</template>
