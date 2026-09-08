<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'
import { useAuthStore } from '../../store/auth'
import Badge from '../../components/ui/Badge.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import OrdenResumen from '../../components/produccion/OrdenResumen.vue'
import OrdenTrazabilidad from '../../components/produccion/OrdenTrazabilidad.vue'
import { CLASIFICACION_BADGE, ESTADO_BADGE, mapearErroresCampo } from '../../utils/ordenes'
import VerificacionesPesaje from '../../components/produccion/VerificacionesPesaje.vue'
import { VERIFICACIONES_PESAJE, VERIFICACIONES_CRITICAS } from '../../utils/pesaje'

const route = useRoute()
const auth = useAuthStore()
const esSupervisor = computed(() => auth.rol === 'supervisor_pesaje')
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
const verificacionesAplicables = computed(() =>
  esCritico.value ? [...VERIFICACIONES_PESAJE, ...VERIFICACIONES_CRITICAS] : VERIFICACIONES_PESAJE,
)
const noCumple = computed(() =>
  verificacionesAplicables.value.some(([campo]) => form.value[campo] === false),
)
const unidadVisible = computed(() => orden.value?.unidad?.trim() || 'Sin unidad')

// Solo presentación: conserva todos los decimales significativos, sin redondear pesos.
function formatearCantidad(valor) {
  return String(valor ?? '').replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1')
}

function diferenciaVisible(material, peso) {
  if (!esSupervisor.value || !String(peso).trim()) return ''
  const diferencia = Number((Number(peso) - Number(material.cantidad)).toFixed(4))
  if (!Number.isFinite(diferencia) || diferencia === 0) return ''
  return `${diferencia > 0 ? '+' : ''}${formatearCantidad(diferencia.toFixed(4))} ${unidadVisible.value}`
}

const CAMPOS = [
  ['lote_anterior', 'Lote anterior'],
  ['referencia_anterior', 'Referencia anterior'],
  ['lote_actual', 'Lote actual'],
  ['nombre_operario', 'Nombre del operario de Pesaje'],
]

function mostrarOrden(data) {
  orden.value = data
  const registro = data.pesaje || {}
  form.value = {
    ...Object.fromEntries(CAMPOS.map(([campo]) => [campo, registro[campo] || ''])),
    ...Object.fromEntries(
      [...VERIFICACIONES_PESAJE, ...VERIFICACIONES_CRITICAS].map(([campo]) => [
        campo,
        registro[campo] ?? null,
      ]),
    ),
    critico_observaciones: registro.critico_observaciones || '',
    observaciones: registro.observaciones || '',
    pesos: data.materiales.map((material) => ({
      material: material.id,
      peso_real: formatearCantidad(
        registro.pesos?.find((peso) => peso.material === material.id)?.peso_real ?? '',
      ),
    })),
  }
}

async function cargarOrden() {
  cargando.value = true
  errorCarga.value = ''
  orden.value = null
  errores.value = {}
  mensaje.value = ''
  motivo.value = ''
  try {
    const { data } = await api.get(`/produccion/ordenes/${route.params.id}/`)
    mostrarOrden(data)
  } catch {
    errorCarga.value =
      'No se pudo cargar la OP. Puede haber cambiado de etapa; vuelva a la bandeja.'
  } finally {
    cargando.value = false
  }
}

function validarEnvio() {
  const pendientes = {}
  if (!orden.value.grupo_critico_pesaje) {
    pendientes.grupo_critico_pesaje =
      'Solicite clasificar el producto en administración antes de enviarlo.'
  }
  for (const [campo] of CAMPOS) {
    if (!form.value[campo].trim()) pendientes[campo] = 'Este campo es obligatorio.'
  }
  for (const [campo] of verificacionesAplicables.value) {
    if (form.value[campo] === null) pendientes[campo] = 'Seleccione Cumple o No cumple.'
  }
  if (
    !form.value.pesos.length ||
    form.value.pesos.some(
      (peso) =>
        !peso.peso_real.trim() ||
        !Number.isFinite(Number(peso.peso_real)) ||
        Number(peso.peso_real) <= 0,
    )
  )
    pendientes.pesos = 'Registre un peso positivo para cada materia prima.'
  errores.value = pendientes
  return !Object.keys(pendientes).length
}

async function guardar(enviar = false) {
  if (procesando.value || !editable.value) return
  errores.value = {}
  mensaje.value = ''
  if (enviar && !validarEnvio()) return
  procesando.value = true
  try {
    // Los pesos vacíos quedan pendientes en el borrador; el envío los exige todos.
    const payload = {
      ...form.value,
      pesos: form.value.pesos.filter((peso) => peso.peso_real.trim()),
    }
    if (!esCritico.value) {
      for (const [campo] of VERIFICACIONES_CRITICAS) delete payload[campo]
      delete payload.critico_observaciones
    }
    const accion = enviar ? 'enviar-supervisor/' : ''
    const { data } = await api.patch(
      `/produccion/ordenes/${route.params.id}/pesaje/${accion}`,
      payload,
    )
    mostrarOrden(data)
    mensaje.value = enviar
      ? 'OP enviada a Supervisor de Pesaje.'
      : 'Borrador guardado correctamente.'
  } catch (e) {
    errores.value = mapearErroresCampo(e)
    if (e.response?.data?.pesos) {
      errores.value.pesos =
        typeof e.response.data.pesos === 'string'
          ? e.response.data.pesos
          : 'Revise los pesos: deben ser positivos, con máximo 10 enteros y 4 decimales, sin materiales repetidos.'
    }
    if (!Object.keys(errores.value).length)
      errores.value.detail = 'No se pudo guardar. Intente nuevamente.'
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
      <OrdenResumen :orden="orden" />
      <OrdenTrazabilidad :orden="orden" />
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

      <form novalidate @submit.prevent="guardar(true)">
        <p v-if="!orden.grupo_critico_pesaje" class="mb-4 text-sm font-medium text-danger">
          Producto sin clasificar. Solicite clasificar el código {{ orden.codigo_producto }} en
          administración antes de enviarlo a supervisor. Puede guardar el borrador.
        </p>
        <p v-if="errores.grupo_critico_pesaje" role="alert" class="mb-4 text-sm text-danger">
          {{ errores.grupo_critico_pesaje }}
        </p>
        <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
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
              Complete todos los campos y verificaciones. Si no hubo un lote anterior, indique “No
              aplica” en lote y referencia anterior.
            </p>
            <VerificacionesPesaje
              v-model="form"
              :campos="VERIFICACIONES_PESAJE"
              :errores="errores"
              :editable="editable"
            />
            <label v-if="editable" class="block">
              <span class="mb-1.5 block text-sm font-medium text-ink-900"
                >Observaciones de Pesaje (opcional)</span
              >
              <textarea
                v-model="form.observaciones"
                rows="3"
                class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
              />
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
            Grupo de producto: <Badge color="amber">{{ orden.grupo_critico_pesaje_display }}</Badge>
          </p>
          <fieldset :disabled="!editable || procesando" class="min-w-0 space-y-4">
            <VerificacionesPesaje
              v-model="form"
              :campos="VERIFICACIONES_CRITICAS"
              :errores="errores"
              :editable="editable"
            />
            <label v-if="editable" class="block">
              <span class="mb-1.5 block text-sm font-medium text-ink-900"
                >Acciones correctivas / Observaciones (opcional)</span
              >
              <textarea
                v-model="form.critico_observaciones"
                rows="3"
                class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
              />
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

        <section class="mb-6 rounded-xl bg-white p-5 shadow-sm">
          <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-500">
            Cantidades pesadas por materia prima
          </h2>
          <p class="mb-4 text-sm text-ink-500">
            Registre el peso real en la misma unidad de la cantidad de fórmula. La cantidad original
            se conserva.
          </p>
          <fieldset :disabled="!editable || procesando" class="min-w-0">
            <div class="overflow-x-auto rounded-lg border border-slate-100">
              <table class="w-full min-w-[560px] text-left text-sm">
                <thead class="bg-surface-alt text-xs font-semibold uppercase text-ink-500">
                  <tr>
                    <th class="px-4 py-2">Código</th>
                    <th class="px-4 py-2">Descripción</th>
                    <th class="px-4 py-2">Cantidad esperada</th>
                    <th class="px-4 py-2">Peso real</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-if="!orden.materiales.length">
                    <td colspan="4" class="px-4 py-6 text-center text-ink-500">
                      Esta orden no tiene materiales registrados.
                    </td>
                  </tr>
                  <tr v-for="(material, index) in orden.materiales" :key="material.id">
                    <td class="px-4 py-2 text-ink-900">{{ material.codigo }}</td>
                    <td class="px-4 py-2 text-ink-900">{{ material.descripcion }}</td>
                    <td class="px-4 py-2 text-ink-500 tabular-nums">
                      {{ formatearCantidad(material.cantidad) }}
                      <span class="whitespace-nowrap">{{ unidadVisible }}</span>
                    </td>
                    <td class="px-4 py-2">
                      <div v-if="editable" class="flex min-w-[180px] items-end gap-2">
                        <BaseInput
                          v-model="form.pesos[index].peso_real"
                          class="min-w-0 flex-1"
                          :label="`Peso real · ${material.codigo}`"
                          type="number"
                          min="0.0001"
                          step="0.0001"
                          required
                        />
                        <span class="shrink-0 pb-2.5 text-sm text-ink-500">{{
                          unidadVisible
                        }}</span>
                      </div>
                      <template v-else>
                        <span class="font-medium text-ink-900 tabular-nums">
                          {{
                            form.pesos[index].peso_real
                              ? formatearCantidad(form.pesos[index].peso_real)
                              : 'Pendiente'
                          }}
                          <span class="whitespace-nowrap">{{ unidadVisible }}</span>
                        </span>
                        <p
                          v-if="diferenciaVisible(material, form.pesos[index].peso_real)"
                          class="mt-0.5 text-xs text-ink-500 tabular-nums"
                          title="Diferencia frente a la cantidad esperada; solo informativa."
                        >
                          Diferencia: {{ diferenciaVisible(material, form.pesos[index].peso_real) }}
                        </p>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </fieldset>
          <p v-if="errores.pesos" class="mt-2 text-sm text-danger">{{ errores.pesos }}</p>
        </section>
        <p v-if="noCumple" class="mb-4 text-sm font-medium text-danger">
          El registro contiene verificaciones marcadas “No cumple”. El supervisor debe revisarlas
          antes de aprobar.
        </p>
        <div v-if="Object.keys(errores).length" role="alert" class="mb-4 text-sm text-danger">
          {{
            errores.detail ||
            errores.non_field_errors ||
            'Revise los campos indicados antes de continuar.'
          }}
        </div>
        <div v-if="editable" class="mb-6 flex flex-col gap-3 sm:flex-row">
          <BaseButton variant="secondary" :disabled="procesando" @click="guardar(false)"
            >Guardar borrador</BaseButton
          >
          <BaseButton type="submit" :loading="procesando">Enviar a supervisor</BaseButton>
        </div>
      </form>

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
            <BaseButton :loading="procesando" @click="revisar(false)"
              >Aprobar y enviar a Mezcla</BaseButton
            >
            <BaseButton type="submit" variant="danger" :disabled="procesando"
              >Devolver a Pesaje</BaseButton
            >
          </div>
        </form>
      </section>
    </template>
  </main>
</template>
